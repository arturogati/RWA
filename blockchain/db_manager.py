"""
Ответственность:
Управление бизнесами, токенами и балансами пользователей.
Поддерживает обновление существующих записей.
"""

import sqlite3

class DBManager:
    def __init__(self, db_path="blockchain/database.sqlite"):
        self.conn = sqlite3.connect(db_path)
        print(f"[DEBUG] Подключена база данных: {db_path}")
        self._initialize_tables()

    def _initialize_tables(self):
        """Создание таблиц при первом запуске."""
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
            print("[DEBUG] Таблицы проверены/созданы.")

    def register_or_update_business(self, inn: str, name: str):
        """Регистрирует или обновляет данные о компании."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT inn FROM businesses WHERE inn = ?", (inn,))
            if cursor.fetchone():
                cursor.execute("UPDATE businesses SET name = ? WHERE inn = ?", (name, inn))
                print(f"[INFO] Обновлена компания с ИНН {inn}")
            else:
                cursor.execute("INSERT INTO businesses (inn, name) VALUES (?, ?)", (inn, name))
                print(f"[INFO] Добавлена новая компания с ИНН {inn}")

    def issue_tokens(self, inn: str, amount: float):
        """Выпускает токены для бизнеса по ИНН (перезаписывает предыдущее значение)."""
        if amount <= 0:
            raise ValueError("Количество токенов должно быть положительным.")

        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT business_inn FROM token_issuances WHERE business_inn = ?", (inn,))
            if cursor.fetchone():
                cursor.execute("""
                    UPDATE token_issuances 
                    SET amount = ?, issued_at = CURRENT_TIMESTAMP 
                    WHERE business_inn = ?
                """, (amount, inn))
                print(f"[INFO] Токены для ИНН {inn} обновлены до {amount}.")
            else:
                cursor.execute("INSERT INTO token_issuances (business_inn, amount) VALUES (?, ?)", (inn, amount))
                print(f"[INFO] Выпущено {amount} токенов для ИНН {inn}.")

    def get_token_stats(self, inn: str):
        """Возвращает информацию о токенах по ИНН."""
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
                return {"error": "Компания не найдена или токены не выпущены."}

            amount, issued_at, name = result
            return {
                "inn": inn,
                "name": name,
                "total_issued": amount,
                "issued_at": issued_at
            }

    def get_all_issuances(self):
        """Возвращает все записи о выпуске токенов."""
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
        Увеличивает количество токенов у пользователя.
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
                print(f"[INFO] Обновлено количество токенов для {email} — бизнес {business_inn}")
            else:
                cursor.execute("""
                    INSERT INTO user_tokens (email, business_inn, tokens) VALUES (?, ?, ?)
                """, (email, business_inn, amount))
                print(f"[INFO] Выдано {amount} токенов для {email} — бизнес {business_inn}")

    def get_user_tokens(self, email: str):
        """
        Возвращает список всех токенов пользователя по компаниям.
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