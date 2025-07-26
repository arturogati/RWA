"""
Ответственность:
Клиент для Checko API — проверка компании по ИНН.
"""

import requests

class FinancialAPIClient:
    BASE_URL = "https://api.checko.ru/v2/finances"  # ⚠️ Без пробела в конце!

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_company_data(self, inn: str) -> dict:
        params = {"key": self.api_key, "inn": inn}
        try:
            response = requests.get(self.BASE_URL, params=params)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка сети: {e}")

        if response.status_code != 200:
            raise Exception(f"Ошибка HTTP: {response.status_code}, Текст: {response.text}")

        try:
            data = response.json()
        except ValueError:
            raise Exception("Не удалось разобрать JSON от Checko.")

        meta = data.get("meta", {})
        if meta.get("status") != "ok":
            error_msg = meta.get("message", "Неизвестная ошибка")
            raise Exception(f"Ошибка в метаданных Checko: {error_msg}")

        company_info = data.get("company", {})
        if not company_info:
            raise Exception("Нет данных о компании. Убедитесь, что ключ поддерживает доступ.")

        status = company_info.get("Статус")
        if status != "Действует":
            raise ValueError(f"Компания с ИНН {inn} не действует. Статус: {status}")

        return data

    def get_company_info(self, inn: str) -> dict:
        data = self.fetch_company_data(inn)
        company = data.get("company", {})
        return {
            "name": company.get("НаимПолн", "Неизвестное название"),
            "short_name": company.get("НаимСокр", "Неизвестное сокращение"),
            "status": company.get("Статус", "Неизвестный статус"),
            "ogrn": company.get("ОГРН", "Неизвестный ОГРН"),
            "kpp": company.get("КПП", "Неизвестный КПП"),
            "registration_date": company.get("ДатаРег", "Неизвестная дата"),
            "address": company.get("ЮрАдрес", "Неизвестный адрес"),
            "okved": company.get("ОКВЭД", "Неизвестный ОКВЭД"),
            "revenue": company.get("Выручка", 0)
        }