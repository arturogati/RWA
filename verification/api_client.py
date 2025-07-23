"""
Responsabilité :
Client pour interagir avec l'API Checko via /v2/finances
Vérifie si une entreprise existe par son numéro d'identification (INN) et si son statut est valide ("Actif")
"""

import requests

class FinancialAPIClient:
    BASE_URL = "https://api.checko.ru/v2/finances" 

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_company_data(self, inn: str) -> dict:
        """
        Récupère les données d'une entreprise via /v2/finances
        Vérifie :
        - Le statut HTTP (200 OK)
        - meta.status == 'ok'
        - La présence de données dans le champ company
        - company.Statut == 'Actif'
        """
        print(f"[DEBUG] Envoi d'une requête à Checko pour l'INN {inn}...")

        params = {
            "key": self.api_key,
            "inn": inn
        }

        try:
            response = requests.get(self.BASE_URL, params=params)
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erreur réseau : {e}")

        if response.status_code != 200:
            raise Exception(f"Erreur HTTP : {response.status_code}, Texte : {response.text}")

        try:
            data = response.json()
        except ValueError:
            raise Exception("Impossible d'analyser le JSON de Checko.")

        # Vérification de meta.status
        meta = data.get("meta", {})
        if meta.get("status") != "ok":
            error_msg = meta.get("message", "Erreur inconnue")
            raise Exception(f"Erreur dans les métadonnées Checko : {error_msg}")

        # Vérification de la présence de données sur l'entreprise
        company_info = data.get("company", {})
        if not company_info:
            raise Exception("Aucune donnée d'entreprise dans la réponse. La clé API ne permet peut-être pas d'accéder à ces données.")

        # Vérification du statut de l'entreprise
        status = company_info.get("Statut")
        if status != "Actif":
            raise ValueError(f"L'entreprise avec l'INN {inn} n'est pas enregistrée ou inactive. Statut : {status}")

        return data

    def get_company_info(self, inn: str) -> dict:
        """
        Retourne les informations principales sur l'entreprise.
        """
        data = self.fetch_company_data(inn)
        company = data.get("company", {})

        return {
            "name": company.get("NomComplet", "Nom d'entreprise introuvable"),
            "short_name": company.get("NomCourt", "Nom abrégé introuvable"),
            "status": company.get("Statut", "Statut introuvable"),
            "ogrn": company.get("OGRN", "OGRN introuvable"),
            "kpp": company.get("KPP", "KPP introuvable"),
            "registration_date": company.get("DateEnreg", "Date d'enregistrement introuvable"),
            "address": company.get("AdresseLegale", "Adresse introuvable"),
            "okved": company.get("OKVED", "OKVED introuvable")
        }