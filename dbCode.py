# dbCode.py
# Author: Jordan Martin
# Helper functions for database connection and queries

import pymysql
import creds

def get_conn():
    """Returns a connection to the MySQL RDS instance."""
    try:
        conn = pymysql.connect(
            host=creds.host,
            user=creds.user,
            password=creds.password,
            db=creds.db,
            connect_timeout=5,
            read_timeout=10,
            write_timeout=10,
        )
        return conn
    except pymysql.err.OperationalError as exc:
        raise ConnectionError(
            f"Database connection failed for host '{creds.host}'. "
            "Check RDS accessibility (security group, public access, and networking)."
        ) from exc

def execute_query(query, args=()):
    """Executes a SELECT query and returns all rows as dictionaries."""
    conn = get_conn()
    cur = conn.cursor(pymysql.cursors.DictCursor)
    try:
        cur.execute(query, args)
        rows = cur.fetchall()
        return rows
    finally:
        cur.close()
        conn.close()


def execute_non_query(query, args=()):
    """Execute INSERT/UPDATE/DELETE/DDL queries and commit the result."""
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        conn.commit()
        return cur.lastrowid
    finally:
        cur.close()
        conn.close()


def ensure_app_users_table():
    """Create the persistent app users table if it does not already exist."""
    query = """
        CREATE TABLE IF NOT EXISTS app_users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            display_name VARCHAR(100) NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """
    execute_non_query(query)


def get_app_users():
    return execute_query(
        "SELECT user_id, display_name, created_at, updated_at FROM app_users ORDER BY created_at DESC"
    )


def get_app_user(user_id):
    rows = execute_query(
        "SELECT user_id, display_name, created_at, updated_at FROM app_users WHERE user_id = %s",
        (user_id,),
    )
    return rows[0] if rows else None


def create_app_user(display_name):
    return execute_non_query(
        "INSERT INTO app_users (display_name) VALUES (%s)",
        (display_name,),
    )


def update_app_user(user_id, display_name):
    return execute_non_query(
        "UPDATE app_users SET display_name = %s WHERE user_id = %s",
        (display_name, user_id),
    )


def delete_app_user(user_id):
    return execute_non_query(
        "DELETE FROM app_users WHERE user_id = %s",
        (user_id,),
    )

def get_random_country(category):
    """
    Get a random country with a non-null stat for the given category.
    Categories: 'population', 'gnp', 'life_expectancy'
    Returns: dict with Name and the stat value, or None if fails
    """
    if category.lower() == 'population':
        query = "SELECT Name, Population AS stat_value FROM country WHERE Population IS NOT NULL ORDER BY RAND() LIMIT 1"
    elif category.lower() == 'gnp':
        query = "SELECT Name, GNP AS stat_value FROM country WHERE GNP IS NOT NULL ORDER BY RAND() LIMIT 1"
    elif category.lower() == 'life_expectancy':
        query = "SELECT Name, LifeExpectancy AS stat_value FROM country WHERE LifeExpectancy IS NOT NULL ORDER BY RAND() LIMIT 1"
    elif category.lower() == 'surface_area':
        query = "SELECT Name, SurfaceArea AS stat_value FROM country WHERE SurfaceArea IS NOT NULL ORDER BY RAND() LIMIT 1"
    elif category.lower() == 'indep_year':
        query = "SELECT Name, IndepYear AS stat_value FROM country WHERE IndepYear IS NOT NULL ORDER BY RAND() LIMIT 1"
    else:
        return None
    
    result = execute_query(query)
    return result[0] if result else None

def get_country_stat(country_name, category):
    """
    Get the stat value for a specific country and category.
    Returns the numeric stat value or None if not found.
    """
    if category.lower() == 'population':
        query = "SELECT Population AS stat_value FROM country WHERE Name = %s"
    elif category.lower() == 'gnp':
        query = "SELECT GNP AS stat_value FROM country WHERE Name = %s"
    elif category.lower() == 'life_expectancy':
        query = "SELECT LifeExpectancy AS stat_value FROM country WHERE Name = %s"
    else:
        return None
    
    result = execute_query(query, (country_name,))
    return result[0]['stat_value'] if result else None


def get_official_languages(limit=25):
    """Return countries joined with their official languages from the world database."""
    query = """
        SELECT
            c.Name AS country_name,
            cl.Language AS language,
            cl.Percentage AS percentage,
            cl.IsOfficial AS is_official
        FROM country c
        JOIN countrylanguage cl ON c.Code = cl.CountryCode
        WHERE cl.IsOfficial = 'T'
        ORDER BY cl.Percentage DESC, c.Name ASC
        LIMIT %s
    """
    return execute_query(query, (limit,))
