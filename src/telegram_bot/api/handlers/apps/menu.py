import logging.config

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

strings = OmegaConf.load("./src/telegram_bot/conf/apps/menu.yaml")


def create_user_menu_markup(lang) -> InlineKeyboardMarkup:
    """Create the menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in strings[lang].options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def register_handlers(bot):
    """Register menu handlers"""
    logger.info("Registering menu handlers")

    @bot.message_handler(commands=["menu", "main_menu"])
    def menu_menu_command(message: Message, data: dict):
        user = data["user"]

        bot.send_message(message.chat.id, strings[user.lang].title, reply_markup=create_user_menu_markup(user.lang))
