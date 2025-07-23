"""
Responsabilité :
Logique de vérification des entreprises via l'API des rapports financiers.
"""

from verification.api_client import FinancialAPIClient

class BusinessVerifier:
    def __init__(self, financial_api_key: str):
        self.financial_client = FinancialAPIClient(financial_api_key)

    def verify(self, inn: str) -> dict:
        """
        Vérifie une entreprise via l'API des rapports financiers.
        """
        try:
            company_info = self.financial_client.get_company_info(inn)
        except Exception as e:
            return {"status": "REJECTED", "message": str(e)}

        return {
            "status": "APPROVED",
            "company_name": company_info["name"],
            "last_year_revenue": company_info["revenue"]
        }