import logging
import logging.config
import os

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf" , "admin", "menu.yaml")
config = OmegaConf.load(config_path)
strings = config.strings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_menu_markup(lang) -> InlineKeyboardMarkup:
    """Create the admin menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in strings[lang].admin_menu.options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def register_handlers(bot):
    """Register the handlers for the admin menu."""

    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message: Message, data: dict):
        """Handler to show the admin menu."""
        user = data["user"]
        if user.role != "admin":
            # Inform the user that they do not have admin rights
            bot.send_message(message.from_user.id, strings[user.lang].no_rights)
            return

        # Send the admin menu
        bot.send_message(
            message.from_user.id, strings[user.lang].admin_menu.title, reply_markup=create_admin_menu_markup(user.lang)
        )
