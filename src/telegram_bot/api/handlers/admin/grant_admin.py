import logging
import logging.config

from omegaconf import OmegaConf
from telebot import types
from telegram_bot.api.handlers.common import create_cancel_button
from telegram_bot.db import crud

# Load configuration
strings = OmegaConf.load("./src/telegram_bot/conf/admin/grant_admin.yaml")

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# React to any text if not command
def register_handlers(bot):
    """Register grant admin handlers"""
    logger.info("Registering grant admin handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "add_admin")
    def add_admin_handler(call: types.CallbackQuery, data: dict):
        user = data["user"]

        # Ask for the username
        sent_message = bot.send_message(
            user.id, strings[user.lang].enter_username, reply_markup=create_cancel_button(user.lang)
        )

        # Move to the next step: receiving the custom message
        bot.register_next_step_handler(sent_message, read_username, bot, user)

    def read_username(message, bot, user):
        admin_username = message.text

        # Look for the user in the database
        retrieved_user = crud.read_user_by_username(username=admin_username)
        # if user does not exists
        if not retrieved_user:
            bot.send_message(
                user.id, strings[user.lang].user_not_found.format(username=admin_username), parse_mode="MarkdownV2"
            )
        # if user is already admin
        elif retrieved_user.role == "admin":
            bot.send_message(
                user.id, strings[user.lang].user_already_admin.format(username=admin_username), parse_mode="MarkdownV2"
            )
        else:
            crud.upsert_user(id=retrieved_user.id, username=retrieved_user.username, role="admin")

            bot.send_message(
                user.id,
                strings[user.lang].add_admin_confirm.format(
                    user_id=int(retrieved_user.id), username=retrieved_user.username
                ),
                parse_mode="MarkdownV2",
            )
