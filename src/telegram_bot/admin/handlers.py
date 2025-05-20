"""Handler to show information about the application configuration."""
import logging

import os
from ast import Call
from datetime import datetime
from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import CallbackQuery, Message

from ..database.core import export_all_tables
from .markup import create_admin_menu_markup

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
app_strings = config.strings


def register_handlers(bot):
    """Register about handlers"""
    logger.info("Registering `about` handlers")

    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message: Message, data: dict):
        """Handler to show the admin menu."""
        user = data["user"]
        if user.role_id not in {0, 1}:
            # Inform the user that they do not have admin rights
            bot.send_message(message.from_user.id, app_strings[user.lang].no_rights)
            return

        # Send the admin menu
        bot.send_message(
            message.from_user.id,
            app_strings[user.lang].menu.title,
            reply_markup=create_admin_menu_markup(user.lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "admin")
    def admin_menu_handler(call: CallbackQuery, data: dict):
        """Handler to show the admin menu."""
        user = data["user"]
        if user.role_id not in {0, 1}:
            # Inform the user that they do not have admin rights
            bot.send_message(call.message.from_user.id, app_strings[user.lang].no_rights)
            return

        # Edit message instead
        bot.edit_message_text(
            app_strings[user.lang].menu.title,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_admin_menu_markup(user.lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "about")
    def about_handler(call: Call, data: dict):
        user_id = call.from_user.id

        config_str = OmegaConf.to_yaml(config)

        # Send config
        bot.send_message(user_id, f"```yaml\n{config_str}\n```", parse_mode="Markdown")


    @bot.callback_query_handler(func=lambda call: call.data == "export_data")
    def export_data_handler(call, data):
        user = data["user"]

        if user.role_id != 0:
            # inform that the user does not have rights
            bot.send_message(call.from_user.id, app_strings.users.no_rights[user.lang])
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


