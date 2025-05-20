import logging

from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
app_strings = config.strings

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_admin_menu_markup(lang: str) -> InlineKeyboardMarkup:
    """Create the admin menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in app_strings[lang].menu.options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def create_users_menu_markup(lang: str, user_id: str) -> InlineKeyboardMarkup:
    """Create the users menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in app_strings[lang].users.menu.options:
        menu_markup.add(
            InlineKeyboardButton(
                option.label, callback_data=option.value.format(user_id=user_id)
            )
        )
    return menu_markup


def create_cancel_button(lang: str) -> InlineKeyboardMarkup:
    """Create a cancel button for the admin menu."""
    cancel_button = InlineKeyboardMarkup(row_width=1)
    cancel_button.add(
        InlineKeyboardButton(app_strings[lang].cancel, callback_data="cancel_admin")
    )
    return cancel_button
