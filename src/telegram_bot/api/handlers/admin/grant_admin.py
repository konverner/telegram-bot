import logging
import logging.config
import os

from omegaconf import OmegaConf
from telebot import types

from ....db import crud
from ..common import create_cancel_button


# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf" , "admin", "grant_admin.yaml")
config = OmegaConf.load(config_path)
strings = config.strings

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
            user.id, strings[user.lang].enter_username_or_user_id,
            reply_markup=create_cancel_button(user.lang)
        )

        # Move to the next step: receiving the custom message
        bot.register_next_step_handler(sent_message, read_user_data, bot, user)

    def read_user_data(message, bot, user):
        user_data = message.text

        def grant_admin(retrieved_user):
            crud.upsert_user(id=retrieved_user.id, role="admin")
            bot.send_message(user.id, strings[user.lang].add_admin_confirm, username=retrieved_user.username)

        if user_data.isdigit():
            retrieved_user = crud.read_user(id=int(user_data))
            if not retrieved_user:
                bot.send_message(user.id, strings[user.lang].user_id_not_found.format(user_id=user_data), user_id=user_data)
            elif retrieved_user.role == "admin":
                bot.send_message(user.id, strings[user.lang].user_already_admin.format(user_data=user_data), username=user_data)
            else:
                grant_admin(retrieved_user)
        else:
            retrieved_user = crud.read_user_by_username(username=user_data)
            if not retrieved_user:
                bot.send_message(user.id, strings[user.lang].username_not_found.format(username=user_data), username=user_data)
            elif retrieved_user.role == "admin":
                bot.send_message(user.id, strings[user.lang].username_already_admin.format(username=user_data), username=user_data)
            else:
                grant_admin(retrieved_user)