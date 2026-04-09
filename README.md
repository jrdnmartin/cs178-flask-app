# Higher or Lower: Country Edition

**CS178: Cloud and Database Systems — Project #1**
**Author:** Jordan Martin
**GitHub:** jrdnmartin

---

## Overview

**Higher or Lower: Country Edition** is an interactive web-based game where players compare statistics between random countries and guess whether a country has a higher or lower value for a selected metric (population, GNP, life expectancy, surface area, or independence year). The app demonstrates cloud-native development by combining a Flask web tier on EC2 with both relational (MySQL) and non-relational (DynamoDB) databases, providing hands-on experience with multi-database architectures and AWS service integration. Players can create accounts, compete in multiple game categories, and see their scores on a live leaderboard.

---

## Technologies Used

- **Flask** — Python web framework
- **AWS EC2** — hosts the running Flask application
- **AWS RDS (MySQL)** — relational database for the `world` country dataset used by the game
- **AWS DynamoDB** — non-relational database for leaderboard score records and completed games
- **GitHub Actions** — auto-deploys code from GitHub to EC2 on push

---

## Project Structure

```
ProjectOne/
├── flaskapp.py          # Main Flask application — routes and app logic
├── dbCode.py            # MySQL helper functions for the world database
├── dynamoCode.py        # DynamoDB helper functions for leaderboard scores
├── creds_sample.py      # Sample credentials file (see Credential Setup below)
├── templates/
│   ├── home.html        # Landing page
│   ├── country_languges.html # Page for the country language table
│   ├── create_user.html # Page to create user
│   ├── delete_user.html # Page to delete users
│   ├── display_users.html # Page to display all countries
│   ├── edit_user.html # Page to edit a user's name
│   ├── game_categories.html # The main page to select a game category
│   ├── game_result.html # The page that shows at the end of a game
│   ├── game_round.html # The page that shows the content for the round of a game
│   ├── leaderboard.html # The page displaying the leaderboard results
│   ├── list_users.html # The page to display the users
├── .gitignore           # Excludes creds.py and other sensitive files
└── README.md
```

---

## How to Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/jrdnmartin/cs178-flask-app.git
   cd your-repo-name
   ```

2. Install dependencies:

   ```bash
   pip3 install flask pymysql boto3
   ```

3. Set up your credentials (see Credential Setup below)

4. Run the app:

   ```bash
   python3 flaskapp.py
   ```

5. Open your browser and go to `http://127.0.0.1:8080`

---

## How to Access in the Cloud

The app is deployed on an AWS EC2 instance. To view the live version:

```
http://ec2-3-81-51-123.compute-1.amazonaws.com:8080/
```

_(Note: the EC2 instance may not be running after project submission.)_

---

## Credential Setup

This project requires a `creds.py` file that is **not included in this repository** for security reasons.

Create a file called `creds.py` in the project root with the following format (see `creds_sample.py` for reference):

```python
# creds.py — do not commit this file
host = "your-rds-endpoint"
user = "admin"
password = "your-password"
db = "your-database-name"
```

---

## Database Design

### SQL (MySQL on RDS)

The project uses the `world` database on MySQL/RDS to power the country comparison gameplay. The Flask app queries the `country` table to fetch random countries and to retrieve stat values such as Population, GNP, and LifeExpectancy. This is the relational part of the project because the data is stored in a fixed table schema and accessed through SQL.

Current SQL usage:

- `country` — stores world-country data such as name, population, and GNP; primary key is `Code`
- The game reads random rows from `country` to compare two countries during play

The JOIN query used in this project combines `users`, `high_scores`, and `categories` to build a leaderboard in the SQL-backed version of the app.

### DynamoDB

The non-relational part of the project uses DynamoDB for leaderboard score records. Each completed game writes a score item into a DynamoDB table, which stores flexible event data without requiring joins or a rigid relational schema.

- **Table name:** `leaderboard_scores`
- **Partition key:** `session_id`
- **Sort key:** `achieved_at`
- **Used for:** storing player name, category, score, and timestamp for completed games

---

## CRUD Operations

| Operation | Route      | Description    |
| --------- | ---------- | -------------- |
| Create    | `/create-user` | Creates a new user for scoring values to the database |
| Read      | `/users` | Print all of the currently stored users |
| Update    | `/users/<int:user_id>/edit` | Edit the username for any given user |
| Delete    | `/users/<int:user_id>/delete` | Remove the user from the database |

---

## Challenges and Insights

**Challenges:**
- **Hybrid Database Design:** Balancing where data belongs required careful decisions—user accounts and game metadata live in MySQL for consistency and joins, while game scores and leaderboard entries use DynamoDB for flexible schema and faster writes.
- **Flask Deployment:** Running Flask in production with `nohup` required binding to `0.0.0.0` and ensuring the EC2 security group allows inbound traffic on port 8080; missing any step broke the public URL.

**Insights:**
- GitHub Actions can automate deployment, but manual troubleshooting of startup logs was essential to catch configuration errors that CI/CD alone would not surface.
- Jinja2 templating and Flask's session management simplified game state tracking without needing a separate cache layer.

---

## AI Assistance

Used Github Copilot for help with styling, formatting, and some Jinja templated code. Additionally for random troubleshooting/bug fixes.
