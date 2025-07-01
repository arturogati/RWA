"""
Ответственность:
Точка входа в приложение. Выбор между пользователем и компанией.
"""

import os
import sys
from dotenv import load_dotenv

# Подгружаем переменные окружения
load_dotenv()

from verification.api_client import FinancialAPIClient
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from utils.logger import Logger


def run_full_demo():
    logger = Logger("TokenizeLocal")
    logger.log("=== Токенизация бизнеса через БД ===")

    checko_api_key = os.getenv("CHECKO_API_KEY", "yCEWUepinagwBCn3")
    if not checko_api_key or checko_api_key == "your_checko_api_key":
        logger.log("[ERROR] Не найден CHECKO_API_KEY", level="ERROR")
        sys.exit(1)

    # Инициализируем клиентов
    card_client = FinancialAPIClient(api_key=checko_api_key)
    db = DBManager()
    user_manager = UserManager()

    # --- Выбор роли: пользователь или компания ---
    role = input("Вы пользователь или компания? (user/company): ").strip().lower()
    if role not in ("user", "company"):
        logger.log("[ERROR] Неверная роль.", level="ERROR")
        sys.exit(1)

    if role == "user":
        logger.log("\n[INFO] Режим пользователя.")
        email = input("Введите ваш email: ").strip()
        password = input("Введите пароль: ").strip()

        try:
            # Попытка авторизации
            if user_manager.authenticate_user(email, password):
                print(f"[INFO] Пользователь {email} авторизован.")
            else:
                name = input("Пользователь не найден. Введите имя для регистрации: ")
                user_manager.register_user(name, email, password)
                print(f"[INFO] Новый пользователь зарегистрирован: {email}")
        except Exception as e:
            logger.log(f"[ERROR] Ошибка авторизации: {e}", level="ERROR")
            sys.exit(1)

        # --- Вывод всех компаний ---
        logger.log("\n[INFO] Доступные компании:")
        all_issuances = db.get_all_issuances()
        available_companies = []

        for idx, row in enumerate(all_issuances):
            inn_db, name_db, amount_db, issued_at_db = row
            amount = amount_db if amount_db is not None else 0
            print(f"{idx+1}. {name_db} (ИНН: {inn_db}) — доступно токенов: {amount}")
            available_companies.append({"inn": inn_db, "name": name_db, "available": amount})

        if not available_companies:
            logger.log("[INFO] Нет доступных компаний.")
            sys.exit(0)

        # --- Выбор компании и покупка токенов ---
        choice = int(input("\nВыберите номер компании для покупки: ")) - 1
        if not (0 <= choice < len(available_companies)):
            logger.log("[ERROR] Неверный выбор компании.", level="ERROR")
            sys.exit(1)

        selected = available_companies[choice]
        max_tokens = selected["available"]

        buy_amount = float(input(f"Сколько токенов хотите купить (доступно: {max_tokens})? "))
        if buy_amount <= 0 or buy_amount > max_tokens:
            logger.log("[ERROR] Недостаточно токенов.", level="ERROR")
            sys.exit(1)

        # --- Списание из общего пула и зачисление пользователю ---
        try:
            db.issue_tokens(inn=selected["inn"], amount=-buy_amount)  # Уменьшаем общий пул
            db.add_user_tokens(email=email, business_inn=selected["inn"], amount=buy_amount)
            logger.log(f"\n✅ Вы купили {buy_amount} токенов компании '{selected['name']}'")
        except Exception as e:
            logger.log(f"[ERROR] Не удалось купить токены: {e}", level="ERROR")
            sys.exit(1)

        # --- Отображение текущих токенов пользователя ---
        print("\n💼 Ваши токены:")
        user_tokens = db.get_user_tokens(email)
        if not user_tokens:
            print("Нет токенов.")
        else:
            for row in user_tokens:
                inn_db, name_db, token_count = row
                print(f"- {name_db} ({inn_db}): {token_count} токенов")

        logger.log("\n✅ Токенизация завершена.")
    else:
        logger.log("\n[INFO] Режим компании.")

        inn = input("Введите ИНН компании для токенизации: ").strip()
        tokens_input = input("Сколько токенов выпустить? ").strip()

        try:
            tokens = float(tokens_input)
            if tokens <= 0:
                raise ValueError("Количество токенов должно быть положительным.")
        except ValueError as e:
            logger.log(f"[ERROR] Ошибка: {e}", level="ERROR")
            sys.exit(1)

        # --- Проверка компании через Checko API ---
        logger.log(f"\n[INFO] Проверяем компанию с ИНН {inn} через Checko API...")

        try:
            company_info = card_client.get_company_info(inn)
            logger.log(f"[INFO] Компания найдена: {company_info['name']}")
            logger.log(f"Статус: {company_info['status']} — можно выпускать токены.")
        except Exception as e:
            logger.log(f"[ERROR] Компания не прошла проверку: {e}", level="ERROR")
            sys.exit(1)

        # --- Регистрация/обновление компании в БД ---
        logger.log("\n[INFO] Регистрация/обновление компании в локальной БД...")
        try:
            db.register_or_update_business(inn=inn, name=company_info["name"])
        except Exception as e:
            logger.log(f"[ERROR] Не удалось зарегистрировать бизнес: {e}", level="ERROR")
            sys.exit(1)

        # --- Выпуск токенов ---
        logger.log(f"\n[INFO] Выпуск {tokens} токенов для компании '{company_info['name']}'...")
        try:
            db.issue_tokens(inn=inn, amount=tokens)
        except Exception as e:
            logger.log(f"[ERROR] Не удалось выпустить токены: {e}", level="ERROR")
            sys.exit(1)

        # --- Вывод информации о токенах ---
        token_stats = db.get_token_stats(inn=inn)
        if "error" in token_stats:
            logger.log(token_stats["error"], level="ERROR")
        else:
            logger.log("\n📊 Информация о токенах:")
            logger.log(f"ИНН: {token_stats['inn']}")
            logger.log(f"Название: {token_stats['name']}")
            logger.log(f"Выпущено токенов: {token_stats['total_issued']}")
            logger.log(f"Дата выпуска: {token_stats['issued_at']}")

        logger.log("\n✅ Токенизация завершена.")


if __name__ == "__main__":
    run_full_demo()