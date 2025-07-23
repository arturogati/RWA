"""
Responsibilities:
Client for interacting with Checko API via /v2/finances
Checks if a company exists by INN and whether its status is "Active"
"""

import requests

class FinancialAPIClient:
    BASE_URL = "https://api.checko.ru/v2/finances" 

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_company_data(self, inn: str) -> dict:
        """
        Retrieves company data via /v2/finances
        Verifies:
        - HTTP status (200 OK)
        - meta.status == 'ok'
        - Presence of data in company field
        - company.Status == 'Active'
        """
        print(f"[DEBUG] Sending request to Checko for INN {inn}...")

        params = {
            "key": self.api_key,
            "inn": inn
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error: {e}")

        if response.status_code != 200:
            raise Exception(f"HTTP error: {response.status_code}, Text: {response.text}")

        try:
            data = response.json()
        except ValueError:
            raise Exception("Failed to parse JSON from Checko.")

        # Verify meta.status
        meta = data.get("meta", {})
        if meta.get("status") != "ok":
            error_msg = meta.get("message", "Unknown error")
            raise Exception(f"Checko metadata error: {error_msg}")

        # Verify company data exists
        company_info = data.get("company", {})
        if not company_info:
            raise Exception("Response contains no company data. The API key may not have sufficient permissions.")

        # Verify company status
        status = company_info.get("Status")
        if status != "Active":
            raise ValueError(f"Company with INN {inn} is not registered or inactive. Status: {status}")

        return data

    def get_company_info(self, inn: str) -> dict:
        """
        Returns core company information.
        """
        data = self.fetch_company_data(inn)
        company = data.get("company", {})

        return {
            "name": company.get("FullName", "Company name not found"),
            "short_name": company.get("ShortName", "Short name not found"),
            "status": company.get("Status", "Status not found"),
            "ogrn": company.get("OGRN", "OGRN not found"),
            "kpp": company.get("KPP", "KPP not found"),
            "registration_date": company.get("RegDate", "Registration date not found"),
            "address": company.get("LegalAddress", "Address not found"),
            "okved": company.get("OKVED", "OKVED not found")
        }