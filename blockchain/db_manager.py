"""
Responsabilités :
Gestion des entreprises, des tokens et des soldes utilisateurs.
Prend en charge la mise à jour des enregistrements existants.
"""

import sqlite3

class DBManager:
    def __init__(self, db_path="database.sqlite"):
        self.conn = sqlite3.connect(db_path)
        print(f"[DEBUG] Base de données connectée : {db_path}")
        self._initialize_tables()

    def _initialize_tables(self):
        """Création des tables lors du premier lancement."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS businesses (
                    inn TEXT PRIMARY KEY,
                    name TEXT NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS token_issuances (
                    business_inn TEXT PRIMARY KEY,
                    amount REAL NOT NULL,
                    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (business_inn) REFERENCES businesses(inn)
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL,
                    business_inn TEXT NOT NULL,
                    tokens REAL DEFAULT 0,
                    UNIQUE(email, business_inn),
                    FOREIGN KEY(business_inn) REFERENCES businesses(inn)
                )
            """)
            print("[DEBUG] Tables vérifiées/créées.")

    def register_or_update_business(self, inn: str, name: str):
        """Enregistre ou met à jour les données d'une entreprise."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT inn FROM businesses WHERE inn = ?", (inn,))
            if cursor.fetchone():
                cursor.execute("UPDATE businesses SET name = ? WHERE inn = ?", (name, inn))
                print(f"[INFO] Entreprise avec INN {inn} mise à jour")
            else:
                cursor.execute("INSERT INTO businesses (inn, name) VALUES (?, ?)", (inn, name))
                print(f"[INFO] Nouvelle entreprise ajoutée avec INN {inn}")

    def issue_tokens(self, inn: str, amount: float):
        """
        Met à jour le nombre de tokens pour une entreprise.
        Valeur positive - augmente.
        Valeur négative - diminue.
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT business_inn, amount FROM token_issuances WHERE business_inn = ?", (inn,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Entreprise avec INN {inn} introuvable")

            current_amount = row[1]
            new_amount = current_amount + amount

            if new_amount < 0:
                raise ValueError(f"Tokens insuffisants. Solde restant : {current_amount}")

            cursor.execute("""
                UPDATE token_issuances 
                SET amount = ?, issued_at = CURRENT_TIMESTAMP 
                WHERE business_inn = ?
            """, (new_amount, inn))

            print(f"[INFO] Tokens pour INN {inn} mis à jour à {new_amount}.")

    def get_token_stats(self, inn: str):
        """Retourne les informations sur les tokens par INN."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT t.amount, t.issued_at, b.name
                FROM token_issuances t
                JOIN businesses b ON t.business_inn = b.inn
                WHERE t.business_inn = ?
            """, (inn,))
            result = cursor.fetchone()
            if not result:
                return {"error": "Entreprise introuvable ou aucun token émis."}

            amount, issued_at, name = result
            return {
                "inn": inn,
                "name": name,
                "total_issued": amount,
                "issued_at": issued_at
            }

    def get_all_issuances(self):
        """Retourne tous les enregistrements d'émission de tokens."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT b.inn, b.name, t.amount, t.issued_at
                FROM businesses b
                LEFT JOIN token_issuances t ON b.inn = t.business_inn
            """)
            return cursor.fetchall()

    def add_user_tokens(self, email: str, business_inn: str, amount: float):
        """
        Augmente le nombre de tokens d'un utilisateur.
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT tokens FROM user_tokens
                WHERE email = ? AND business_inn = ?
            """, (email, business_inn))

            row = cursor.fetchone()
            if row:
                current_tokens = row[0]
                new_tokens = current_tokens + amount
                cursor.execute("""
                    UPDATE user_tokens 
                    SET tokens = ? 
                    WHERE email = ? AND business_inn = ?
                """, (new_tokens, email, business_inn))
                print(f"[INFO] Nombre de tokens mis à jour pour {email} - entreprise {business_inn}")
            else:
                cursor.execute("""
                    INSERT INTO user_tokens (email, business_inn, tokens) VALUES (?, ?, ?)
                """, (email, business_inn, amount))
                print(f"[INFO] {amount} tokens attribués à {email} - entreprise {business_inn}")

    def get_user_tokens(self, email: str):
        """
        Retourne la liste de tous les tokens d'un utilisateur par entreprise.
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ut.business_inn, b.name, ut.tokens
                FROM user_tokens ut
                JOIN businesses b ON ut.business_inn = b.inn
                WHERE ut.email = ?
            """, (email,))
            return cursor.fetchall()