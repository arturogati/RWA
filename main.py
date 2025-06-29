"""
Ответственность:
Точка входа в приложение. Проверка статуса компании и выпуск токенов.
"""

import os
import sys
from dotenv import load_dotenv

# Подгружаем переменные окружения
load_dotenv()

from verification.api_client import FinancialAPIClient
from blockchain.db_manager import DBManager
from utils.logger import Logger


def run_full_demo():
    logger = Logger("TokenizeLocal")
    logger.log("=== Токенизация бизнеса через БД ===")

    # Шаг 0: Получаем API-ключ
    checko_api_key = os.getenv("CHECKO_API_KEY", "yCEWUepinagwBCn3")
    if not checko_api_key or checko_api_key == "your_checko_api_key":
        logger.log("[ERROR] Не найден CHECKO_API_KEY", level="ERROR")
        sys.exit(1)

    # Шаг 1: Инициализируем клиентов
    card_client = FinancialAPIClient(api_key=checko_api_key)
    db = DBManager()

    # Шаг 2: Ввод данных
    inn = input("Введите ИНН компании для токенизации: ").strip()
    tokens_input = input("Сколько токенов выпустить? ").strip()

    try:
        tokens = float(tokens_input)
        if tokens <= 0:
            raise ValueError("Количество токенов должно быть положительным.")
    except ValueError as e:
        logger.log(f"[ERROR] Ошибка: {e}", level="ERROR")
        sys.exit(1)

    # Шаг 3: Проверка компании через /v2/card
    logger.log(f"\n[INFO] Проверяем компанию с ИНН {inn} через Checko API...")

    try:
        company_info = card_client.get_company_info(inn)
        logger.log(f"[INFO] Компания найдена: {company_info['name']}")
        logger.log(f"Статус: {company_info['status']} — можно выпускать токены.")
    except Exception as e:
        logger.log(f"[ERROR] Компания не прошла проверку: {e}", level="ERROR")
        sys.exit(1)

    # Шаг 4: Регистрация/обновление компании в БД
    logger.log("\n[INFO] Регистрация/обновление компании в локальной БД...")
    try:
        db.register_or_update_business(inn=inn, name=company_info["name"])
    except Exception as e:
        logger.log(f"[ERROR] Не удалось зарегистрировать бизнес: {e}", level="ERROR")
        sys.exit(1)

    # Шаг 5: Выпуск токенов
    logger.log(f"\n[INFO] Выпуск {tokens} токенов для компании '{company_info['name']}'...")
    try:
        db.issue_tokens(inn=inn, amount=tokens)
    except Exception as e:
        logger.log(f"[ERROR] Не удалось выпустить токены: {e}", level="ERROR")
        sys.exit(1)

    # Шаг 6: Вывод информации о токенах
    token_stats = db.get_token_stats(inn=inn)
    if "error" in token_stats:
        logger.log(token_stats["error"], level="ERROR")
    else:
        logger.log("\n📊 Информация о токенах:")
        logger.log(f"ИНН: {token_stats['inn']}")
        logger.log(f"Название: {token_stats['name']}")
        logger.log(f"Выпущено токенов: {token_stats['total_issued']}")
        logger.log(f"Дата выпуска: {token_stats['issued_at']}")

    # Шаг 7: Вывод всех компаний из БД
    logger.log("\n📋 Все компании и их токены:")
    all_issuances = db.get_all_issuances()
    for row in all_issuances:
        inn_db, name_db, amount_db, issued_at_db = row
        amount = amount_db if amount_db is not None else 0
        issued_at = issued_at_db if issued_at_db else "не установлено"
        logger.log(f"ИНН: {inn_db} | Название: {name_db} | Выпущено: {amount} | Дата: {issued_at}")

    logger.log("\n✅ Токенизация завершена.")


if __name__ == "__main__":
    run_full_demo()