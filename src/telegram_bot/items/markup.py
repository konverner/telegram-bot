import logging

from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from .models import Item

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_items_menu_markup(lang: str) -> InlineKeyboardMarkup:
    """Create the items menu markup"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(strings[lang].create_item, callback_data="create_item")
    )
    markup.add(InlineKeyboardButton(strings[lang].my_items, callback_data="my_items"))
    markup.add(InlineKeyboardButton(strings[lang].back_to_menu, callback_data="menu"))
    return markup


def create_item_menu_markup(lang: str, item_id: int) -> InlineKeyboardMarkup:
    """Create the item menu markup"""
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(
            strings[lang].delete_item, callback_data=f"delete_item_{item_id}"
        )
    )
    markup.add(
        InlineKeyboardButton(strings[lang].back_to_items, callback_data="my_items")
    )
    markup.add(InlineKeyboardButton(strings[lang].back_to_menu, callback_data="menu"))
    return markup


def create_items_list_markup(lang: str, items: list[Item]) -> InlineKeyboardMarkup:
    """Create the items menu markup"""
    markup = InlineKeyboardMarkup()
    for item in items:
        markup.add(
            InlineKeyboardButton(item.name, callback_data=f"view_item_{item.id}")
        )

    markup.add(InlineKeyboardButton(strings[lang].back_to_menu, callback_data="menu"))
    return markup


def create_categories_list_markup(
    lang: str, categories: list[str]
) -> InlineKeyboardMarkup:
    """Create the categories list markup"""
    markup = InlineKeyboardMarkup()
    for category in categories:
        markup.add(
            InlineKeyboardButton(category.name, callback_data=f"category_{category.id}")
        )
    return markup


def create_cancel_button(lang: str) -> InlineKeyboardMarkup:
    """Create a cancel button for the items menu"""
    cancel_button = InlineKeyboardMarkup(row_width=1)
    cancel_button.add(
        InlineKeyboardButton(strings[lang].cancel, callback_data="item"),
    )
    return cancel_button
