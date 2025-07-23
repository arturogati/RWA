"""
Responsabilité :
Gestion de l'enregistrement, de l'authentification et des opérations utilisateurs.
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
        """Initialisation des tables lors du premier lancement."""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
                )
            """)
            print("[DEBUG] Table 'users' vérifiée/créée.")

    def register_user(self, name: str, email: str, password: str):
        """Enregistre un nouvel utilisateur."""
        if "@" not in email:
            raise InvalidEmail("Format d'email invalide")

        with self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, password)
                )
                print(f"[INFO] Utilisateur enregistré : {email}")
            except sqlite3.IntegrityError:
                raise UserAlreadyExists(f"Un utilisateur avec l'email '{email}' existe déjà.")
            except Exception as e:
                raise Exception(f"Erreur lors de l'enregistrement : {e}")

    def authenticate_user(self, email: str, password: str):
        """Vérifie les identifiants de connexion."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return result[0] == password
        return False

    def find_user_by_email(self, email: str):
        """Recherche un utilisateur par son email."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, email FROM users WHERE email = ?", (email,))
        result = cursor.fetchone()
        if result:
            return {"name": result[0], "email": result[1]}
        return None