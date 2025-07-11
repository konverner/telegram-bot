"""Handler to show information about the application configuration."""
import logging

import os
from datetime import datetime
from pathlib import Path

from omegaconf import OmegaConf
from telebot.states import State, StatesGroup
from telebot.types import CallbackQuery, Message

from ..auth.service import read_user, upsert_user
from ..database.core import export_all_tables
from .markup import create_cancel_button, create_users_menu_markup

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
app_strings = config.strings

# States
class UsersStates(StatesGroup):
    """Application states"""

    users_menu = State()
    read_user_data = State()
    user_menu = State()


def register_handlers(bot):
    """Register about handlers"""
    logger.info("Registering `about` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "users")
    def add_admin_handler(call: CallbackQuery, data: dict):
        user = data["user"]

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=app_strings[user.lang].enter_username_or_user_id,
            reply_markup=create_cancel_button(user.lang),
        )

        # Set the state
        data["state"].set(UsersStates.read_user_data)

    @bot.message_handler(state=UsersStates.read_user_data)
    def read_user_data(message: Message, data: dict):
        user = data["user"]
        user_data = message.text
        db_session = data["db_session"]

        if user_data.isdigit():
            retrieved_user = read_user(db_session, id=int(user_data))
            if not retrieved_user:
                bot.send_message(
                    user.id,
                    app_strings[user.lang].user_id_not_found.format(user_id=user_data),
                    user_id=user_data,
                )
                return
        else:
            retrieved_user = read_user(db_session, username=user_data)
            if not retrieved_user:
                bot.send_message(
                    user.id,
                    app_strings[user.lang].username_not_found.format(
                        username=user_data
                    ),
                )
                return

        # Send the user data
        format_message = f"id: `{retrieved_user.id}`\nusername: `{retrieved_user.username}`\nrole: `{retrieved_user.role.name}`"
        format_message = app_strings[user.lang].user_info_template.format(
            user_id=retrieved_user.id,
            username=retrieved_user.username,
            first_name=retrieved_user.first_name,
            last_name=retrieved_user.last_name,
            role=retrieved_user.role.name,
            is_blocked=retrieved_user.is_blocked,
        )

        bot.send_message(
            user.id,
            format_message,
            parse_mode="Markdown",
            reply_markup=create_users_menu_markup(user.lang, retrieved_user),
        )

        # Set the state
        data["state"].set(UsersStates.user_menu)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("grant_admin"))
    def grant_admin_handler(call, data: dict):
        user = data["user"]
        grant_admin_user_id = call.data.split("_")[2]
        db_session = data["db_session"]
        upsert_user(db_session, id=grant_admin_user_id, role_id=0)
        bot.send_message(
            user.id,
            app_strings[user.lang].add_admin_confirm.format(
                user_id=grant_admin_user_id
            ),
            parse_mode="Markdown",
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("block_user"))
    def block_user_handler(call, data: dict):
        user = data["user"]
        block_user_id = call.data.split("_")[2]
        db_session = data["db_session"]
        upsert_user(db_session, id=block_user_id, is_blocked=True)
        bot.send_message(
            user.id,
            app_strings[user.lang].block_user_confirm.format(user_id=block_user_id),
            parse_mode="Markdown",
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("unblock_user"))
    def block_user_handler(call, data: dict):
        """Handler to unblock a user"""
        user = data["user"]
        block_user_id = call.data.split("_")[2]
        db_session = data["db_session"]
        upsert_user(db_session, id=block_user_id, is_blocked=False)
        bot.send_message(
            user.id,
            app_strings[user.lang].unblock_user_confirm.format(user_id=block_user_id),
            parse_mode="Markdown",
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("revoke_admin"))
    def grant_admin_handler(call, data: dict):
        """Handler to revoke admin rights from a user"""
        user = data["user"]
        revoke_admin_user_id = call.data.split("_")[2]
        db_session = data["db_session"]
        upsert_user(db_session, id=revoke_admin_user_id, role_id=1)
        bot.send_message(
            user.id,
            app_strings[user.lang].revoke_admin_confirm.format(
                user_id=revoke_admin_user_id
            ),
            parse_mode="Markdown",
        )

    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def about_handler(call):
        user_id = call.from_user.id

        config_str = OmegaConf.to_yaml(config)

        # Send config
        bot.send_message(user_id, f"```yaml\n{config_str}\n```", parse_mode="Markdown")

    @bot.callback_query_handler(func=lambda call: call.data == "export_data")
    def export_data_handler(call, data):
        user = data["user"]

        if user.role_id != 0:
            # inform that the user does not have rights
            bot.send_message(
                call.from_user.id, app_strings[user.lang].no_rights[user.lang]
            )
            return

        # Export data
        export_dir = f'./data/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(export_dir)
        try:
            export_all_tables(export_dir)
            for table in config.db.tables:
                # save as excel in temp folder and send to a user
                filename = f"{export_dir}/{table}.csv"
                bot.send_document(user.id, open(filename, "rb"))
                # remove the file
                os.remove(filename)
        except Exception as e:
            bot.send_message(user.id, str(e))
            logger.error(f"Error exporting data: {e}")
