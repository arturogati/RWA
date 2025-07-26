"""
Ответственность:
Управление бизнесами, токенами, пользователями и дивидендами.
Поддерживает выпуск, списание, балансы и выплаты.
"""

import sqlite3

class DBManager:
    def __init__(self, db_path="database.sqlite"):
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
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL
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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS dividend_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_inn TEXT NOT NULL,
                    distribution_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_revenue REAL NOT NULL,
                    dividend_pool REAL NOT NULL,
                    token_price REAL NOT NULL,
                    FOREIGN KEY (business_inn) REFERENCES businesses(inn)
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
        """
        Выпускает или списывает токены для бизнеса.
        Если записи нет — создаёт новую.
        """
        if amount == 0:
            return

        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT amount FROM token_issuances WHERE business_inn = ?", (inn,))
            row = cursor.fetchone()

            if row is None:
                if amount < 0:
                    raise ValueError(f"Нельзя списать токены у новой компании.")
                cursor.execute("""
                    INSERT INTO token_issuances (business_inn, amount, issued_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (inn, amount))
                print(f"[INFO] Создана новая запись для ИНН {inn} с {amount} токенами.")
            else:
                current_amount = row[0]
                new_amount = current_amount + amount
                if new_amount < 0:
                    raise ValueError(f"Недостаточно токенов для списания. Осталось: {current_amount}")
                cursor.execute("""
                    UPDATE token_issuances 
                    SET amount = ?, issued_at = CURRENT_TIMESTAMP 
                    WHERE business_inn = ?
                """, (new_amount, inn))
                print(f"[INFO] Токены для ИНН {inn} обновлены до {new_amount}.")

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
        """Увеличивает количество токенов у пользователя."""
        if amount == 0:
            return
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT tokens FROM user_tokens
                WHERE email = ? AND business_inn = ?
            """, (email, business_inn))
            row = cursor.fetchone()
            if row:
                new_tokens = row[0] + amount
                cursor.execute("""
                    UPDATE user_tokens 
                    SET tokens = ? 
                    WHERE email = ? AND business_inn = ?
                """, (new_tokens, email, business_inn))
                print(f"[INFO] Обновлено количество токенов для {email}")
            else:
                cursor.execute("""
                    INSERT INTO user_tokens (email, business_inn, tokens) VALUES (?, ?, ?)
                """, (email, business_inn, amount))
                print(f"[INFO] Выдано {amount} токенов для {email}")

    def get_user_tokens(self, email: str):
        """Возвращает список всех токенов пользователя по компаниям."""
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT ut.business_inn, b.name, ut.tokens
                FROM user_tokens ut
                JOIN businesses b ON ut.business_inn = b.inn
                WHERE ut.email = ?
            """, (email,))
            return cursor.fetchall()

    def distribute_dividends(self, inn: str, revenue: float, dividend_percentage: float = 0.1):
        """
        Распределяет дивиденды между держателями токенов.
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT amount FROM token_issuances WHERE business_inn = ?", (inn,))
            row = cursor.fetchone()
            if not row or row[0] <= 0:
                raise ValueError(f"Компания с ИНН {inn} не выпустила токены.")
            total_tokens = row[0]
            dividend_pool = revenue * dividend_percentage
            token_price = dividend_pool / total_tokens

            cursor.execute("""
                SELECT email, tokens FROM user_tokens
                WHERE business_inn = ?
            """, (inn,))
            holders = cursor.fetchall()

            for email, token_count in holders:
                if token_count > 0:
                    dividend = (token_count / total_tokens) * dividend_pool
                    print(f"[DIVIDEND] {email} получает ${dividend:.2f} за {token_count} токенов")

            cursor.execute("""
                INSERT INTO dividend_history (business_inn, total_revenue, dividend_pool, token_price)
                VALUES (?, ?, ?, ?)
            """, (inn, revenue, dividend_pool, token_price))
            print(f"[INFO] Дивиденды распределены для ИНН {inn}: ${dividend_pool:.2f}")