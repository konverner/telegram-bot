from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings

def create_lang_menu_markup(lang: str) -> InlineKeyboardMarkup:
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    for option in strings[lang].options:
        lang_menu_markup.add(
            InlineKeyboardButton(option.name, callback_data=f"_{option.code}")
        )
    return lang_menu_markup
