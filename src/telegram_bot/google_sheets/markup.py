import logging
from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_worksheet_selection_markup(worksheet_names: list[str], lang: str):
    worksheet_buttons = [
        InlineKeyboardButton(text=name, callback_data=name) for name in worksheet_names
    ]
    worksheet_buttons.append(
        InlineKeyboardButton(
            text=strings[lang].create_new_worksheet, callback_data="create_new"
        )
    )

    markup = InlineKeyboardMarkup()
    markup.add(*worksheet_buttons)
    return markup


def create_cancel_button(lang):
    cancel_button = InlineKeyboardMarkup(row_width=1)
    cancel_button.add(
        InlineKeyboardButton(
            strings[lang].cancel, callback_data="cancel_google_sheets"
        ),
    )
    return cancel_button
