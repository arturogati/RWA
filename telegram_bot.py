"""
TokenizeLocal Telegram Bot - Version finale avec correction de l'achat de tokens
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

# Initialisation du logger et du token
logger = Logger("TokenizeLocalBot")
TELEGRAM_BOT_TOKEN = "8184934106:AAElcn4Y28rFjvUOeg83XHxKgJzOoptpvjI"


class TelegramBotHandler:
    def __init__(self):
        self.checko_api_key = "yCEWUepinagwBCn3"
        self.user_states = {}
        self.commands_help = (
            "🔍 Commandes disponibles:\n"
            "/start - Démarrer\n"
            "/register - S'inscrire\n"
            "/login - Se connecter\n"
            "/issue_tokens - Émettre des tokens\n"
            "/companies - Liste des entreprises\n"
            "/buy - Acheter des tokens\n"
            "/balance - Mon solde\n"
            "/help - Aide"
        )

    def get_user_state(self, user_id: int) -> Dict:
        """Retourne l'état actuel de l'utilisateur"""
        if user_id not in self.user_states:
            self.user_states[user_id] = {"role": None, "data": {}, "help_shown": False}
        return self.user_states[user_id]

    async def show_help_once(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche l'aide une seule fois"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if not user_state["help_shown"]:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self.commands_help
            )
            user_state["help_shown"] = True

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestion de la commande /start - choix du rôle"""
        keyboard = [
            [InlineKeyboardButton("👤 Utilisateur", callback_data="role_user")],
            [InlineKeyboardButton("🏢 Entreprise", callback_data="role_company")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Bienvenue sur TokenizeLocal!\n"
            "Choisissez votre rôle:",
            reply_markup=reply_markup
        )
        await self.show_help_once(update, context)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestion de la commande /help"""
        await update.message.reply_text(self.commands_help)

    async def handle_role_selection(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestion du choix de rôle"""
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        user_state = self.get_user_state(user_id)
        if query.data == "role_user":
            user_state["role"] = "user"
            await query.edit_message_text("Vous avez sélectionné le mode utilisateur. Utilisez /login pour vous connecter ou /register pour vous inscrire.")
        elif query.data == "role_company":
            user_state["role"] = "company"
            await query.edit_message_text("Vous avez sélectionné le mode entreprise. Utilisez /issue_tokens pour émettre des tokens")
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=self.commands_help
        )

    async def register_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inscription d'un nouvel utilisateur"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Veuillez d'abord sélectionner le rôle utilisateur via /start")
            return
        await update.message.reply_text("Entrez votre nom, email et mot de passe séparés par des espaces\nExemple: Jean user@example.com 123456")
        user_state["awaiting_register"] = True

    async def login_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Authentification utilisateur"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Veuillez d'abord sélectionner le rôle utilisateur via /start")
            return
        await update.message.reply_text("Entrez votre email et mot de passe séparés par un espace\nExemple: user@example.com 123456")
        user_state["awaiting_login"] = True

    async def issue_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Début du processus d'émission de tokens"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "company":
            await update.message.reply_text("Veuillez d'abord sélectionner le rôle entreprise via /start")
            return
        await update.message.reply_text("Entrez le numéro INN de l'entreprise (10 ou 12 chiffres):")
        user_state["awaiting_inn"] = True

    async def process_inn_input(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Traitement de la saisie de l'INN et vérification de l'entreprise"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        inn = update.message.text.strip()
        if not (len(inn) in (10, 12) and inn.isdigit()):
            await update.message.reply_text("❌ Format INN invalide. Doit contenir 10 ou 12 chiffres.")
            user_state.pop("awaiting_inn", None)
            return
        await update.message.reply_text("🔍 Vérification de l'entreprise...")
        try:
            api_client = FinancialAPIClient(self.checko_api_key)
            company_info = api_client.get_company_info(inn)
            user_state["company_data"] = {
                "inn": inn,
                "name": company_info["name"],
                "status": company_info["status"]
            }
            await update.message.reply_text(
                f"✅ Entreprise trouvée: {company_info['name']}\n"
                f"Statut: {company_info['status']}\n"
                "Entrez maintenant le nombre de tokens à émettre:"
            )
            user_state["awaiting_token_amount"] = True
        except Exception as e:
            await update.message.reply_text(
                f"❌ Erreur de vérification. Vérifiez que:\n"
                f"- L'INN est correct\n"
                f"- L'entreprise est active\n"
                f"Détails techniques: {str(e)}"
            )
        finally:
            user_state.pop("awaiting_inn", None)

    async def process_token_amount(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Traitement de la saisie du nombre de tokens"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        amount_text = update.message.text.strip()
        try:
            amount = float(amount_text)
            company_data = user_state.get("company_data")
            if not company_data:
                raise ValueError("Données de l'entreprise introuvables")
            db = DBManager()
            db.register_or_update_business(company_data["inn"], company_data["name"])
            db.issue_tokens(company_data["inn"], amount)
            await update.message.reply_text(
                f"✅ {amount} tokens émis avec succès pour {company_data['name']}!"
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ Nombre de tokens invalide: {str(e)}")
        except Exception as e:
            await update.message.reply_text(f"❌ Erreur d'émission de tokens: {str(e)}")
        finally:
            user_state.pop("awaiting_token_amount", None)
            user_state.pop("company_data", None)

    async def show_companies(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche la liste des entreprises"""
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("Aucune entreprise disponible.")
            return
        response = "📋 Entreprises disponibles:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} (INN: {inn}) - tokens disponibles: {amount or 0}\n"
        await update.message.reply_text(response)

    async def show_balance(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Affiche le solde de tokens de l'utilisateur"""
        user_id = update.effective_user.id
        email = f"{user_id}@telegram.local"
        db = DBManager()
        user_tokens = db.get_user_tokens(email)
        if not user_tokens:
            await update.message.reply_text("Vous n'avez pas encore de tokens.")
            return
        response = "💰 Vos tokens:\n"
        for inn, name, amount in user_tokens:
            response += f"- {name}: {amount} tokens\n"
        await update.message.reply_text(response)

    async def buy_tokens(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Début du processus d'achat de tokens"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        if user_state["role"] != "user":
            await update.message.reply_text("Cette commande est réservée aux utilisateurs")
            return
        db = DBManager()
        companies = db.get_all_issuances()
        if not companies:
            await update.message.reply_text("❌ Aucune entreprise disponible pour achat.")
            return
        response = "📋 Choisissez une entreprise pour acheter des tokens:\n"
        for idx, (inn, name, amount, _) in enumerate(companies):
            response += f"{idx+1}. {name} (Tokens disponibles: {amount or 0})\n"
        response += "\nEntrez le numéro de l'entreprise et le nombre de tokens séparés par un espace\nExemple: 1 10"
        await update.message.reply_text(response)
        user_state["awaiting_purchase"] = True

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Gestion des messages texte"""
        user_id = update.effective_user.id
        user_state = self.get_user_state(user_id)
        text = update.message.text.strip()

        try:
            if user_state.get("awaiting_register"):
                name, email, password = text.split()
                user_manager = UserManager()
                try:
                    user_manager.register_user(name, email, password)
                    await update.message.reply_text(f"✅ Inscription réussie! Bienvenue, {name}!")
                    await self.show_companies(update, context)
                except UserAlreadyExists:
                    await update.message.reply_text("❌ Un utilisateur avec cet email existe déjà.")
                user_state.pop("awaiting_register", None)

            elif user_state.get("awaiting_login"):
                email, password = text.split()
                user_manager = UserManager()
                if user_manager.authenticate_user(email, password):
                    await update.message.reply_text("✅ Connexion réussie!")
                    await self.show_companies(update, context)
                else:
                    await update.message.reply_text("❌ Email ou mot de passe incorrect.")
                user_state.pop("awaiting_login", None)

            elif user_state.get("awaiting_inn"):
                await self.process_inn_input(update, context)

            elif user_state.get("awaiting_token_amount"):
                await self.process_token_amount(update, context)

            elif user_state.get("awaiting_purchase"):
                try:
                    # Notification de début de traitement
                    await update.message.reply_text("🔄 Traitement de la demande...")

                    # Découpage de l'entrée
                    parts = text.split()
                    if len(parts) != 2:
                        raise ValueError("Vous devez entrer exactement 2 nombres")

                    # Vérification que l'entrée contient des nombres
                    try:
                        company_num = int(parts[0])
                        amount = float(parts[1])
                    except ValueError:
                        raise ValueError("Le numéro d'entreprise et la quantité doivent être des nombres")

                    if company_num <= 0 or amount <= 0:
                        raise ValueError("Les nombres doivent être positifs")

                    db = DBManager()
                    companies = db.get_all_issuances()

                    if company_num > len(companies):
                        raise ValueError("Cette entreprise n'existe pas")

                    inn, name, available, _ = companies[company_num - 1]
                    if available is None or amount > available:
                        raise ValueError(f"Tokens insuffisants. Disponible: {available or 0}")

                    email = f"{user_id}@telegram.local"
                    db.issue_tokens(inn, -amount)
                    db.add_user_tokens(email, inn, amount)

                    user_tokens = db.get_user_tokens(email)
                    current_amount = next((t[2] for t in user_tokens if t[0] == inn), 0)

                    await update.message.reply_text(
                        f"✅ Achat réussi de {amount} tokens de {name}!\n"
                        f"Votre solde actuel: {current_amount}\n"
                        f"Utilisez /balance pour voir tous vos tokens"
                    )

                except ValueError as e:
                    await update.message.reply_text(
                        f"❌ Erreur de saisie: {str(e)}\n"
                        "Format correct: NUMÉRO QUANTITÉ\n"
                        "Exemple: 1 10\n"
                        "Assurez-vous que:\n"
                        "- Le numéro d'entreprise existe\n"
                        "- La quantité ne dépasse pas le disponible\n"
                        "- Les deux nombres sont positifs"
                    )

                except Exception as e:
                    await update.message.reply_text(f"❌ Erreur inattendue: {str(e)}")
                    logger.log(f"Erreur d'achat: {str(e)}", level="ERROR")

                finally:
                    user_state.pop("awaiting_purchase", None)

        except ValueError as e:
            await update.message.reply_text(f"❌ Format de saisie invalide: {str(e)}")
            logger.log(f"Erreur de saisie utilisateur {user_id}: {str(e)}", level="ERROR")

    def setup_handlers(self, application):
        """Configuration des gestionnaires de commandes"""
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
    """Lance le bot avec le token spécifié"""
    handler = TelegramBotHandler()
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    handler.setup_handlers(application)
    logger.log("✅ Bot démarré")
    application.run_polling()


if __name__ == "__main__":
    run_bot()