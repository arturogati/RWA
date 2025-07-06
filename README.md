

# 🛠️ **TokenizeLocal: Техническая архитектура токенизации бизнеса**

## 1. Общая структура проекта

```
tokenize_local/
│
├── main.py                      # Основной скрипт с логикой выбора роли и обработки данных
├── .env                         # Хранение API-ключа Checko
│
├── blockchain/
│   ├── db_manager.py            # Работа с бизнесами, токенами и балансом пользователей
│   ├── register_user.py         # Регистрация новых пользователей
│   └── records_check.py         # Проверка содержимого БД
│
├── verification/
│   └── api_client.py           # Клиент для проверки компаний через Checko API
│
└── utils/
    └── logger.py               # Логирование событий
```

---

## 2. Схема работы системы

```
[ИНН] → [Проверка через Checko API] → [Выпуск токенов в БД]
     ↓
[Пользователь] → [Авторизация / регистрация] → [Выбор компании из списка]
     ↓
[Инвестор покупает токены] → [Токены записываются в user_tokens]
     ↓
[Бизнес обновляет выручку] → [Расчёт дивидендного пула] → [Выплата дивидендов по токенам]
     ↓
[Все данные сохраняются в SQLite] → [Можно просматривать через records_check.py]
```

---

## 3. Техническая реализация

### 3.1. **Система БД (SQLite)**
Все данные хранятся в `blockchain/database.sqlite`.  
Создаются при первом запуске через метод `_initialize_tables()`.

#### Таблицы:
| Название | Поля |
|----------|------|
| `businesses` | `inn TEXT PRIMARY KEY`, `name TEXT NOT NULL` |
| `token_issuances` | `business_inn TEXT PRIMARY KEY`, `amount REAL`, `issued_at DATETIME` |
| `users` | `id INTEGER PRIMARY KEY`, `name TEXT`, `email TEXT UNIQUE`, `password TEXT` |
| `user_tokens` | `id INTEGER PRIMARY KEY`, `email TEXT`, `business_inn TEXT`, `tokens REAL DEFAULT 0` |

> ⚙️ Все таблицы связаны через внешние ключи (`FOREIGN KEY`) и поддерживают уникальные записи.

---

### 3.2. **Проверка компании через Checko API**

Класс `FinancialAPIClient` делает запрос к `/v2/finances` и проверяет:
- HTTP-статус ответа.
- Поле `"meta.status" == "ok"`
- `"company.Статус" == "Действует"`

```python
from verification.api_client import FinancialAPIClient
client = FinancialAPIClient(api_key="yCEWUepinagwBCn3")
data = client.get_company_info("5009051111")  # ИНН ООО Шоколадница
```

Если компания не найдена или не действует → выбрасывается ошибка:
```text
ValueError: Компания с ИНН 5009051111 не зарегистрирована или не действует. Статус: Ликвидирована
```

---

### 3.3. **Управление токенами через DBManager**

Основные методы:
- `register_or_update_business(inn, name)` → добавляет или обновляет компанию.
- `issue_tokens(inn, amount)` → выпускает токены, перезаписывает предыдущие значения.
- `get_token_stats(inn)` → возвращает информацию о токенах по ИНН.
- `get_all_issuances()` → вывод всех компаний с количеством токенов.
- `add_user_tokens(email, business_inn, amount)` → увеличивает баланс пользователя.
- `get_user_tokens(email)` → возвращает список токенов у пользователя.
- `distribute_dividends(business_inn, revenue, dividend_percentage)` → рассчитывает и распределяет дивиденды между всеми владельцами токенов.

---

### 3.4. **Регистрация и авторизация пользователей**

Через класс `UserManager`:

- Регистрация:
  ```python
  from blockchain.users import UserManager
  user_manager = UserManager()
  user_manager.register_user(name="Alice", email="alice@example.com", password="pass123")
  ```

- Авторизация:
  ```python
  if user_manager.authenticate_user("alice@example.com", "pass123"):
      print("✅ Авторизация успешна")
  ```

> 🔐 Пароли пока хранятся в открытом виде. В будущем можно добавить хэширование через `bcrypt`.

---

### 3.5. **Логика покупки токенов**

После авторизации пользователь видит список компаний и может выбрать количество токенов.

Пример:
```bash
1. ООО Шоколадница (ИНН: 5009051111) — доступно токенов: 10000.0
2. ООО Кофемания (ИНН: 7701234567) — доступно токенов: 5000.0

Выберите номер компании: 1
Сколько токенов хотите купить (доступно: 10000)? 2000
```

#### Что происходит в БД:
- Выполняется `issue_tokens` с отрицательным значением: `db.issue_tokens(inn=selected["inn"], amount=-buy_amount)`
- Зачисляются токены пользователю: `db.add_user_tokens(email=email, business_inn=selected["inn"], amount=buy_amount)`

---

### 3.6. **Автоматическое распределение дивидендов**

Метод `distribute_dividends` рассчитывает выплаты на основе:
- Выручки бизнеса.
- Процента выручки, который направляется на дивиденды (например, 10%).
- Общего числа токенов.
- Количества токенов у каждого пользователя.

#### Пример:
```python
db.distribute_dividends(business_inn="5009051111", revenue=10000, dividend_percentage=0.1)
```

👉 Общий пул дивидендов: $1000  
👉 Пользователь с 2000 токенов получает:  
**$1000 × (2000 / 10000) = $200**

---

## 4. Механизм начисления дивидендов

### Формулы:
$$ \text{Дивидендный пул} = \text{Выручка} \times \text{Процент дивидендов} $$  
$$ \text{Дивиденд на токен} = \frac{\text{Дивидендный пул}}{\text{Общее число токенов}} $$  
$$ \text{Дивиденд пользователю} = \text{Дивиденд на токен} \times \text{токенов у пользователя} $$

---

## 5. Структура базы данных

```sql
-- Таблицы:
CREATE TABLE businesses (
    inn TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE token_issuances (
    business_inn TEXT PRIMARY KEY,
    amount REAL NOT NULL,
    issued_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (business_inn) REFERENCES businesses (inn)
);

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE user_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    business_inn TEXT NOT NULL,
    tokens REAL DEFAULT 0,
    UNIQUE(email, business_inn),
    FOREIGN KEY(business_inn) REFERENCES businesses (inn)
);

CREATE TABLE dividend_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    business_inn TEXT NOT NULL,
    amount REAL NOT NULL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. Сценарий взаимодействия с системой

### 6.1. Инвестор:
1. Выбирает роль: `user`.
2. Вводит email и пароль.
3. Видит список компаний и количество доступных токенов.
4. Выбирает компанию и покупает нужное число токенов.
5. Получает ежемесячные дивиденды пропорционально своей доле.

### 6.2. Компания:
1. Выбирает роль: `company`.
2. Вводит ИНН и проверяет статус через Checko.
3. Указывает количество токенов и выпускает их.
4. Ежемесячно обновляет данные о выручке.
5. Вызывает `distribute_dividends(...)` для автоматической выплаты инвесторам.

---

## 7. Как работает система внутри

### 7.1. Поток данных

```
main.py
│
├── Проверка роли: user / company
│
├── Если role == 'user':
│   ├── Авторизация через UserManager
│   ├── Список компаний из get_all_issuances()
│   ├── Покупка токенов через add_user_tokens()
│   └── Отображение текущих токенов через get_user_tokens()
│
├── Если role == 'company':
│   ├── Проверка через Checko API
│   ├── Выпуск токенов через issue_tokens()
│   └── Распределение дивидендов через distribute_dividends()
│
└── Все данные сохраняются в database.sqlite
```

---

## 8. Пример вызова дивидендов

```python
def run_full_demo():
    ...
    db.issue_tokens(inn=selected["inn"], amount=tokens)  # Выпуск токенов
    ...
    revenue_input = input("Введите месячную выручку бизнеса: ").strip()
    try:
        revenue = float(revenue_input)
        db.distribute_dividends(business_inn=selected["inn"], revenue=revenue)
    except ValueError:
        logger.log("[ERROR] Неверная выручка.", level="ERROR")
```

---

## 9. Как проверить состояние системы

Запустите `records_check.py`:

```bash
python blockchain/records_check.py
```

Он покажет:
- Какие таблицы есть.
- Содержимое каждой.
- Сколько токенов у кого.

---

## 10. Технологии и зависимости

| Технология | Назначение |
|------------|-------------|
| Python | Основной язык |
| SQLite | Централизованное хранение данных |
| requests | Взаимодействие с Checko API |
| logging | Логирование операций |
| python-dotenv | Для хранения API-ключа |
| sqlite3 | Подключение к БД |

---

## 11. Возможности масштабирования

| Возможность | Реализация |
|-------------|-------------|
| REST API | FastAPI / Flask |
| GUI интерфейс | Streamlit / Tkinter |
| DAO управление | Snapshot / голосование в БД |
| Вторичный рынок токенов | Перепродажа между пользователями |
| Интеграция с блокчейном | web3.py + смарт-контракты |
| Оракулы | Pyth Network / Chainlink |
| Поддержка USDT / USDC | Для стабильности дивидендов |
| Автоматический выпуск дивидендов | Через cron или Airflow |
| Хэширование паролей | bcrypt / hashlib |
| История операций | Таблица `dividend_history` |

---

## 12. Как всё взаимодействует между собой

```
+------------------+       +-------------------+
|                  |       |                   |
|  main.py         |<-----> verification/     |
| (точка входа)    |       | api_client.py     |
|                  |       | (Checko API)       |
+--------+---------+       +-------------------+
         |
         v
+--------+---------+       +------------------+
|                   |       |                  |
|  blockchain/      |<-----> db_manager.py   |
|  users.py         |       | (CRUD бизнесов,   |
| (UserManager)     |       | токенов, дивидендов) |
+-------------------+       +------------------+

         |
         v
+--------+---------+
|                   |
|  utils/logger.py  |
| (логирование)     |
+-------------------+
```

---

## 13. Примеры SQL-запросов

### Просмотр всех компаний:
```sql
SELECT b.inn, b.name, t.amount, t.issued_at
FROM businesses b
LEFT JOIN token_issuances t ON b.inn = t.business_inn;
```

### Просмотр токенов пользователя:
```sql
SELECT ut.business_inn, b.name, ut.tokens
FROM user_tokens ut
JOIN businesses b ON ut.business_inn = b.inn
WHERE ut.email = 'alice@example.com';
```

### Расчёт дивидендов:
```sql
SELECT email, tokens FROM user_tokens WHERE business_inn = '5009051111';
```

---
