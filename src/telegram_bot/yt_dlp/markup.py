import logging
from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load configuration
CURRENT_DIR = Path(__file__).parent
try:
    config = OmegaConf.load(CURRENT_DIR / "config.yaml")
    strings = config.strings
except FileNotFoundError:
    logging.error(f"Config file not found at {CURRENT_DIR / 'config.yaml'}")
    # Provide default strings or handle the error appropriately
    strings = OmegaConf.create(
        {
            "en": {
                "video": "Video (mp4)",
                "audio": "Audio (mp3)",
                "cancel": "Cancel",
                "back_to_menu": "⬅️ Back to Menu",
            }
        }
    )  # Basic fallback

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_format_selection_markup(lang: str) -> InlineKeyboardMarkup:
    """Creates markup for selecting video or audio format."""
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton(strings[lang].video, callback_data="ydl_format_video"),
        InlineKeyboardButton(strings[lang].audio, callback_data="ydl_format_audio"),
    )
    markup.add(InlineKeyboardButton(strings[lang].cancel, callback_data="ydl_cancel"))
    return markup


def create_cancel_button(
    lang: str, callback_data: str = "menu"
) -> InlineKeyboardMarkup:
    """Creates a generic cancel button."""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(strings[lang].cancel, callback_data=callback_data),
    )
    return markup


def create_back_to_menu_button(lang: str) -> InlineKeyboardMarkup:
    """Creates a button to go back to the main menu."""
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton(strings[lang].back_to_menu, callback_data="menu"),
    )
    return markup
