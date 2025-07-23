"""
TokenizeLocal Console App - Version miroir du bot Telegram
"""

import os
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Initialisation
logger = Logger("TokenizeLocalConsole")
checko_api_key = "yCEWUepinagwBCn3"  # ou charger depuis .env
db = DBManager()
user_manager = UserManager()

def show_help():
    print("""
🔍 Commandes disponibles:
1. Se connecter en tant qu'utilisateur
2. S'inscrire comme utilisateur
3. Mode entreprise
4. Émettre des tokens
5. Liste des entreprises
6. Acheter des tokens
7. Mon solde
8. Aide
9. Quitter
    """)

def login_user():
    print("\n🔐 Connexion utilisateur")
    email = input("Email: ").strip()
    password = input("Mot de passe: ").strip()

    if user_manager.authenticate_user(email, password):
        print(f"[INFO] Connexion réussie pour {email}")
        return email
    else:
        print("[ERREUR] Email ou mot de passe incorrect.")
        return None

def register_user():
    print("\n📝 Inscription d'un nouvel utilisateur")
    name = input("Nom: ").strip()
    email = input("Email: ").strip()
    password = input("Mot de passe: ").strip()

    try:
        user_manager.register_user(name, email, password)
        print(f"[INFO] Inscription réussie! Bienvenue, {name}!")
        return email
    except UserAlreadyExists:
        print("[ERREUR] Un utilisateur avec cet email existe déjà.")
    except InvalidEmail:
        print("[ERREUR] Email invalide.")
    except Exception as e:
        print(f"[ERREUR] Erreur d'inscription: {e}")
    return None

def company_mode():
    print("\n🏢 Mode entreprise")
    inn = input("Entrez le numéro INN de l'entreprise: ").strip()

    if len(inn) not in (10, 12) or not inn.isdigit():
        print("[ERREUR] Format INN invalide. Doit contenir 10 ou 12 chiffres.")
        return

    try:
        api_client = FinancialAPIClient(checko_api_key)
        company_info = api_client.get_company_info(inn)
        print(f"[INFO] Entreprise trouvée: {company_info['name']}")
        print(f"Statut: {company_info['status']}")

        amount_input = input("Nombre de tokens à émettre: ")
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError("Le nombre doit être positif.")

        db.register_or_update_business(inn, company_info["name"])
        db.issue_tokens(inn, amount)
        print(f"[INFO] {amount} tokens émis pour l'entreprise '{company_info['name']}'")

    except Exception as e:
        print(f"[ERREUR] Erreur d'émission de tokens: {e}")

def show_companies():
    print("\n📋 Entreprises disponibles:")
    companies = db.get_all_issuances()
    if not companies:
        print("Aucune entreprise disponible.")
        return

    for idx, (inn, name, amount, _) in enumerate(companies):
        print(f"{idx+1}. {name} (INN: {inn}) — tokens disponibles: {amount or 0}")

def buy_tokens(email):
    print("\n🛒 Achat de tokens")
    show_companies()
    choice = input("Choisissez le numéro d'entreprise: ").strip()
    amount_input = input("Nombre de tokens à acheter: ").strip()

    try:
        company_num = int(choice)
        amount = float(amount_input)

        if company_num <= 0 or amount <= 0:
            raise ValueError("Les nombres doivent être positifs")

        companies = db.get_all_issuances()
        if company_num > len(companies):
            raise ValueError("Cette entreprise n'existe pas")

        inn, name, available, _ = companies[company_num - 1]
        if available is None or amount > available:
            raise ValueError(f"Tokens insuffisants. Disponible: {available or 0}")

        db.issue_tokens(inn, -amount)
        db.add_user_tokens(email=email, business_inn=inn, amount=amount)

        user_tokens = db.get_user_tokens(email)
        current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

        print(f"\n✅ Achat réussi de {amount} tokens de '{name}'")
        print(f"Votre solde actuel: {current_amount}")
    except ValueError as e:
        print(f"[ERREUR] Erreur de saisie: {e}")
    except Exception as e:
        print(f"[ERREUR] Erreur inattendue: {e}")

def show_balance(email):
    print("\n💰 Votre solde:")
    tokens = db.get_user_tokens(email)
    if not tokens:
        print("Vous n'avez pas encore de tokens.")
        return
    for row in tokens:
        inn, name, token_count = row
        print(f"- {name}: {token_count} tokens")

def run_full_demo():
    print("=== Application Console TokenizeLocal ===")
    email = None
    role = None

    while True:
        show_help()
        choice = input("Choisissez une action (1-9): ").strip()

        if choice == "1":
            email = login_user()
            role = "user"
        elif choice == "2":
            email = register_user()
            role = "user"
        elif choice == "3":
            role = "company"
        elif choice == "4":
            if role == "company":
                company_mode()
            else:
                print("[ERREUR] Sélectionnez le mode entreprise.")
        elif choice == "5":
            show_companies()
        elif choice == "6":
            if role == "user" and email:
                buy_tokens(email)
            else:
                print("[ERREUR] Connectez-vous d'abord comme utilisateur.")
        elif choice == "7":
            if role == "user" and email:
                show_balance(email)
            else:
                print("[ERREUR] Connectez-vous d'abord comme utilisateur.")
        elif choice == "8":
            show_help()
        elif choice == "9":
            print("Déconnexion...")
            break
        else:
            print("[ERREUR] Choix invalide.")

if __name__ == "__main__":
    run_full_demo()