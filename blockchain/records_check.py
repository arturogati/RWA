"""
Ответственность:
Тестовый скрипт для проверки содержимого базы данных.
"""

import sqlite3
import os

def get_db_connection(db_path="database.sqlite"):
    """
    Создает подключение к базе данных SQLite.
    Проверяет, существует ли файл БД.
    """
    print(f"[DEBUG] Подключаемся к базе данных: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Файл базы данных не найден: {db_path}")
        choice = input("Хотите создать новую БД? (y/n): ").strip().lower()
        if choice == "y":
            open(db_path, 'w').close()  # Создаем пустой файл
            print(f"[INFO] Новая БД создана по пути: {db_path}")
        else:
            exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Доступ по имени колонок
    return conn

def list_tables(conn):
    """Возвращает список таблиц в базе данных."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]
    return tables

def print_table_contents(conn, table_name):
    """Выводит содержимое указанной таблицы."""
    print(f"\n--- Таблица: {table_name} ---")

    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        print("Колонки:", ", ".join(columns))

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print("Таблица пуста.")
            return

        for row in rows:
            print(dict(row))  # Выводим как словарь для удобства

    except sqlite3.OperationalError as e:
        print(f"[Ошибка] Не удалось прочитать таблицу '{table_name}': {e}")

def main():
    print("=== Проверка содержимого БД ===\n")
    
    db_path = "database.sqlite"
    
    conn = get_db_connection(db_path)
    
    tables = list_tables(conn)
    
    if not tables:
        print("База данных пуста, таблиц нет.")
        return
    
    print("Найденные таблицы:", tables)
    
    for table in tables:
        print_table_contents(conn, table)

if __name__ == "__main__":
    main()