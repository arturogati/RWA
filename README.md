

---
# 📊 **TokenizeLocal : Documentation technique**
## 🔍 Description générale  
**TokenizeLocal** est une plateforme de tokenisation des entreprises locales, permettant aux utilisateurs d’acheter des jetons numériques représentant une part dans une entreprise réelle.  
Chaque jeton donne droit à des **dividendes mensuels**, proportionnels au chiffre d’affaires de l’entreprise.
---
## 🧠 Composants principaux du système
```
+---------------------+
|    Bot Telegram     |
| (Interface          |
| utilisateur)        |
+----------+----------+
           |
           v
+---------------------+
|  TelegramBotHandler |
| (Gestionnaires de   |
| commandes, états,    |
| logique)             |
+----------+----------+
           |
           v
+---------------------+
|      DBManager      |
| (Opérations CRUD sur |
| les entreprises,     |
| les jetons et        |
| les soldes)          |
+----------+----------+
           |
           v
+---------------------+
|  FinancialAPIClient |
| (API Checko /        |
| API internationales) |
+----------+----------+
           |
           v
+---------------------+
|      Base de données|
| (SQLite, fichier)   |
+---------------------+
```
---
## 🔄 Algorithme de fonctionnement du système
### 1. **Enregistrement de l’entreprise**
```
graph TD
    A[Entreprise] --> B[/issue_tokens]
    B --> C[Saisie de l’INN ou du VAT ID]
    C --> D[Validation du format : 10/12 chiffres (INN), 8-12 caractères (VAT)]
    D --> E[Passage à l’étape de vérification du statut de l’entreprise]
```
### 2. **Vérification de l’entreprise via l’API**
```
graph TD
    F[/issue_tokens] --> G[FinancialAPIClient.get_company_info()]
    G --> H{Vérification du statut : "Actif"}
    H -->|Oui| I[Obtention des états financiers]
    H -->|Non| J[Erreur : entreprise non enregistrée]
    I --> K[Calcul du nombre maximal de jetons]
```
---
## 🛡️ Bloc de vérification de l’entreprise
### 1. **L’entreprise s’enregistre et saisit son INN (ou VAT ID)**  
#### Identifiants pris en charge :
| Pays | Identifiant | Exemple |
|--------|----------------|--------|
| Russie | INN            | 5009051111 |
| États-Unis | EIN            | 123456789 |
| UE     | VAT ID         | DE276452187 |
#### Vérification du format :
```python
if not (len(inn) in (10, 12) and inn.isdigit()):
    raise ValueError("❌ Format INN invalide. Doit contenir 10 ou 12 chiffres.")
```
### 2. **Vérification du statut de l’entreprise et de ses états financiers via l’API**  
#### API utilisées :
| Région | API              | Fonction |
|--------|------------------|---------|
| Russie | Checko API       | `get_company_info()` |
| UE     | VIES             | Vérification du VAT ID |
| États-Unis | Dun & Bradstreet | Vérification de l’EIN et du statut |
| Global | OpenCorporates   | Données publiques sur les entreprises |
#### Logique de fonctionnement :
```python
def get_company_info(self, inn: str):
    """
    Récupère les informations de l'entreprise via l'API Checko.
    Valide le statut et les états financiers.
    """
    response = requests.get(f"{self.BASE_URL}?inn={inn}&key={self.api_key}")
    data = response.json()
    if data["meta"]["status"] != "ok":
        raise Exception(data["meta"]["message"])
    company = data.get("company", {})
    if company.get("Status") != "Active":
        raise ValueError(f"Entreprise non enregistrée ou inactive. Statut : {company.get('Status')}")
    return {
        "name": company.get("Full Name", "Nom inconnu"),
        "short_name": company.get("Short Name", "Abréviation inconnue"),
        "status": company.get("Status", "Statut inconnu"),
        "revenue": company.get("Revenue", 0)
    }
```
### 3. **Émission de jetons**
#### Limite basée sur le chiffre d’affaires :
```python
max_tokens = revenue * 0.1 / token_price
```
> Exemple :  
Chiffre d’affaires : 1 000 000 ₽  
Prix du jeton : 100 ₽  
Nombre maximal de jetons : 1 000 unités.
#### Méthode :
```python
def issue_tokens(self, inn: str, amount: float):
    with self.conn:
        cursor = self.conn.cursor()
        cursor.execute("SELECT business_inn FROM token_issuances WHERE business_inn = ?", (inn,))
        if cursor.fetchone():
            cursor.execute("UPDATE token_issuances SET amount = ? WHERE business_inn = ?", (amount, inn))
        else:
            cursor.execute("INSERT INTO token_issuances (business_inn, amount) VALUES (?, ?)", (inn, amount))
```
---
## 🔄 Algorithme de fonctionnement du système
### 1. **Enregistrement de l’entreprise**
```
graph TD
    L[/issue_tokens] --> M[Saisie de l’INN]
    M --> N[Validation du format]
    N --> O[FinancialAPIClient.get_company_info()]
    O --> P[Récupération des données de statut et de chiffre d’affaires]
    P --> Q[DBManager.register_or_update_business()]
    Q --> R[Saisie du nombre de jetons]
    R --> S[DBManager.issue_tokens()]
    S --> T[Entreprise ajoutée au marché]
```
### 2. **Achat de jetons par l’utilisateur**
```
graph TD
    U[/buy] --> V[Sélection de l’entreprise dans la liste]
    V --> W[Saisie du nombre et du montant]
    W --> X[Validation de la disponibilité des jetons]
    X --> Y[DBManager.issue_tokens(inn, -amount)]
    Y --> Z[DBManager.add_user_tokens(email, inn, amount)]
    Z --> AA[Notification de confirmation d’achat]
```
---
## 🛠️ Implémentation technique
### 1. **Base de données (SQLite)**  
#### Tables :
| Table | Description |
|--------|----------|
| `businesses` | INN, nom de l’entreprise |
| `token_issuances` | Jetons émis, date d’émission |
| `users` | Email, nom, mot de passe |
| `user_tokens` | Solde de jetons des utilisateurs |
| `dividend_history` | Historique des paiements de dividendes |
#### Exemple SQL :
```sql
-- Afficher toutes les entreprises avec leurs jetons
SELECT b.name, t.amount, t.issued_at
FROM businesses b
JOIN token_issuances t ON b.inn = t.business_inn;
```
---
### 2. **API Checko**
#### Requête :
```python
api_client = FinancialAPIClient(api_key="your_api_key")
company_info = api_client.get_company_info("5009051111")  # INN de OOO Shokoladnitsa
```
#### Réponse :
```json
{
  "name": "OOO Shokoladnitsa",
  "status": "Active",
  "inn": "5009051111",
  "ogrn": "1027700123456",
  "address": "Moscou, rue Myasnitskaya, 1"
}
```
---
### 3. **DBManager**
#### Méthodes principales :
- `register_or_update_business()` → ajoute ou met à jour une entreprise.
- `issue_tokens()` → émet ou retire des jetons.
- `add_user_tokens()` → augmente le solde utilisateur.
- `distribute_dividends()` → distribue les dividendes.
- `get_token_stats()` → récupère les informations sur les jetons.
- `get_all_issuances()` → renvoie toutes les entreprises.
---
### 4. **Bot Telegram**
#### Fonctionnalités :
- Enregistrement / authentification
- Émission de jetons
- Achat de jetons
- Distribution de dividendes
- Consultation du solde
- Prise en charge des formats de saisie
- Journalisation des événements
---
## ✅ Critères techniques d’acceptation (TAC)
| № | Critère | Indicateur d’achèvement |
|---|---------|--------------------|
| 1 | Enregistrement de l’entreprise | ✔️ Possibilité d’enregistrement via INN / VAT ID |
| 2 | Vérification de l’entreprise via API | ✔️ Requête réussie et statut récupéré |
| 3 | Limite de jetons basée sur le chiffre d’affaires | ✔️ Limite implémentée |
| 4 | Émission de jetons par l’entreprise | ✔️ Jetons enregistrés dans la base de données |
| 5 | Mise à jour du solde après achat | ✔️ Table `user_tokens` mise à jour |
| 6 | Consultation de l’historique des jetons | ✔️ Commande `/balance` fonctionne correctement |
| 7 | Prise en charge des formats de saisie | ✔️ Gestion correcte des nombres et formats |
| 8 | Stockage des données | ✔️ Toutes les données sauvegardées dans SQLite |
| 9 | Intégration Telegram | ✔️ Le bot démarre et répond aux commandes |
| 10 | Journalisation des événements | ✔️ Toutes les actions sont journalisées |
---
## 📈 Plan de montée en échelle
| Direction | Implémentation |
|------------|-------------|
| API REST | FastAPI / Flask |
| Interface GUI | Streamlit / Tkinter |
| Gouvernance DAO | Snapshot / vote dans la base de données |
| Marché secondaire de jetons | Revente entre utilisateurs |
| Intégration blockchain | web3.py + contrats intelligents |
| Oracle | Réseau Pyth / Chainlink |
| Prise en charge de USDT / USDC | Pour la stabilité des dividendes |
| Émission automatique de dividendes | via cron ou Airflow |
| Hachage des mots de passe | bcrypt / hashlib |
| Historique des transactions | Table `dividend_history` |
---
## 📦 Fonctionnalités prévues
### 1. **Plafond de jetons basé sur le chiffre d’affaires de l’entreprise**  
> Introduire une limite sur le nombre maximal de jetons qu’une entreprise peut émettre, en fonction de son chiffre d’affaires et de sa valorisation.
#### Fonctionnement :
- Lors de l’émission de jetons, les éléments suivants seront calculés :
  - Chiffre d’affaires mensuel
  - Coefficient de capitalisation
- Nombre maximal de jetons = (Chiffre d’affaires × Coefficient) / Prix par jeton
#### Exemple :
- Chiffre d’affaires : 1 000 000 ₽
- Coefficient : 0,1
- Prix du jeton : 100 ₽
- Nombre max de jetons = (1 000 000 × 0,1) / 100 = 1 000 jetons
---
### 2. **Ajout d’API pour les données d’entreprises aux États-Unis et en Europe**  
> Étendre la couverture géographique pour permettre l’investissement dans des entreprises internationales.
#### Plan d’implémentation :
- Intégrer des équivalents de Checko :
  - **États-Unis** : Dun & Bradstreet, OpenCorporates
  - **Europe** : Companies House (Royaume-Uni), Business Register (UE)
- Ajouter la prise en charge des identifiants :
  - EIN (États-Unis)
  - VAT ID (UE)
- Étendre la logique de validation du statut de l’entreprise
---
### 3. **Émission de jetons dans un système blockchain propriétaire**  
> Améliorer la transparence et la sécurité des transactions.
#### Plan d’implémentation :
- Développer une blockchain légère en Python (ou intégrer une existante)
- Émettre des jetons sous forme de NFT ou de jetons ERC-20
- Utiliser des contrats intelligents pour la distribution des dividendes
- Prendre en charge les portefeuilles (MetaMask, Trust Wallet, etc.)
---
## 🧩 Marché secondaire prévu (DEX)
### 🎯 Objectif :
Créer une bourse décentralisée interne (DEX) où les utilisateurs peuvent :
- **Acheter et vendre des jetons directement**
- **Déterminer le prix par l’offre et la demande**
- **Sortir de l’investissement à tout moment**
### 📦 Fonctionnalités du DEX :
| Fonction | Description |
|--------|----------|
| Échange de jetons | Les utilisateurs peuvent échanger des jetons entre eux |
| Ordres à cours limité | Définir prix et volume |
| Ordres au marché | Achat/vente instantané au prix du marché |
| Graphiques et analyses | Visualiser la dynamique des prix |
| Staking de jetons | Protection contre la volatilité et croissance de la valeur |
| Pools de liquidité | Participer à des pools pour gagner des frais |
| Gouvernance DAO | Voter sur le développement de l’entreprise et de la plateforme |
### 💰 Monétisation du DEX :
| Type | Frais |
|-----|----------|
| Achat de jetons | 0,5–1 % |
| Revente de jetons | 0,1–0,5 % |
| Listing premium | 500–1000 $ par listing |
| Analytique | 10–50 $ par mois |
| Programme affilié | 2–5 % par parrain |
---
## 🌍 Prise en charge des API mondiales de vérification des entreprises
| Pays | Identifiant | API |
|--------|----------------|-----|
| Russie | INN            | Checko |
| États-Unis | EIN            | Dun & Bradstreet |
| UE     | VAT ID         | VIES |
| Global | Company ID     | OpenCorporates |
---
## 💸 Prise en charge multi-devises
| Devises prises en charge | Description |
|------------------------|----------|
| RUB                    | Rouble russe |
| USD                    | Dollar américain |
| EUR                    | Euro |
| USDT                   | Stablecoin (TRC20, ERC20) |
| USDC                   | Stablecoin (ERC20) |
| ETH                    | Ethereum |
| BTC                    | Bitcoin |
---
## 📅 Statut actuel et plan de lancement
### ✅ Prototype :
- Fonctionnel avec l’API Checko (entreprises russes)
- Prend en charge l’enregistrement, l’émission et l’achat de jetons
- Distribution des dividendes implémentée
- Bot Telegram entièrement fonctionnel
### 🚀 Opportunités de lancement :
- Une **version bêta** peut être lancée en **1 mois**
- La plateforme est prête pour les premières transactions
- Peut être déployée avec un groupe test d’entreprises et d’utilisateurs
---