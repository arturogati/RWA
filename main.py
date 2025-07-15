"""
TokenizeLocal Console App - зеркальная версия Telegram-бота
"""

import os
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Инициализация
logger = Logger("TokenizeLocalConsole")
checko_api_key = "yCEWUepinagwBCn3"  # или загрузите из .env
db = DBManager()
user_manager = UserManager()

def show_help():
    print("""
🔍 Доступные команды:
1. Войти как пользователь
2. Зарегистрироваться как пользователь
3. Войти как компания
4. Выпустить токены
5. Список компаний
6. Купить токены
7. Мой баланс
8. Помощь
9. Выход
    """)

def login_user():
    print("\n🔐 Вход как пользователь")
    email = input("Введите email: ").strip()
    password = input("Введите пароль: ").strip()

    if user_manager.authenticate_user(email, password):
        print(f"[INFO] Вход выполнен успешно для {email}")
        return email
    else:
        print("[ERROR] Неверный email или пароль.")
        return None

def register_user():
    print("\n📝 Регистрация нового пользователя")
    name = input("Имя: ").strip()
    email = input("Email: ").strip()
    password = input("Пароль: ").strip()

    try:
        user_manager.register_user(name, email, password)
        print(f"[INFO] Регистрация успешна! Добро пожаловать, {name}!")
        return email
    except UserAlreadyExists:
        print("[ERROR] Пользователь с таким email уже существует.")
    except InvalidEmail:
        print("[ERROR] Некорректный email.")
    except Exception as e:
        print(f"[ERROR] Ошибка регистрации: {e}")
    return None

def company_mode():
    print("\n🏢 Режим компании")
    inn = input("Введите ИНН компании: ").strip()

    if len(inn) not in (10, 12) or not inn.isdigit():
        print("[ERROR] Неверный формат ИНН. Должно быть 10 или 12 цифр.")
        return

    try:
        api_client = FinancialAPIClient(checko_api_key)
        company_info = api_client.get_company_info(inn)
        print(f"[INFO] Компания найдена: {company_info['name']}")
        print(f"Статус: {company_info['status']}")

        amount_input = input("Сколько токенов выпустить? ")
        amount = float(amount_input)
        if amount <= 0:
            raise ValueError("Количество должно быть положительным.")

        db.register_or_update_business(inn, company_info["name"])
        db.issue_tokens(inn, amount)
        print(f"[INFO] Выпущено {amount} токенов для компании '{company_info['name']}'")

    except Exception as e:
        print(f"[ERROR] Ошибка выпуска токенов: {e}")

def show_companies():
    print("\n📋 Доступные компании:")
    companies = db.get_all_issuances()
    if not companies:
        print("Нет доступных компаний.")
        return

    for idx, (inn, name, amount, _) in enumerate(companies):
        print(f"{idx+1}. {name} (ИНН: {inn}) — доступно токенов: {amount or 0}")

def buy_tokens(email):
    print("\n🛒 Покупка токенов")
    show_companies()
    choice = input("Выберите номер компании: ").strip()
    amount_input = input("Сколько токенов хотите купить? ").strip()

    try:
        company_num = int(choice)
        amount = float(amount_input)

        if company_num <= 0 or amount <= 0:
            raise ValueError("Числа должны быть положительными")

        companies = db.get_all_issuances()
        if company_num > len(companies):
            raise ValueError("Компании с таким номером не существует")

        inn, name, available, _ = companies[company_num - 1]
        if available is None or amount > available:
            raise ValueError(f"Недостаточно токенов. Доступно: {available or 0}")

        db.issue_tokens(inn, -amount)
        db.add_user_tokens(email=email, business_inn=inn, amount=amount)

        user_tokens = db.get_user_tokens(email)
        current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

        print(f"\n✅ Успешно куплено {amount} токенов компании '{name}'")
        print(f"Ваш текущий баланс: {current_amount}")
    except ValueError as e:
        print(f"[ERROR] Ошибка ввода: {e}")
    except Exception as e:
        print(f"[ERROR] Неожиданная ошибка: {e}")

def show_balance(email):
    print("\n💰 Ваш баланс:")
    tokens = db.get_user_tokens(email)
    if not tokens:
        print("У вас пока нет токенов.")
        return
    for row in tokens:
        inn, name, token_count = row
        print(f"- {name}: {token_count} токенов")

def run_full_demo():
    print("=== TokenizeLocal Console App ===")
    email = None
    role = None

    while True:
        show_help()
        choice = input("Выберите действие (1-9): ").strip()

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
                print("[ERROR] Выберите роль компании.")
        elif choice == "5":
            show_companies()
        elif choice == "6":
            if role == "user" and email:
                buy_tokens(email)
            else:
                print("[ERROR] Сначала войдите как пользователь.")
        elif choice == "7":
            if role == "user" and email:
                show_balance(email)
            else:
                print("[ERROR] Сначала войдите как пользователь.")
        elif choice == "8":
            show_help()
        elif choice == "9":
            print("Выход...")
            break
        else:
            print("[ERROR] Неверный выбор.")

if __name__ == "__main__":
    run_full_demo()