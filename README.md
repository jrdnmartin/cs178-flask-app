# Higher or Lower: Country Edition

**CS178: Cloud and Database Systems — Project #1**
**Author:** Jordan Martin
**GitHub:** jrdnmartin

---

## Overview

<!-- Describe your project in 2-4 sentences. What does it do? Who is it for? What problem does it solve? -->

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
│   ├── ...
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

<!-- What was the hardest part? What did you learn? Any interesting design decisions? -->

---

## AI Assistance

Used Github Copilot for help with styling, formatting, and some Jinja templated code. Additionally for random troubleshooting/bug fixes.
