"""
Responsabilité :
Script de test pour vérifier le contenu de la base de données.
"""

import sqlite3
import os

def get_db_connection(db_path="database.sqlite"):
    """
    Crée une connexion à la base de données SQLite.
    Vérifie si le fichier de base de données existe.
    """
    print(f"[DEBUG] Connexion à la base de données : {db_path}")
    
    if not os.path.exists(db_path):
        print(f"[ERROR] Fichier de base de données introuvable : {db_path}")
        choice = input("Voulez-vous créer une nouvelle base de données ? (y/n) : ").strip().lower()
        if choice == "y":
            open(db_path, 'w').close()  # Crée un fichier vide
            print(f"[INFO] Nouvelle base de données créée à : {db_path}")
        else:
            exit(1)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Accès aux colonnes par nom
    return conn

def list_tables(conn):
    """Retourne la liste des tables dans la base de données."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row["name"] for row in cursor.fetchall()]
    return tables

def print_table_contents(conn, table_name):
    """Affiche le contenu de la table spécifiée."""
    print(f"\n--- Table : {table_name} ---")

    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [info[1] for info in cursor.fetchall()]
        print("Colonnes :", ", ".join(columns))

        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print("La table est vide.")
            return

        for row in rows:
            print(dict(row))  # Affichage sous forme de dictionnaire pour plus de lisibilité

    except sqlite3.OperationalError as e:
        print(f"[Erreur] Impossible de lire la table '{table_name}' : {e}")

def main():
    print("=== Vérification du contenu de la base de données ===\n")
    
    db_path = "database.sqlite"
    
    conn = get_db_connection(db_path)
    
    tables = list_tables(conn)
    
    if not tables:
        print("La base de données est vide, aucune table trouvée.")
        return
    
    print("Tables trouvées :", tables)
    
    for table in tables:
        print_table_contents(conn, table)

if __name__ == "__main__":
    main()