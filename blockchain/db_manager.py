"""
Responsibilities:
Management of businesses, tokens, and user balances.
Supports updating existing records.
"""

import sqlite3

class DBManager:
    def __init__(self, db_path="database.sqlite"):
        self.conn = sqlite3.connect(db_path)
        print(f"[DEBUG] Database connected: {db_path}")
        self._initialize_tables()

    def _initialize_tables(self):
        """Create tables on first run."""
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
            print("[DEBUG] Tables verified/created.")

    def register_or_update_business(self, inn: str, name: str):
        """Registers or updates company data."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT inn FROM businesses WHERE inn = ?", (inn,))
            if cursor.fetchone():
                cursor.execute("UPDATE businesses SET name = ? WHERE inn = ?", (name, inn))
                print(f"[INFO] Updated company with TIN {inn}")
            else:
                cursor.execute("INSERT INTO businesses (inn, name) VALUES (?, ?)", (inn, name))
                print(f"[INFO] Added new company with TIN {inn}")

    def issue_tokens(self, inn: str, amount: float):
        """
        Updates token amount for a business.
        Positive value - increases.
        Negative value - decreases.
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT business_inn, amount FROM token_issuances WHERE business_inn = ?", (inn,))
            row = cursor.fetchone()

            if not row:
                raise ValueError(f"Company with TIN {inn} not found")

            current_amount = row[1]
            new_amount = current_amount + amount

            if new_amount < 0:
                raise ValueError(f"Insufficient tokens for withdrawal. Remaining: {current_amount}")

            cursor.execute("""
                UPDATE token_issuances 
                SET amount = ?, issued_at = CURRENT_TIMESTAMP 
                WHERE business_inn = ?
            """, (new_amount, inn))

            print(f"[INFO] Tokens for TIN {inn} updated to {new_amount}.")

    def get_token_stats(self, inn: str):
        """Returns token information by TIN."""
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
                return {"error": "Company not found or no tokens issued."}

            amount, issued_at, name = result
            return {
                "inn": inn,
                "name": name,
                "total_issued": amount,
                "issued_at": issued_at
            }

    def get_all_issuances(self):
        """Returns all token issuance records."""
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
        Increases user's token amount.
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
                print(f"[INFO] Updated token amount for {email} - business {business_inn}")
            else:
                cursor.execute("""
                    INSERT INTO user_tokens (email, business_inn, tokens) VALUES (?, ?, ?)
                """, (email, business_inn, amount))
                print(f"[INFO] Issued {amount} tokens to {email} - business {business_inn}")

    def get_user_tokens(self, email: str):
        """
        Returns all user tokens by company.
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