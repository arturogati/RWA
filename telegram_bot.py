"""
Ответственность:
Telegram-бот с полным функционалом TokenizeLocal (аналог main.py)
"""

import os
from typing import Optional, Dict
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
from blockchain.users import UserManager, UserAlreadyExists
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Инициализация логгера и токена
logger = Logger("TokenizeLocalBot")
TELEGRAM_BOT_TOKEN = "8184934106:AAElcn4Y28rFjvUOeg83XHxKgJzOoptpvjI"  # Ваш токен

class TelegramBotHandler:
    def __init__(self):
        self.checko_api_key = "yCEWUepinagwBCn3"
        self.user_states = {}  # Хранение состояний пользователей

    def get_user_state(self, user_id: int) -> Dict:
        """Возвращает текущее состояние пользователя"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {"role": None, "data": {}}
        return self.user_states[user_id]

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start - выбор роли"""
        keyboard = [
            [InlineKeyboardButton("👤 Пользователь", callback_data="role_user")],
            [InlineKeyboardButton("🏢 Компания", callback_data="role_company")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Добро пожаловать в TokenizeLocal!\n"
            "Выберите вашу роль:",
            reply_markup=reply_markup
        )

    async def handle_role_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка выбора роли"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        user_state = self.get_user_state(user_id)
        
        if query.data == "role_user":
            user_state["role"] = "user"
            await query.edit_message_text("Вы выбрали режим пользователя. Используйте /login для входа или /register для регистрации.")
        elif query.data == "role_company":
            user_state["role"] = "company"
            await query.edit_message_text("Вы выбрали режим компании. Для выпуска токенов используйте /issue_tokens")

    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Регистрация нового пользователя"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        
        if user_state["role"] != "user":
            await update.message.reply_text("Пожалуйста, сначала выберите роль пользователя через /start")
            return

        await update.message.reply_text("Введите ваше имя, email и пароль через пробел\nПример: Иван user@example.com 123456")
        user_state["awaiting_register"] = True

    async def login_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Авторизация пользователя"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        
        if user_state["role"] != "user":
            await update.message.reply_text("Пожалуйста, сначала выберите роль пользователя через /start")
            return

        await update.message.reply_text("Введите ваш email и пароль через пробел\nПример: user@example.com 123456")
        user_state["awaiting_login"] = True

    async def issue_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса выпуска токенов"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        
        if user_state["role"] != "company":
            await update.message.reply_text("Пожалуйста, сначала выберите роль компании через /start")
            return

        await update.message.reply_text("Введите ИНН компании (10 или 12 цифр):")
        user_state["awaiting_inn"] = True

    async def process_inn_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода ИНН и проверка компании"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        inn = update.message.text.strip()
        
        # Проверка формата ИНН
        if not (len(inn) in (10, 12) and inn.isdigit()):
            await update.message.reply_text("❌ Неверный формат ИНН. Должно быть 10 или 12 цифр.")
            user_state.pop("awaiting_inn", None)
            return

        # Проверка компании через API
        api_client = FinancialAPIClient(self.checko_api_key)
        try:
            company_info = api_client.get_company_info(inn)
            user_state["company_data"] = {
                "inn": inn,
                "name": company_info["name"],
                "status": company_info["status"]
            }
            
            await update.message.reply_text(
                f"✅ Компания найдена: {company_info['name']}\n"
                f"Статус: {company_info['status']}\n\n"
                "Теперь введите количество токенов для выпуска:"
            )
            user_state["awaiting_token_amount"] = True
            user_state.pop("awaiting_inn", None)
            
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка проверки компании: {str(e)}")
            user_state.pop("awaiting_inn", None)

    async def process_token_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода количества токенов"""
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
                
            # Регистрация компании и выпуск токенов
            db = DBManager()
            db.register_or_update_business(company_data["inn"], company_data["name"])
            db.issue_tokens(company_data["inn"], amount)
            
            await update.message.reply_text(
                f"✅ Успешно выпущено {amount} токенов для компании {company_data['name']}!"
            )
            
        except ValueError as e:
            await update.message.reply_text(f"❌ Неверное количество токенов: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Ошибка выпуска токенов: {str(e)}")
        finally:
            user_state.pop("awaiting_token_amount", None)
            user_state.pop("company_data", None)

    async def show_companies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать список компаний"""
        db = DBManager()
        companies = db.get_all_issuances()
        
        if not companies:
            await update.message.reply_text("Нет доступных компаний.")
            return

        response = "📋 Доступные компании:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} (ИНН: {inn}) - токенов: {amount or 0}\n"
        
        await update.message.reply_text(response)

    async def buy_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Покупка токенов"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        
        if user_state["role"] != "user":
            await update.message.reply_text("Эта команда только для пользователей")
            return

        await update.message.reply_text("Введите номер компании и количество токенов через пробел\nПример: 1 100")
        user_state["awaiting_purchase"] = True

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        text = update.message.text
        
        try:
            if user_state.get("awaiting_register"):
                name, email, password = text.split()
                user_manager = UserManager()
                
                try:
                    user_manager.register_user(name, email, password)
                    await update.message.reply_text(f"✅ Регистрация успешна! Добро пожаловать, {name}!")
                    await self.show_companies(update, context)
                except UserAlreadyExists:
                    await update.message.reply_text("❌ Пользователь с таким email уже существует.")
                
                user_state.pop("awaiting_register", None)

            elif user_state.get("awaiting_login"):
                email, password = text.split()
                user_manager = UserManager()
                
                if user_manager.authenticate_user(email, password):
                    await update.message.reply_text("✅ Вход выполнен успешно!")
                    await self.show_companies(update, context)
                else:
                    await update.message.reply_text("❌ Неверный email или пароль.")
                
                user_state.pop("awaiting_login", None)

            elif user_state.get("awaiting_inn"):
                await self.process_inn_input(update, context)

            elif user_state.get("awaiting_token_amount"):
                await self.process_token_amount(update, context)

            elif user_state.get("awaiting_purchase"):
                company_num, amount = map(float, text.split())
                db = DBManager()
                companies = db.get_all_issuances()
                
                if not (1 <= company_num <= len(companies)):
                    await update.message.reply_text("❌ Неверный номер компании")
                    return
                
                inn = companies[int(company_num)-1][0]
                email = f"{user_id}@telegram.local"  # Генерация email на основе Telegram ID
                
                try:
                    # Уменьшаем общий пул и добавляем пользователю
                    db.issue_tokens(inn, -amount)
                    db.add_user_tokens(email, inn, amount)
                    await update.message.reply_text(f"✅ Успешно куплено {amount} токенов!")
                except Exception as e:
                    await update.message.reply_text(f"❌ Ошибка покупки: {str(e)}")
                
                user_state.pop("awaiting_purchase", None)

        except ValueError as e:
            await update.message.reply_text(f"❌ Неверный формат ввода: {str(e)}")
            logger.log(f"User {user_id} input error: {str(e)}", level="ERROR")

    def setup_handlers(self, application):
        """Настройка обработчиков команд"""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CallbackQueryHandler(self.handle_role_selection))
        application.add_handler(CommandHandler("register", self.register_user))
        application.add_handler(CommandHandler("login", self.login_user))
        application.add_handler(CommandHandler("issue_tokens", self.issue_tokens))
        application.add_handler(CommandHandler("companies", self.show_companies))
        application.add_handler(CommandHandler("buy", self.buy_tokens))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

def run_bot():
    """Запуск бота с указанным токеном"""
    handler = TelegramBotHandler()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler.setup_handlers(application)
    
    logger.log("✅ Бот запущен с токеном: " + TELEGRAM_BOT_TOKEN[:4] + "..." + TELEGRAM_BOT_TOKEN[-4:])
    application.run_polling()

if __name__ == "__main__":
    run_bot()