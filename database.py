import sqlite3
import logging
from contextlib import contextmanager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect('bot.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database with users and mods tables."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                phone TEXT,
                age INTEGER,
                username TEXT,
                verified BOOLEAN DEFAULT 0
            )
        ''')
        # Create mods table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mods (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        logger.info("Database initialized with users and mods tables.")

def save_user(user_id, full_name=None, phone=None, age=None, username=None, verified=False):
    """Save or update user data."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO users (user_id, full_name, phone, age, username, verified)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, full_name, phone, age, username, verified))
            conn.commit()
            logger.info(f"User {user_id} saved successfully.")
    except sqlite3.Error as e:
        logger.error(f"DB save error for user {user_id}: {e}")
        raise

def get_all_users():
    """Retrieve all users."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE verified = 1')
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Get all users error: {e}")
        return []

def get_user(user_id):
    """Retrieve a single user by ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    except sqlite3.Error as e:
        logger.error(f"Get user error for {user_id}: {e}")
        return None

def add_mod(user_id, added_by):
    """Add a moderator."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO mods (user_id, added_by) VALUES (?, ?)', (user_id, added_by))
            conn.commit()
            logger.info(f"Moderator {user_id} added by {added_by}.")
    except sqlite3.Error as e:
        logger.error(f"Add mod error: {e}")
        raise

def get_mods():
    """Retrieve all moderators."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM mods')
            return cursor.fetchall()
    except sqlite3.Error as e:
        logger.error(f"Get mods error: {e}")
        return []

def remove_mod(user_id):
    """Remove a moderator."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM mods WHERE user_id = ?', (user_id,))
            conn.commit()
            logger.info(f"Moderator {user_id} removed.")
    except sqlite3.Error as e:
        logger.error(f"Remove mod error: {e}")
        raise

def get_stats():
    """Retrieve bot statistics."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as total, SUM(verified) as verified FROM users')
            stats = cursor.fetchone()
            return {"total_users": stats['total'], "verified_users": stats['verified']}
    except sqlite3.Error as e:
        logger.error(f"Stats retrieval error: {e}")
        return {"total_users": 0, "verified_users": 0}

def export_users():
    """Export all users and mods to a list of dictionaries."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users')
            users = [dict(row) for row in cursor.fetchall()]
            cursor.execute('SELECT * FROM mods')
            mods = [dict(row) for row in cursor.fetchall()]
            return {"users": users, "mods": mods}
    except sqlite3.Error as e:
        logger.error(f"Export error: {e}")
        return {"users": [], "mods": []}