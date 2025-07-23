"""
TokenizeLocal Console App - mirror version of Telegram bot
"""

import os
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Initialization
logger = Logger("TokenizeLocalConsole")
checko_api_key = "yCEWUepinagwBCn3"  # or load from .env
db = DBManager()
user_manager = UserManager()

def show_help():
    print("""
🔍 Available commands:
1. Login as user
2. Register as user
3. Login as company
4. Issue tokens
5. List companies
6. Buy tokens
7. My balance
8. Help
9. Exit
    """)

def login_user():
    print("\n🔐 User login")
    email = input("Enter email: ").strip()
    password = input("Enter password: ").strip()

    if user_manager.authenticate_user(email, password):
        print(f"[INFO] Login successful for {email}")
        return email
    else:
        print("[ERROR] Invalid email or password.")
        return None

def register_user():
    print("\n📝 New user registration")
    name = input("Name: ").strip()
    email = input("Email: ").strip()
    password = input("Password: ").strip()

    try:
        user_manager.register_user(name, email, password)
        print(f"[INFO] Registration successful! Welcome, {name}!")
        return email
    except UserAlreadyExists:
        print("[ERROR] User with this email already exists.")
    except InvalidEmail:
        print("[ERROR] Invalid email format.")
    except Exception as e:
        print(f"[ERROR] Registration error: {e}")
    return None

def company_mode():
    print("\n🏢 Company mode")
    inn = input("Enter company TIN: ").strip()

    if len(inn) not in (10, 12) or not inn.isdigit():
        print("[ERROR] Invalid TIN format. Must be 10 or 12 digits.")
        return

    try:
        api_client = FinancialAPIClient(checko_api_key)
        company_info = api_client.get_company_info(inn)
        print(f"[INFO] Company found: {company_info['name']}")
        print(f"Status: {company_info['status']}")

        amount_input = input("How many tokens to issue? ")
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError("Amount must be positive.")

        db.register_or_update_business(inn, company_info["name"])
        db.issue_tokens(inn, amount)
        print(f"[INFO] Issued {amount} tokens for company '{company_info['name']}'")

    except Exception as e:
        print(f"[ERROR] Token issuance error: {e}")

def show_companies():
    print("\n📋 Available companies:")
    companies = db.get_all_issuances()
    if not companies:
        print("No companies available.")
        return

    for idx, (inn, name, amount, _) in enumerate(companies):
        print(f"{idx+1}. {name} (TIN: {inn}) — available tokens: {amount or 0}")

def buy_tokens(email):
    print("\n🛒 Token purchase")
    show_companies()
    choice = input("Select company number: ").strip()
    amount_input = input("How many tokens do you want to buy? ").strip()

    try:
        company_num = int(choice)
        amount = float(amount_input)

        if company_num <= 0 or amount <= 0:
            raise ValueError("Values must be positive")

        companies = db.get_all_issuances()
        if company_num > len(companies):
            raise ValueError("Company with this number doesn't exist")

        inn, name, available, _ = companies[company_num - 1]
        if available is None or amount > available:
            raise ValueError(f"Not enough tokens. Available: {available or 0}")

        db.issue_tokens(inn, -amount)
        db.add_user_tokens(email=email, business_inn=inn, amount=amount)

        user_tokens = db.get_user_tokens(email)
        current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

        print(f"\n✅ Successfully purchased {amount} tokens of '{name}'")
        print(f"Your current balance: {current_amount}")
    except ValueError as e:
        print(f"[ERROR] Input error: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")

def show_balance(email):
    print("\n💰 Your balance:")
    tokens = db.get_user_tokens(email)
    if not tokens:
        print("You don't have any tokens yet.")
        return
    for row in tokens:
        inn, name, token_count = row
        print(f"- {name}: {token_count} tokens")

def run_full_demo():
    print("=== TokenizeLocal Console App ===")
    email = None
    role = None

    while True:
        show_help()
        choice = input("Select action (1-9): ").strip()

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
                print("[ERROR] Select company role first.")
        elif choice == "5":
            show_companies()
        elif choice == "6":
            if role == "user" and email:
                buy_tokens(email)
            else:
                print("[ERROR] Please login as user first.")
        elif choice == "7":
            if role == "user" and email:
                show_balance(email)
            else:
                print("[ERROR] Please login as user first.")
        elif choice == "8":
            show_help()
        elif choice == "9":
            print("Exiting...")
            break
        else:
            print("[ERROR] Invalid choice.")

if __name__ == "__main__":
    run_full_demo()