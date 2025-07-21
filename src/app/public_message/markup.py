from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


def create_keyboard_markup(lang: str) -> InlineKeyboardMarkup:
    """Create an InlineKeyboardMarkup object for the public message menu"""
    keyboard_markup = InlineKeyboardMarkup()
    for option in strings[lang].menu.options:
        keyboard_markup.add(
            InlineKeyboardButton(option.label, callback_data=option.value)
        )
    return keyboard_markup

