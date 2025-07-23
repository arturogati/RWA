"""
TokenizeLocal Telegram Bot - final version with fixed token purchase
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

# Initialize logger and token
logger = Logger("TokenizeLocalBot")
TELEGRAM_BOT_TOKEN = "8184934106:AAElcn4Y28rFjvUOeg83XHxKgJzOoptpvjI"


class TelegramBotHandler:
    def __init__(self):
        self.checko_api_key = "yCEWUepinagwBCn3"
        self.user_states = {}
        self.commands_help = (
            "🔍 Available commands:\n"
            "/start - Start bot\n"
            "/register - Registration\n"
            "/login - Login\n"
            "/issue_tokens - Issue tokens\n"
            "/companies - List companies\n"
            "/buy - Buy tokens\n"
            "/balance - My balance\n"
            "/help - Help"
        )

    def get_user_state(self, user_id: int) -> Dict:
        """Returns current user state"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {"role": None, "data": {}, "help_shown": False}
        return self.user_states[user_id]

    async def show_help_once(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Shows help message once"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if not user_state["help_shown"]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.commands_help
            )
            user_state["help_shown"] = True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /start command - role selection"""
        keyboard = [
            [InlineKeyboardButton("👤 User", callback_data="role_user")],
            [InlineKeyboardButton("🏢 Company", callback_data="role_company")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Welcome to TokenizeLocal!\n"
            "Select your role:",
            reply_markup=reply_markup
        )
        await self.show_help_once(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles /help command"""
        await update.message.reply_text(self.commands_help)

    async def handle_role_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles role selection"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        user_state = self.get_user_state(user_id)
        if query.data == "role_user":
            user_state["role"] = "user"
            await query.edit_message_text("You selected user mode. Use /login to sign in or /register to create account.")
        elif query.data == "role_company":
            user_state["role"] = "company"
            await query.edit_message_text("You selected company mode. Use /issue_tokens to issue tokens")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.commands_help
        )

    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles user registration"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Please select user role first via /start")
            return
        await update.message.reply_text("Enter your name, email and password separated by spaces\nExample: John user@example.com 123456")
        user_state["awaiting_register"] = True

    async def login_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles user login"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Please select user role first via /start")
            return
        await update.message.reply_text("Enter your email and password separated by space\nExample: user@example.com 123456")
        user_state["awaiting_login"] = True

    async def issue_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Starts token issuance process"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "company":
            await update.message.reply_text("Please select company role first via /start")
            return
        await update.message.reply_text("Enter company TIN (10 or 12 digits):")
        user_state["awaiting_inn"] = True

    async def process_inn_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processes TIN input and verifies company"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        inn = update.message.text.strip()
        if not (len(inn) in (10, 12) and inn.isdigit()):
            await update.message.reply_text("❌ Invalid TIN format. Must be 10 or 12 digits.")
            user_state.pop("awaiting_inn", None)
            return
        await update.message.reply_text("🔍 Verifying company...")
        try:
            api_client = FinancialAPIClient(self.checko_api_key)
            company_info = api_client.get_company_info(inn)
            user_state["company_data"] = {
                "inn": inn,
                "name": company_info["name"],
                "status": company_info["status"]
            }
            await update.message.reply_text(
                f"✅ Company found: {company_info['name']}\n"
                f"Status: {company_info['status']}\n"
                "Now enter token amount to issue:"
            )
            user_state["awaiting_token_amount"] = True
        except Exception as e:
            await update.message.reply_text(
                f"❌ Company verification failed. Please ensure:\n"
                f"- TIN is correct\n- Company is active\n"
                f"Technical details: {str(e)}"
            )
        finally:
            user_state.pop("awaiting_inn", None)

    async def process_token_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Processes token amount input"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        amount_text = update.message.text.strip()
        try:
            amount = float(amount_text)
            company_data = user_state.get("company_data")
            if not company_data:
                raise ValueError("Company data not found")
            db = DBManager()
            db.register_or_update_business(company_data["inn"], company_data["name"])
            db.issue_tokens(company_data["inn"], amount)
            await update.message.reply_text(
                f"✅ Successfully issued {amount} tokens for {company_data['name']}!"
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid token amount: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Token issuance error: {str(e)}")
        finally:
            user_state.pop("awaiting_token_amount", None)
            user_state.pop("company_data", None)

    async def show_companies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Shows list of available companies"""
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("No companies available.")
            return
        response = "📋 Available companies:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} (TIN: {inn}) - available tokens: {amount or 0}\n"
        await update.message.reply_text(response)

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Shows user's token balance"""
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        user_tokens = db.get_user_tokens(email)
        if not user_tokens:
            await update.message.reply_text("You don't have any tokens yet.")
            return
        response = "💰 Your tokens:\n"
        for inn, name, amount in user_tokens:
            response += f"- {name}: {amount} tokens\n"
        await update.message.reply_text(response)

    async def buy_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Starts token purchase process"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("This command is for users only")
            return
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("❌ No companies available for purchase.")
            return
        response = "📋 Select company to buy tokens from:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} (Available tokens: {amount or 0})\n"
        response += "\nEnter company number and token amount separated by space\nExample: 1 10"
        await update.message.reply_text(response)
        user_state["awaiting_purchase"] = True

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles text messages"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        text = update.message.text.strip()

        try:
            if user_state.get("awaiting_register"):
                name, email, password = text.split()
                user_manager = UserManager()
                try:
                    user_manager.register_user(name, email, password)
                    await update.message.reply_text(f"✅ Registration successful! Welcome, {name}!")
                    await self.show_companies(update, context)
                except UserAlreadyExists:
                    await update.message.reply_text("❌ User with this email already exists.")
                user_state.pop("awaiting_register", None)

            elif user_state.get("awaiting_login"):
                email, password = text.split()
                user_manager = UserManager()
                if user_manager.authenticate_user(email, password):
                    await update.message.reply_text("✅ Login successful!")
                    await self.show_companies(update, context)
                else:
                    await update.message.reply_text("❌ Invalid email or password.")
                user_state.pop("awaiting_login", None)

            elif user_state.get("awaiting_inn"):
                await self.process_inn_input(update, context)

            elif user_state.get("awaiting_token_amount"):
                await self.process_token_amount(update, context)

            elif user_state.get("awaiting_purchase"):
                try:
                    # Processing notification
                    await update.message.reply_text("🔄 Processing request...")

                    # Parse input
                    parts = text.split()
                    if len(parts) != 2:
                        raise ValueError("Exactly 2 numbers required")

                    # Validate numbers
                    try:
                        company_num = int(parts[0])
                        amount = float(parts[1])
                    except ValueError:
                        raise ValueError("Company number and amount must be numbers")

                    if company_num <= 0 or amount <= 0:
                        raise ValueError("Numbers must be positive")

                    db = DBManager()
                    companies = db.get_all_issuances()

                    if company_num > len(companies):
                        raise ValueError("Company with this number doesn't exist")

                    inn, name, available, _ = companies[company_num - 1]
                    if available is None or amount > available:
                        raise ValueError(f"Not enough tokens. Available: {available or 0}")

                    email = f"{user_id}@telegram.local"
                    db.issue_tokens(inn, -amount)
                    db.add_user_tokens(email, inn, amount)

                    user_tokens = db.get_user_tokens(email)
                    current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

                    await update.message.reply_text(
                        f"✅ Successfully purchased {amount} tokens of {name}!\n"
                        f"Your current balance: {current_amount}\n"
                        f"Use /balance to view all tokens"
                    )

                except ValueError as e:
                    await update.message.reply_text(
                        f"❌ Input error: {str(e)}\n"
                        "Correct format: NUMBER AMOUNT\n"
                        "Example: 1 10\n"
                        "Please ensure:\n"
                        "- Company number exists\n"
                        "- Amount doesn't exceed available\n"
                        "- Both numbers are positive"
                    )

                except Exception as e:
                    await update.message.reply_text(f"❌ Unexpected error: {str(e)}")
                    logger.log(f"Purchase error: {str(e)}", level="ERROR")

                finally:
                    user_state.pop("awaiting_purchase", None)

        except ValueError as e:
            await update.message.reply_text(f"❌ Invalid input format: {str(e)}")
            logger.log(f"User {user_id} input error: {str(e)}", level="ERROR")

    def setup_handlers(self, application):
        """Configures command handlers"""
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
    """Starts the bot with specified token"""
    handler = TelegramBotHandler()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler.setup_handlers(application)
    logger.log("✅ Bot started")
    application.run_polling()


if __name__ == "__main__":
    run_bot()