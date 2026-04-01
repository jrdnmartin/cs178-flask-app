# dbCode.py
# Author: Your Name
# Helper functions for database connection and queries

import pymysql
import creds

def get_conn():
    """Returns a connection to the MySQL RDS instance."""
    conn = pymysql.connect(
        host=creds.host,
        user=creds.user,
        password=creds.password,
        db=creds.db,
    )
    return conn

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
