"""
Ответственность:
Регистрация, аутентификация и работа с пользователями.
"""

import sqlite3

class UserAlreadyExists(Exception):
    pass

class InvalidEmail(Exception):
    pass

class UserManager:
    def __init__(self, db_path="blockchain/database.sqlite"):
        self.conn = sqlite3.connect(db_path)
        self._initialize_tables()

    def _initialize_tables(self):
        """Создание таблиц при первом запуске."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            print("[DEBUG] Таблица 'users' проверена/создана.")

    def register_user(self, name: str, email: str, password: str):
        """Регистрирует нового пользователя."""
        if "@" not in email:
            raise InvalidEmail("Некорректный формат email")

        with self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, password)
                )
                print(f"[INFO] Зарегистрирован пользователь: {email}")
            except sqlite3.IntegrityError:
                raise UserAlreadyExists(f"Пользователь с email '{email}' уже существует.")
            except Exception as e:
                raise Exception(f"Ошибка при регистрации: {e}")

    def authenticate_user(self, email: str, password: str):
        """Проверяет логин и пароль."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0] == password
        return False

    def find_user_by_email(self, email: str):
        """Ищет пользователя по email."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, email FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return {"name": result[0], "email": result[1]}
        return None