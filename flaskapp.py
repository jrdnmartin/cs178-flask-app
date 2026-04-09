# author: Jordan Martin
# description: Flask example using redirect, url_for, and flash

from flask import Flask, render_template, request, redirect, url_for, flash, session
from dbCode import (
    execute_query,
    get_random_country,
    get_official_languages,
    ensure_app_users_table,
    get_app_users,
    get_app_user,
    create_app_user,
    update_app_user,
    delete_app_user,
)
from dynamoCode import save_score, get_high_scores_by_category
from uuid import uuid4

app = Flask(__name__)
app.secret_key = 'your_secret_key' # this is an artifact for using flash displays; 
                                   # it is required, but you can leave this alone

try:
    ensure_app_users_table()
except Exception as db_init_error:
    print(f"[WARN] Database initialization skipped: {db_init_error}")

GAME_CATEGORIES = [
    {'id': 'population', 'name': 'Population', 'description': 'Guess if country B has higher or lower population'},
    {'id': 'gnp', 'name': 'GNP', 'description': 'Guess if country B has higher or lower GNP'},
    {'id': 'life_expectancy', 'name': 'Life Expectancy', 'description': 'Guess if country B has higher or lower life expectancy'},
    {'id': 'surface_area', 'name': 'Surface Area', 'description': 'Guess if country B has higher or lower surface area'},
    {'id': 'indep_year', 'name': 'Independence Year', 'description': 'Guess if country B became independent earlier or later'},
]


def get_category_name(category_id):
    for category in GAME_CATEGORIES:
        if category['id'] == category_id:
            return category['name']
    return category_id.replace('_', ' ').title()

# Custom Jinja2 filter for number formatting with commas
@app.template_filter('format_number')
def format_number(value):
    """Format a number with thousand separators."""
    if value is None:
        return 'N/A'
    try:
        return f"{int(float(value)):,}"
    except (ValueError, TypeError):
        return str(value)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/create-user', methods=['GET', 'POST'])
def create_user():
    if request.method == 'POST':
        display_name = request.form.get('display_name', '').strip()
        
        if not display_name:
            flash('Display name is required.', 'danger')
            return redirect(url_for('create_user'))

        try:
            create_app_user(display_name)
            flash(f'User {display_name} created successfully!', 'success')
        except Exception as e:
            flash(f'Could not create user: {e}', 'danger')
            return redirect(url_for('create_user'))

        return redirect(url_for('list_users'))
    else:
        return render_template('create_user.html')

@app.route('/users')
def list_users():
    users = get_app_users()
    return render_template('list_users.html', users=users)

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_user(user_id):
    user = get_app_user(user_id)
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('list_users'))
    
    if request.method == 'POST':
        new_name = request.form.get('display_name', '').strip()
        
        if not new_name:
            flash('Display name is required.', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))

        try:
            update_app_user(user_id, new_name)
            flash('User updated successfully!', 'success')
        except Exception as e:
            flash(f'Could not update user: {e}', 'danger')
            return redirect(url_for('edit_user', user_id=user_id))

        return redirect(url_for('list_users'))
    else:
        return render_template('edit_user.html', user=user)

@app.route('/users/<int:user_id>/delete', methods=['GET', 'POST'])
def delete_user(user_id):
    user = get_app_user(user_id)
    
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('list_users'))
    
    if request.method == 'POST':
        try:
            delete_app_user(user_id)
            flash(f'User {user["display_name"]} deleted successfully!', 'warning')
        except Exception as e:
            flash(f'Could not delete user: {e}', 'danger')
            return redirect(url_for('delete_user', user_id=user_id))

        return redirect(url_for('list_users'))
    else:
        return render_template('delete_user.html', user=user)


# ==================== GAME ROUTES ====================

@app.route('/game-categories')
def game_categories():
    """Show available game categories."""
    return render_template('game_categories.html', categories=GAME_CATEGORIES, users=get_app_users())


@app.route('/game/start/<category>')
def start_game(category):
    """Start a new game with the selected category."""
    valid_categories = [category_def['id'] for category_def in GAME_CATEGORIES]
    
    if category not in valid_categories:
        flash('Invalid category selected.', 'danger')
        return redirect(url_for('game_categories'))
    
    try:
        user_id = request.args.get('user_id', '').strip() or request.form.get('user_id', '').strip()
        if not user_id:
            flash('Pick a saved account before starting the game.', 'danger')
            return redirect(url_for('game_categories'))

        user = get_app_user(int(user_id))
        if not user:
            flash('Selected account no longer exists.', 'danger')
            return redirect(url_for('game_categories'))

        player_name = user['display_name']
        # Get first random country
        country_a = get_random_country(category)
        if not country_a:
            flash(f'No countries found with {category} data.', 'danger')
            return redirect(url_for('game_categories'))
        
        # Initialize game state in session
        session['game'] = {
            'session_id': str(uuid4()),
            'user_id': user['user_id'],
            'category': category,
            'player_name': player_name,
            'country_a': country_a['Name'],
            'stat_a': country_a['stat_value'],
            'score': 0,
            'streak': 0
        }
        session.modified = True
        
        return redirect(url_for('game_round'))
    except Exception as e:
        flash(f'Error starting game: {e}', 'danger')
        return redirect(url_for('game_categories'))


@app.route('/game/round')
def game_round():
    """Display current game round."""
    if 'game' not in session:
        flash('No active game. Start a new one.', 'warning')
        return redirect(url_for('game_categories'))
    
    game = session['game']
    
    try:
        # Get the second random country for this round
        country_b = get_random_country(game['category'])
        if not country_b:
            flash(f'No countries found with {game["category"]} data.', 'danger')
            return redirect(url_for('game_categories'))
        
        # Store country_b for guess processing
        session['game']['country_b'] = country_b['Name']
        session['game']['stat_b'] = country_b['stat_value']
        session.modified = True
        
        # Format category name for display
        category_display = game['category'].replace('_', ' ').title()
        
        return render_template('game_round.html', 
                             country_a=game['country_a'],
                             country_b=country_b['Name'],
                             stat_a=game['stat_a'],
                             category=category_display,
                             player_name=game.get('player_name', 'Guest'),
                             score=game['score'],
                             streak=game['streak'])
    except Exception as e:
        flash(f'Error loading round: {e}', 'danger')
        return redirect(url_for('game_categories'))


@app.route('/game/guess', methods=['POST'])
def game_guess():
    """Process user's higher/lower guess."""
    if 'game' not in session:
        flash('No active game.', 'warning')
        return redirect(url_for('game_categories'))
    
    guess = request.form.get('guess')  # 'higher' or 'lower'
    game = session['game']
    
    if not guess or guess not in ['higher', 'lower']:
        flash('Invalid guess.', 'danger')
        return redirect(url_for('game_round'))
    
    try:
        stat_a = game['stat_a']
        stat_b = game['stat_b']
        next_country = game['country_b']
        
        # Determine if guess was correct
        is_higher = stat_b > stat_a
        was_correct = (guess == 'higher' and is_higher) or (guess == 'lower' and not is_higher)
        
        # Render result page with country details and outcome
        result = {
            'country_a': game['country_a'],
            'country_b': next_country,
            'stat_a': stat_a,
            'stat_b': stat_b,
            'category': get_category_name(game['category']),
            'guess': guess,
            'correct': was_correct,
            'old_score': game['score']
        }
        
        if was_correct:
            # Update score and streak
            game['score'] += 1
            game['streak'] += 1
            # Move country_b to be the next country_a
            game['country_a'] = next_country
            game['stat_a'] = game['stat_b']
            game['country_b'] = None
            game['stat_b'] = None
            session.modified = True
            result['new_score'] = game['score']
            result['message'] = f"Correct! {next_country} has {'higher' if is_higher else 'lower'} {game['category'].lower()}."
        else:
            session.pop('game', None)
            session.modified = True
            try:
                save_score(
                    user_id=game['user_id'],
                    player_name=game.get('player_name', 'Guest'),
                    category=game['category'],
                    score=game['score'],
                    session_id=game['session_id']
                )
            except Exception as save_error:
                flash(f'Game over saved locally, but leaderboard write failed: {save_error}', 'warning')
            result['message'] = f"Wrong! {next_country} has {'higher' if is_higher else 'lower'} {game['category']}. Game over!"
            result['final_score'] = game['score']
            result['game_over'] = True
        
        return render_template('game_result.html', result=result)
    except Exception as e:
        flash(f'Error processing guess: {e}', 'danger')
        return redirect(url_for('game_round'))


@app.route('/game/end')
def end_game():
    """End the current game and show summary."""
    if 'game' in session:
        game = session['game']
        final_score = game['score']
        session.pop('game', None)
        session.modified = True
        try:
            save_score(
                user_id=game['user_id'],
                player_name=game.get('player_name', 'Guest'),
                category=game['category'],
                score=final_score,
                session_id=game['session_id']
            )
        except Exception as save_error:
            flash(f'Game ended, but leaderboard write failed: {save_error}', 'warning')
        flash(f'Game ended. Final score: {final_score}', 'info')
    return redirect(url_for('game_categories'))


@app.route('/leaderboard')
def leaderboard():
    """Display the leaderboard grouped by category using DynamoDB high scores."""
    try:
        grouped_scores = get_high_scores_by_category(limit_per_category=25)
        category_names = {category['id']: category['name'] for category in GAME_CATEGORIES}
        return render_template(
            'leaderboard.html',
            grouped_scores=grouped_scores,
            category_order=[category['id'] for category in GAME_CATEGORIES],
            category_names=category_names,
        )
    except Exception as e:
        flash(f'Error loading leaderboard: {e}', 'danger')
        return redirect(url_for('home'))


@app.route('/country-languages')
def country_languages():
    """Display a live SQL JOIN between country and countrylanguage."""
    try:
        languages = get_official_languages(limit=50)
        return render_template('country_languages.html', languages=languages)
    except Exception as e:
        flash(f'Error loading country languages: {e}', 'danger')
        return redirect(url_for('home'))


@app.route('/display-users')
def display_users():
    try:
        query = """
            SELECT Name, Population, GNP
            FROM country
            ORDER BY Name
            LIMIT 25
        """
        countries = execute_query(query)
        return render_template('display_users.html', users=countries)
    except Exception as e:
        flash(f"Database error: {e}", 'danger')
        return redirect(url_for('home'))


# these two lines of code should always be the last in the file
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
