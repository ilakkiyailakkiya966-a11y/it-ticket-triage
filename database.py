import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    """Opens a new connection to the PostgreSQL database."""
    return psycopg.connect(DATABASE_URL)


def init_db():
    """Creates the tables if they don't already exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'employee'
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            category TEXT,
            urgency TEXT,
            reasoning TEXT,
            status TEXT DEFAULT 'Open',
            submitted_by INTEGER REFERENCES users (id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()


def add_ticket(title, description, submitted_by, category=None, urgency=None, reasoning=None):
    """Saves one new ticket into the database, linked to the user who submitted it."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tickets (title, description, category, urgency, reasoning, submitted_by) VALUES (%s, %s, %s, %s, %s, %s)",
        (title, description, category, urgency, reasoning, submitted_by)
    )
    conn.commit()
    cursor.close()
    conn.close()


def get_all_tickets(user_id=None, search=None, category=None, status=None):
    """
    Fetches tickets, most urgent first, then newest first.
    If user_id is given, only returns tickets submitted by that user (for employees).
    If user_id is None, returns ALL tickets (for IT staff).
    Optional filters: search (matches title/description), category, status.
    """
    conn = get_connection()
    cursor = conn.cursor(row_factory=dict_row)

    base_query = """
        SELECT *,
        CASE urgency
            WHEN 'High' THEN 1
            WHEN 'Medium' THEN 2
            WHEN 'Low' THEN 3
            ELSE 4
        END AS urgency_rank
        FROM tickets
    """

    conditions = []
    params = []

    if user_id is not None:
        conditions.append("submitted_by = %s")
        params.append(user_id)

    if search:
        conditions.append("(title ILIKE %s OR description ILIKE %s)")
        like_pattern = f"%{search}%"
        params.append(like_pattern)
        params.append(like_pattern)

    if category:
        conditions.append("category = %s")
        params.append(category)

    if status:
        conditions.append("status = %s")
        params.append(status)

    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)

    base_query += " ORDER BY urgency_rank ASC, created_at DESC"

    cursor.execute(base_query, params)
    tickets = cursor.fetchall()
    cursor.close()
    conn.close()
    return tickets


def update_ticket_status(ticket_id, new_status):
    """Lets IT staff change a ticket's status (Open, In Progress, Resolved)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tickets SET status = %s WHERE id = %s", (new_status, ticket_id))
    conn.commit()
    cursor.close()
    conn.close()


def create_user(username, password_hash, role="employee"):
    """Creates a new user account. Returns True if successful, False if username taken."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, password_hash, role)
        )
        conn.commit()
        return True
    except psycopg.errors.UniqueViolation:
        # This happens if the username already exists (UNIQUE constraint)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def get_user_by_username(username):
    """Looks up a user by their username. Returns None if not found."""
    conn = get_connection()
    cursor = conn.cursor(row_factory=dict_row)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_stats(user_id=None):
    """Returns simple counts for the dashboard stats bar. Filtered by user if given."""
    conn = get_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open' AND submitted_by = %s", (user_id,))
        open_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE urgency = 'High' AND submitted_by = %s", (user_id,))
        high_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE submitted_by = %s", (user_id,))
        total_count = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE status = 'Open'")
        open_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets WHERE urgency = 'High'")
        high_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tickets")
        total_count = cursor.fetchone()[0]

    cursor.close()
    conn.close()
    return {"open": open_count, "high": high_count, "total": total_count}
