from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..auth.models import User

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
app_strings = config.strings


def create_users_menu_markup(lang: str, retrieved_user: User) -> InlineKeyboardMarkup:
    """Create the users menu markup."""
    menu_markup = InlineKeyboardMarkup(row_width=1)
    options = app_strings[lang].menu.options

    # If retrieved user is ordinary user
    if retrieved_user.role_id == 1:
        menu_markup.add(
            InlineKeyboardButton(
                options[0].label,
                callback_data=options[0].value.format(user_id=retrieved_user.id),
            )
        )
    # If retrieved user is admin
    else:
        menu_markup.add(
            InlineKeyboardButton(
                options[1].label,
                callback_data=options[1].value.format(user_id=retrieved_user.id),
            )
        )

    if retrieved_user.is_blocked:
        menu_markup.add(
            InlineKeyboardButton(
                options[3].label,
                callback_data=options[3].value.format(user_id=retrieved_user.id),
            )
        )
    else:
        menu_markup.add(
            InlineKeyboardButton(
                options[2].label,
                callback_data=options[2].value.format(user_id=retrieved_user.id),
            )
        )
    menu_markup.add(InlineKeyboardButton(app_strings[lang].back, callback_data="users"))
    return menu_markup


def create_cancel_button(lang: str) -> InlineKeyboardMarkup:
    """Create a cancel button for the admin menu."""
    cancel_button = InlineKeyboardMarkup(row_width=1)
    cancel_button.add(
        InlineKeyboardButton(app_strings[lang].cancel, callback_data="admin")
    )
    return cancel_button
