"""
Responsibilities:
Test script for checking database contents.
"""

import sqlite3
import os

def get_db_connection(db_path="database.sqlite"):
    """
    Creates a connection to SQLite database.
    Checks if database file exists.
    """
    print(f"[DEBUG] Connecting to database: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Database file not found: {db_path}")
        choice = input("Create new database? (y/n): ").strip().lower()
        if choice == "y":
            open(db_path, 'w').close()  # Create empty file
            print(f"[INFO] New database created at: {db_path}")
        else:
            exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def list_tables(conn):
    """Returns list of tables in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]
    return tables

def print_table_contents(conn, table_name):
    """Prints contents of specified table."""
    print(f"\n--- Table: {table_name} ---")

    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        print("Columns:", ", ".join(columns))

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print("Table is empty.")
            return

        for row in rows:
            print(dict(row))  # Print as dictionary for readability

    except sqlite3.OperationalError as e:
        print(f"[Error] Failed to read table '{table_name}': {e}")

def main():
    print("=== Database Contents Check ===\n")
    
    db_path = "database.sqlite"
    
    conn = get_db_connection(db_path)
    
    tables = list_tables(conn)
    
    if not tables:
        print("Database is empty, no tables found.")
        return
    
    print("Found tables:", tables)
    
    for table in tables:
        print_table_contents(conn, table)

if __name__ == "__main__":
    main()