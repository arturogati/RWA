---
# 📊 **TokenizeLocal: Technical Documentation**
## 🔍 General Description  
**TokenizeLocal** is a platform for tokenization of local businesses, enabling users to purchase digital tokens representing a share in a real business.  
Each token grants the right to **monthly dividends**, proportional to the company's revenue.
---
## 🧠 Core System Components
```
+---------------------+
|    Telegram Bot     |
| (User Interface)    |
+----------+----------+
           |
           v
+---------------------+
|  TelegramBotHandler |
| (Command handlers,  |
| states, logic)      |
+----------+----------+
           |
           v
+---------------------+
|      DBManager      |
| (CRUD operations on |
| businesses, tokens, |
| and balances)       |
+----------+----------+
           |
           v
+---------------------+
|  FinancialAPIClient |
| (Checko API /       |
| International APIs) |
+----------+----------+
           |
           v
+---------------------+
|      Database       |
| (SQLite, file-based)|
+---------------------+
```
---
## 🔄 System Workflow
### 1. **Company Registration**
```
graph TD
    A[Company] --> B[/issue_tokens]
    B --> C[Enter INN or VAT ID]
    C --> D[Format validation: 10/12 digits (INN), 8-12 characters (VAT)]
    D --> E[Proceed to company status verification]
```
### 2. **Company Verification via API**
```
graph TD
    F[/issue_tokens] --> G[FinancialAPIClient.get_company_info()]
    G --> H{Status check: "Active"}
    H -->|Yes| I[Retrieve financial statements]
    H -->|No| J[Error: company not registered]
    I --> K[Calculate maximum token issuance]
```
---
## 🛡️ Company Verification Module
### 1. **Company registers and enters its INN (or VAT ID)**  
#### Supported identifiers:
| Country | Identifier | Example |
|--------|----------------|--------|
| Russia | INN            | 5009051111 |
| USA    | EIN            | 123456789 |
| EU     | VAT ID         | DE276452187 |
#### Format validation:
```python
if not (len(inn) in (10, 12) and inn.isdigit()):
    raise ValueError("❌ Invalid INN format. Must be 10 or 12 digits.")
```
### 2. **API verifies company status and financial statements**  
#### APIs used:
| Region | API              | Function |
|--------|------------------|---------|
| Russia | Checko API       | `get_company_info()` |
| EU     | VIES             | VAT ID validation |
| USA    | Dun & Bradstreet | EIN and status verification |
| Global | OpenCorporates   | Public company data |
#### Operational logic:
```python
def get_company_info(self, inn: str):
    """
    Retrieves company information via Checko API.
    Validates status and financial statements.
    """
    response = requests.get(f"{self.BASE_URL}?inn={inn}&key={self.api_key}")
    data = response.json()
    if data["meta"]["status"] != "ok":
        raise Exception(data["meta"]["message"])
    company = data.get("company", {})
    if company.get("Status") != "Active":
        raise ValueError(f"Company is not registered or inactive. Status: {company.get('Status')}")
    return {
        "name": company.get("Full Name", "Unknown name"),
        "short_name": company.get("Short Name", "Unknown abbreviation"),
        "status": company.get("Status", "Unknown status"),
        "revenue": company.get("Revenue", 0)
    }
```
### 3. **Token Issuance**
#### Revenue-based cap:
```python
max_tokens = revenue * 0.1 / token_price
```
> Example:  
Revenue: 1,000,000 RUB  
Token price: 100 RUB  
Maximum tokens: 1,000 units.
#### Method:
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
## 🔄 System Workflow
### 1. **Company Registration**
```
graph TD
    L[/issue_tokens] --> M[Enter INN]
    M --> N[Format validation]
    N --> O[FinancialAPIClient.get_company_info()]
    O --> P[Retrieve status and revenue data]
    P --> Q[DBManager.register_or_update_business()]
    Q --> R[Enter token amount]
    R --> S[DBManager.issue_tokens()]
    S --> T[Company added to marketplace]
```
### 2. **User Token Purchase**
```
graph TD
    U[/buy] --> V[Select company from list]
    V --> W[Enter number and amount]
    W --> X[Validate token availability]
    X --> Y[DBManager.issue_tokens(inn, -amount)]
    Y --> Z[DBManager.add_user_tokens(email, inn, amount)]
    Z --> AA[Purchase confirmation notification]
```
---
## 🛠️ Technical Implementation
### 1. **Database (SQLite)**  
#### Tables:
| Table | Description |
|--------|----------|
| `businesses` | INN, company name |
| `token_issuances` | Issued tokens, issuance date |
| `users` | Email, name, password |
| `user_tokens` | User token balances |
| `dividend_history` | Dividend payment history |
#### Example SQL:
```sql
-- View all companies with tokens
SELECT b.name, t.amount, t.issued_at
FROM businesses b
JOIN token_issuances t ON b.inn = t.business_inn;
```
---
### 2. **Checko API**
#### Request:
```python
api_client = FinancialAPIClient(api_key="your_api_key")
company_info = api_client.get_company_info("5009051111")  # INN of OOO Shokoladnitsa
```
#### Response:
```json
{
  "name": "OOO Shokoladnitsa",
  "status": "Active",
  "inn": "5009051111",
  "ogrn": "1027700123456",
  "address": "Moscow, Myasnitskaya St., 1"
}
```
---
### 3. **DBManager**
#### Key Methods:
- `register_or_update_business()` → adds or updates a company.
- `issue_tokens()` → issues or withdraws tokens.
- `add_user_tokens()` → increases user balance.
- `distribute_dividends()` → distributes dividends.
- `get_token_stats()` → retrieves token information.
- `get_all_issuances()` → returns all companies.
---
### 4. **Telegram Bot**
#### Features:
- User registration / authentication
- Token issuance
- Token purchase
- Dividend distribution
- Balance viewing
- Input format support
- Event logging
---
## ✅ Technical Acceptance Criteria (TAC)
| № | Criterion | Completion Indicator |
|---|---------|--------------------|
| 1 | Company registration | ✔️ Ability to register via INN / VAT ID |
| 2 | Company verification via API | ✔️ Successful request and status retrieval |
| 3 | Revenue-based token cap | ✔️ Cap implemented |
| 4 | Company token issuance | ✔️ Tokens recorded in DB |
| 5 | Balance update after purchase | ✔️ `user_tokens` table updated |
| 6 | Token history viewing | ✔️ `/balance` command works correctly |
| 7 | Input format support | ✔️ Correct number and format handling |
| 8 | Data storage | ✔️ All data saved in SQLite |
| 9 | Telegram integration | ✔️ Bot starts and responds to commands |
| 10 | Event logging | ✔️ All actions logged |
---
## 📈 Scaling Roadmap
| Direction | Implementation |
|------------|-------------|
| REST API | FastAPI / Flask |
| GUI Interface | Streamlit / Tkinter |
| DAO Governance | Snapshot / voting in DB |
| Secondary Token Market | Resale between users |
| Blockchain Integration | web3.py + smart contracts |
| Oracles | Pyth Network / Chainlink |
| USDT / USDC Support | For dividend stability |
| Automated Dividend Issuance | via cron or Airflow |
| Password Hashing | bcrypt / hashlib |
| Transaction History | `dividend_history` table |
---
## 📦 Planned Features
### 1. **Token cap based on company revenue**  
> Introduce a limit on the maximum number of tokens a company can issue, based on its revenue and business valuation.
#### How it will work:
- During token issuance, the following will be calculated:
  - Monthly revenue
  - Capitalization coefficient
- Maximum tokens = (Revenue × Coefficient) / Price per token
#### Example:
- Revenue: 1,000,000 RUB
- Coefficient: 0.1
- Token price: 100 RUB
- Max tokens = (1,000,000 × 0.1) / 100 = 1,000 tokens
---
### 2. **Add API for company data from USA and Europe**  
> Expand geographical coverage to enable investment in international businesses.
#### Implementation plan:
- Integrate with Checko equivalents:
  - **USA**: Dun & Bradstreet, OpenCorporates
  - **Europe**: Companies House (UK), Business Register (EU)
- Add support for identifiers:
  - EIN (USA)
  - VAT ID (EU)
- Extend company status validation logic
---
### 3. **Token issuance within a proprietary blockchain system**  
> Enhance transaction transparency and security.
#### Implementation plan:
- Develop a lightweight blockchain in Python (or integrate with existing)
- Issue tokens as NFTs or ERC-20 tokens
- Use smart contracts for dividend distribution
- Support wallets (MetaMask, Trust Wallet, etc.)
---
## 🧩 Planned Secondary Market (DEX)
### 🎯 Objective:
Create an internal decentralized exchange (DEX) where users can:
- **Buy and sell tokens directly**
- **Determine price through supply and demand**
- **Exit investments at any time**
### 📦 DEX Features:
| Feature | Description |
|--------|----------|
| Token trading | Users can trade tokens peer-to-peer |
| Limit orders | Set price and volume |
| Market orders | Instant buy/sell at market price |
| Charts and analytics | View price dynamics |
| Token staking | Protection against volatility and value growth |
| Liquidity pools | Participate in pools to earn fees |
| DAO governance | Vote on business and platform development |
### 💰 DEX Monetization:
| Type | Fee |
|-----|----------|
| Token purchase | 0.5–1% |
| Token resale | 0.1–0.5% |
| Premium listing | $500–$1000 per listing |
| Analytics | $10–$50 monthly |
| Affiliate program | 2–5% per referral |
---
## 🌍 Support for Global Business Verification APIs
| Country | Identifier | API |
|--------|----------------|-----|
| Russia | INN            | Checko |
| USA    | EIN            | Dun & Bradstreet |
| EU     | VAT ID         | VIES |
| Global | Company ID     | OpenCorporates |
---
## 💸 Multi-Currency Support
| Supported Currencies | Description |
|------------------------|----------|
| RUB                    | Russian Ruble |
| USD                    | US Dollar |
| EUR                    | Euro |
| USDT                   | Stablecoin (TRC20, ERC20) |
| USDC                   | Stablecoin (ERC20) |
| ETH                    | Ethereum |
| BTC                    | Bitcoin |
---
## 📅 Current Status and Launch Plan

### ✅ Prototype:
- Operational with Checko API (Russian companies)
- Supports registration, token issuance, and purchase
- Dividend distribution implemented
- Fully functional Telegram bot

### 🚀 Launch Opportunities:
- **Beta version** can be launched within **1 month**
- Platform ready for initial transactions
- Can be deployed with a test group of companies and users
---