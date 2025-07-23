"""
Responsibilities:
User registration, authentication and management.
"""

import sqlite3

class UserAlreadyExists(Exception):
    pass

class InvalidEmail(Exception):
    pass

class UserManager:
    def __init__(self, db_path="database.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self._initialize_tables()

    def _initialize_tables(self):
        """Create tables on first run."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            print("[DEBUG] 'users' table verified/created.")

    def register_user(self, name: str, email: str, password: str):
        """Registers a new user."""
        if "@" not in email:
            raise InvalidEmail("Invalid email format")

        with self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, password)
                )
                print(f"[INFO] Registered user: {email}")
            except sqlite3.IntegrityError:
                raise UserAlreadyExists(f"User with email '{email}' already exists")
            except Exception as e:
                raise Exception(f"Registration error: {e}")

    def authenticate_user(self, email: str, password: str):
        """Verifies login credentials."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0] == password
        return False

    def find_user_by_email(self, email: str):
        """Finds user by email."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, email FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return {"name": result[0], "email": result[1]}
        return None