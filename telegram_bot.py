"""
TokenizeLocal Telegram Bot — финальная версия с дивидендами
"""

import os
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from blockchain.db_manager import DBManager
from blockchain.users import UserManager, UserAlreadyExists, InvalidEmail
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

logger = Logger("TokenizeLocalBot")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8184934106:AAElcn4Y28rFjvUOeg83XHxKgJzOoptpvjI")
CHECKO_API_KEY = os.getenv("CHECKO_API_KEY", "yCEWUepinagwBCn3")

class TelegramBotHandler:
    def __init__(self):
        self.checko_api_key = CHECKO_API_KEY
        self.user_states = {}
        self.commands_help = (
            "🔍 Доступные команды:\n"
            "/start - Начало\n"
            "/register - Регистрация\n"
            "/login - Вход\n"
            "/issue_tokens - Выпуск токенов\n"
            "/companies - Список компаний\n"
            "/buy - Покупка токенов\n"
            "/balance - Мой баланс\n"
            "/dividends - Мои выплаты\n"
            "/help - Помощь"
        )

    def get_user_state(self, user_id: int) -> Dict:
        if user_id not in self.user_states:
            self.user_states[user_id] = {"role": None, "data": {}, "help_shown": False}
        return self.user_states[user_id]

    async def show_help_once(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if not user_state["help_shown"]:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=self.commands_help)
            user_state["help_shown"] = True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [[InlineKeyboardButton("👤 Пользователь", callback_data="role_user")],
                    [InlineKeyboardButton("🏢 Компания", callback_data="role_company")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("Добро пожаловать!\nВыберите роль:", reply_markup=reply_markup)
        await self.show_help_once(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.commands_help)

    async def handle_role_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        user_state = self.get_user_state(user_id)
        if query.data == "role_user":
            user_state["role"] = "user"
            await query.edit_message_text("Вы выбрали режим пользователя.")
        elif query.data == "role_company":
            user_state["role"] = "company"
            await query.edit_message_text("Вы выбрали режим компании.")
        await context.bot.send_message(chat_id=update.effective_chat.id, text=self.commands_help)

    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Выберите роль пользователя через /start")
            return
        await update.message.reply_text("Введите имя, email и пароль через пробел\nПример: Иван user@example.com 1234")
        user_state["awaiting_register"] = True

    async def login_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Выберите роль пользователя через /start")
            return
        await update.message.reply_text("Введите email и пароль через пробел")
        user_state["awaiting_login"] = True

    async def issue_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "company":
            await update.message.reply_text("Выберите роль компании через /start")
            return
        await update.message.reply_text("Введите ИНН компании (10 или 12 цифр):")
        user_state["awaiting_inn"] = True

    async def process_inn_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        inn = update.message.text.strip()
        if not (len(inn) in (10, 12) and inn.isdigit()):
            await update.message.reply_text("❌ Неверный формат ИНН.")
            user_state.pop("awaiting_inn", None)
            return
        try:
            api_client = FinancialAPIClient(self.checko_api_key)
            company_info = api_client.get_company_info(inn)
            if company_info.get("status") != "Действует":
                await update.message.reply_text(f"❌ Компания не действует: {company_info['status']}")
                return
            user_state["company_data"] = {"inn": inn, "name": company_info["name"]}
            await update.message.reply_text(f"✅ {company_info['name']}\nТеперь введите количество токенов:")
            user_state["awaiting_token_amount"] = True
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        finally:
            user_state.pop("awaiting_inn", None)

    async def process_token_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        amount_text = update.message.text.strip()
        try:
            amount = float(amount_text)
            if amount <= 0:
                raise ValueError("Количество должно быть положительным")
            company_data = user_state.get("company_data")
            if not company_data:
                raise ValueError("Данные компании не найдены")
            db = DBManager()
            db.register_or_update_business(company_data["inn"], company_data["name"])
            db.issue_tokens(company_data["inn"], amount)
            await update.message.reply_text(f"✅ Выпущено {amount} токенов для {company_data['name']}!")
        except ValueError as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        finally:
            user_state.pop("awaiting_token_amount", None)
            user_state.pop("company_data", None)

    async def show_companies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("Нет компаний.")
            return
        response = "📋 Доступные компании:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} — {amount or 0} токенов\n"
        await update.message.reply_text(response)

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        user_tokens = db.get_user_tokens(email)
        if not user_tokens:
            await update.message.reply_text("У вас нет токенов.")
            return
        response = "💰 Ваш баланс:\n"
        for inn, name, amount in user_tokens:
            response += f"- {name}: {amount} токенов\n"
        await update.message.reply_text(response)

    async def buy_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Только для пользователей")
            return
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("Нет компаний.")
            return
        response = "Выберите компанию:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} ({amount or 0})\n"
        response += "\nВведите: НОМЕР КОЛИЧЕСТВО\nПример: 1 10"
        await update.message.reply_text(response)
        user_state["awaiting_purchase"] = True

    async def handle_purchase(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, text: str):
        user_state = self.get_user_state(user_id)
        try:
            parts = text.split()
            if len(parts) != 2:
                raise ValueError("Введите два числа")
            company_num = int(parts[0]); amount = float(parts[1])
            if company_num <= 0 or amount <= 0:
                raise ValueError("Числа должны быть положительными")
            db = DBManager()
            companies = db.get_all_issuances()
            if company_num > len(companies):
                raise ValueError("Нет такой компании")
            inn, name, available, _ = companies[company_num - 1]
            if available is None or amount > available:
                raise ValueError(f"Недостаточно токенов. Доступно: {available or 0}")
            email = f"{user_id}@telegram.local"
            db.issue_tokens(inn, -amount)
            db.add_user_tokens(email, inn, amount)
            current = next((t[2] for t in db.get_user_tokens(email) if t[0] == inn), 0)
            await update.message.reply_text(f"✅ Куплено {amount} токенов {name}!\nБаланс: {current}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
        finally:
            user_state.pop("awaiting_purchase", None)

    async def show_dividends(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        cursor = db.conn.cursor()
        cursor.execute("""
            SELECT d.business_inn, b.name, d.distribution_date, d.dividend_pool, d.token_price
            FROM dividend_history d
            JOIN businesses b ON d.business_inn = b.inn
            JOIN user_tokens u ON d.business_inn = u.business_inn
            WHERE u.email = ?
            ORDER BY d.distribution_date DESC
            LIMIT 5
        """, (email,))
        rows = cursor.fetchall()
        if not rows:
            await update.message.reply_text("У вас не было выплат.")
            return
        response = "📈 Ваши выплаты:\n\n"
        for inn, name, date, pool, price in rows:
            tokens = next((t[2] for t in db.get_user_tokens(email) if t[0] == inn), 0)
            if tokens > 0:
                dividend = (tokens / db.get_token_stats(inn).get("total_issued", 1)) * pool
                response += f"🏢 {name}\n📅 {date[:10]}\n💸 {dividend:.2f}$\n\n"
        await update.message.reply_text(response)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        text = update.message.text.strip()
        try:
            if user_state.get("awaiting_register"):
                parts = text.split()
                if len(parts) < 3:
                    await update.message.reply_text("❌ Нужно: имя email пароль")
                    return
                password = parts[-1]; email = parts[-2]; name = " ".join(parts[:-2])
                if "@" not in email:
                    await update.message.reply_text("❌ Некорректный email")
                    return
                user_manager = UserManager()
                try:
                    user_manager.register_user(name, email, password)
                    await update.message.reply_text(f"✅ Регистрация успешна, {name}!")
                    await self.show_companies(update, context)
                except UserAlreadyExists:
                    await update.message.reply_text("❌ Пользователь уже существует.")
                except InvalidEmail:
                    await update.message.reply_text("❌ Некорректный email.")
                finally:
                    user_state.pop("awaiting_register", None)
            elif user_state.get("awaiting_login"):
                parts = text.split()
                if len(parts) != 2:
                    await update.message.reply_text("❌ Введите email и пароль")
                    return
                email, password = parts
                user_manager = UserManager()
                if user_manager.authenticate_user(email, password):
                    await update.message.reply_text("✅ Вход выполнен!")
                    await self.show_companies(update, context)
                else:
                    await update.message.reply_text("❌ Неверный email или пароль.")
                user_state.pop("awaiting_login", None)
            elif user_state.get("awaiting_inn"):
                await self.process_inn_input(update, context)
            elif user_state.get("awaiting_token_amount"):
                await self.process_token_amount(update, context)
            elif user_state.get("awaiting_purchase"):
                await self.handle_purchase(update, context, user_id, text)
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")

    def setup_handlers(self, application):
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.handle_role_selection))
        application.add_handler(CommandHandler("register", self.register_user))
        application.add_handler(CommandHandler("login", self.login_user))
        application.add_handler(CommandHandler("issue_tokens", self.issue_tokens))
        application.add_handler(CommandHandler("companies", self.show_companies))
        application.add_handler(CommandHandler("buy", self.buy_tokens))
        application.add_handler(CommandHandler("balance", self.show_balance))
        application.add_handler(CommandHandler("dividends", self.show_dividends))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

def run_bot():
    handler = TelegramBotHandler()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler.setup_handlers(application)
    logger.log("✅ Бот запущен")
    application.run_polling()

if __name__ == "__main__":
    run_bot()