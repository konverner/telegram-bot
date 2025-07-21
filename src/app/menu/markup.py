from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load configurations
# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


def create_menu_markup(lang: str) -> InlineKeyboardMarkup:
    """Create the menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in strings[lang].main_menu.options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def create_admin_menu_markup(lang: str) -> InlineKeyboardMarkup:
    """Create the admin menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in strings[lang].admin_menu.options:
        menu_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return menu_markup


def create_menu_button_markup(lang: str) -> InlineKeyboardMarkup:
    """Create the main menu button."""
    return InlineKeyboardMarkup().add(
        InlineKeyboardButton(strings[lang].title, callback_data="menu")
    )
