"""
Ответственность:
Клиент для взаимодействия с Checko API через /v2/finances
Проверяет, существует ли компания по ИНН и действителен ли её статус ("Действует")
"""

import requests

class FinancialAPIClient:
    BASE_URL = "https://api.checko.ru/v2/finances" 

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_company_data(self, inn: str) -> dict:
        """
        Получает данные компании через /v2/finances
        Проверяет:
        - Статус HTTP (200 OK)
        - meta.status == 'ok'
        - Наличие данных в поле company
        - company.Статус == 'Действует'
        """
        print(f"[DEBUG] Отправляем запрос к Checko для ИНН {inn}...")

        params = {
            "key": self.api_key,
            "inn": inn
        }

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

        # Проверяем meta.status
        meta = data.get("meta", {})
        if meta.get("status") != "ok":
            error_msg = meta.get("message", "Неизвестная ошибка")
            raise Exception(f"Ошибка в метаданных Checko: {error_msg}")

        # Проверяем, есть ли данные о компании
        company_info = data.get("company", {})
        if not company_info:
            raise Exception("В ответе нет данных о компании. Возможно, ключ не поддерживает доступ к данным.")

        # Проверяем статус компании
        status = company_info.get("Статус")
        if status != "Действует":
            raise ValueError(f"Компания с ИНН {inn} не зарегистрирована или не действует. Статус: {status}")

        return data

    def get_company_info(self, inn: str) -> dict:
        """
        Возвращает основные данные о компании.
        """
        data = self.fetch_company_data(inn)
        company = data.get("company", {})

        return {
            "name": company.get("НаимПолн", "Название компании не найдено"),
            "short_name": company.get("НаимСокр", "Сокращённое название не найдено"),
            "status": company.get("Статус", "Статус не найден"),
            "ogrn": company.get("ОГРН", "ОГРН не найден"),
            "kpp": company.get("КПП", "КПП не найден"),
            "registration_date": company.get("ДатаРег", "Дата регистрации не найдена"),
            "address": company.get("ЮрАдрес", "Адрес не найден"),
            "okved": company.get("ОКВЭД", "ОКВЭД не найден")
        }