"""
TokenizeLocal Telegram Bot - финальная версия с исправленной покупкой токенов
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
from blockchain.users import UserManager, UserAlreadyExists
from verification.api_client import FinancialAPIClient
from utils.logger import Logger

# Инициализация логгера и токена
logger = Logger("TokenizeLocalBot")
TELEGRAM_BOT_TOKEN = "8184934106:AAElcn4Y28rFjvUOeg83XHxKgJzOoptpvjI"


class TelegramBotHandler:
    def __init__(self):
        self.checko_api_key = "yCEWUepinagwBCn3"
        self.user_states = {}
        self.commands_help = (
            "🔍 Доступные команды:\n"
            "/start - Начало работы\n"
            "/register - Регистрация\n"
            "/login - Вход\n"
            "/issue_tokens - Выпуск токенов\n"
            "/companies - Список компаний\n"
            "/buy - Покупка токенов\n"
            "/balance - Мой баланс\n"
            "/help - Помощь"
        )

    def get_user_state(self, user_id: int) -> Dict:
        """Возвращает текущее состояние пользователя"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {"role": None, "data": {}, "help_shown": False}
        return self.user_states[user_id]

    async def show_help_once(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показывает подсказку один раз"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if not user_state["help_shown"]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.commands_help
            )
            user_state["help_shown"] = True

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
        await self.show_help_once(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик команды /help"""
        await update.message.reply_text(self.commands_help)

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
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.commands_help
        )

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
        if not (len(inn) in (10, 12) and inn.isdigit()):
            await update.message.reply_text("❌ Неверный формат ИНН. Должно быть 10 или 12 цифр.")
            user_state.pop("awaiting_inn", None)
            return
        await update.message.reply_text("🔍 Проверяем компанию...")
        try:
            api_client = FinancialAPIClient(self.checko_api_key)
            company_info = api_client.get_company_info(inn)
            user_state["company_data"] = {
                "inn": inn,
                "name": company_info["name"],
                "status": company_info["status"]
            }
            await update.message.reply_text(
                f"✅ Компания найдена: {company_info['name']}\n"
                f"Статус: {company_info['status']}\n"
                "Теперь введите количество токенов для выпуска:"
            )
            user_state["awaiting_token_amount"] = True
        except Exception as e:
            await update.message.reply_text(
                f"❌ Ошибка проверки компании. Убедитесь что:\n"
                f"- ИНН корректен\n- Компания действующая\n"
                f"Техническая информация: {str(e)}"
            )
        finally:
            user_state.pop("awaiting_inn", None)

    async def process_token_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка ввода количества токенов"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        amount_text = update.message.text.strip()
        try:
            amount = float(amount_text)
            company_data = user_state.get("company_data")
            if not company_data:
                raise ValueError("Данные компании не найдены")
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
            response += f"{idx+1}. {name} (ИНН: {inn}) - доступно токенов: {amount or 0}\n"
        await update.message.reply_text(response)

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показать баланс токенов пользователя"""
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        user_tokens = db.get_user_tokens(email)
        if not user_tokens:
            await update.message.reply_text("У вас пока нет токенов.")
            return
        response = "💰 Ваши токены:\n"
        for inn, name, amount in user_tokens:
            response += f"- {name}: {amount} токенов\n"
        await update.message.reply_text(response)

    async def buy_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало процесса покупки токенов"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Эта команда только для пользователей")
            return
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("❌ Нет доступных компаний для покупки.")
            return
        response = "📋 Выберите компанию для покупки токенов:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} (Доступно токенов: {amount or 0})\n"
        response += "\nВведите номер компании и количество токенов через пробел\nПример: 1 10"
        await update.message.reply_text(response)
        user_state["awaiting_purchase"] = True

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка текстовых сообщений"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        text = update.message.text.strip()

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
                try:
                    # Сообщение о начале обработки
                    await update.message.reply_text("🔄 Обработка запроса...")

                    # Разделение ввода
                    parts = text.split()
                    if len(parts) != 2:
                        raise ValueError("Нужно ввести ровно 2 числа")

                    # Проверка, что ввод состоит из чисел
                    try:
                        company_num = int(parts[0])
                        amount = float(parts[1])
                    except ValueError:
                        raise ValueError("Номер компании и количество должны быть числами")

                    if company_num <= 0 or amount <= 0:
                        raise ValueError("Числа должны быть положительными")

                    db = DBManager()
                    companies = db.get_all_issuances()

                    if company_num > len(companies):
                        raise ValueError("Компании с таким номером не существует")

                    inn, name, available, _ = companies[company_num - 1]
                    if available is None or amount > available:
                        raise ValueError(f"Недостаточно токенов. Доступно: {available or 0}")

                    email = f"{user_id}@telegram.local"
                    db.issue_tokens(inn, -amount)
                    db.add_user_tokens(email, inn, amount)

                    user_tokens = db.get_user_tokens(email)
                    current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

                    await update.message.reply_text(
                        f"✅ Успешно куплено {amount} токенов компании {name}!\n"
                        f"Ваш текущий баланс: {current_amount}\n"
                        f"Используйте /balance для просмотра всех токенов"
                    )

                except ValueError as e:
                    await update.message.reply_text(
                        f"❌ Ошибка ввода: {str(e)}\n"
                        "Правильный формат: НОМЕР КОЛИЧЕСТВО\n"
                        "Пример: 1 10\n"
                        "Убедитесь, что:\n"
                        "- Номер компании существует\n"
                        "- Количество не превышает доступное\n"
                        "- Оба числа положительные"
                    )

                except Exception as e:
                    await update.message.reply_text(f"❌ Неожиданная ошибка: {str(e)}")
                    logger.log(f"Purchase error: {str(e)}", level="ERROR")

                finally:
                    user_state.pop("awaiting_purchase", None)

        except ValueError as e:
            await update.message.reply_text(f"❌ Неверный формат ввода: {str(e)}")
            logger.log(f"User {user_id} input error: {str(e)}", level="ERROR")

    def setup_handlers(self, application):
        """Настройка обработчиков команд"""
        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(CommandHandler("help", self.help_command))
        application.add_handler(CallbackQueryHandler(self.handle_role_selection))
        application.add_handler(CommandHandler("register", self.register_user))
        application.add_handler(CommandHandler("login", self.login_user))
        application.add_handler(CommandHandler("issue_tokens", self.issue_tokens))
        application.add_handler(CommandHandler("companies", self.show_companies))
        application.add_handler(CommandHandler("buy", self.buy_tokens))
        application.add_handler(CommandHandler("balance", self.show_balance))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))


def run_bot():
    """Запуск бота с указанным токеном"""
    handler = TelegramBotHandler()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler.setup_handlers(application)
    logger.log("✅ Бот запущен")
    application.run_polling()


if __name__ == "__main__":
    run_bot()