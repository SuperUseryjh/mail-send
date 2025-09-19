import sqlite3
import hashlib
import os

DATABASE_FILE = 'users.db'

def init_db():
    """Initializes the SQLite database and creates the users and domains tables if they don't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            api_key TEXT UNIQUE
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            domain_name TEXT UNIQUE NOT NULL,
            is_verified BOOLEAN NOT NULL DEFAULT FALSE,
            FOREIGN KEY (user_id) REFERENCES users (id)
        ) 
    ''')
    conn.commit()
    conn.close()

def hash_password(password):
    """Hashes a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    """Creates a new user in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        password_hash = hash_password(password)
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Username already exists
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    """Retrieves a user by their username."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, api_key FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {'id': user[0], 'username': user[1], 'password_hash': user[2], 'api_key': user[3]}
    return None

def verify_password(username, password):
    """Verifies a user's password."""
    user = get_user_by_username(username)
    if user and user['password_hash'] == hash_password(password):
        return True
    return False

def generate_api_key():
    """Generates a random API key."""
    return os.urandom(24).hex()

def update_user_api_key(user_id, api_key):
    """Updates a user's API key."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET api_key = ? WHERE id = ?", (api_key, user_id))
    conn.commit()
    conn.close()

def add_domain(user_id, domain_name):
    """Adds a new domain for a user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO domains (user_id, domain_name) VALUES (?, ?)", (user_id, domain_name))
        conn.commit()
        return cursor.lastrowid # Return the ID of the newly added domain
    except sqlite3.IntegrityError:
        # Domain already exists for this user or globally if domain_name is unique
        return None
    finally:
        conn.close()

def get_domains_by_user(user_id):
    """Retrieves all domains for a given user."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, domain_name, is_verified FROM domains WHERE user_id = ?", (user_id,))
    domains = cursor.fetchall()
    conn.close()
    return [{'id': d[0], 'name': d[1], 'verified': bool(d[2])} for d in domains]

def update_domain_verification_status(domain_id, is_verified):
    """Updates the verification status of a domain."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE domains SET is_verified = ? WHERE id = ?", (is_verified, domain_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized and 'users' and 'domains' tables created.")