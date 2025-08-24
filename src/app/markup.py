from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def create_cancel_button(lang: str) -> InlineKeyboardMarkup:
    """Create a cancel button"""
    cancel_button = InlineKeyboardMarkup(row_width=1)
    cancel_button.add(
        InlineKeyboardButton("Cancel", callback_data="cancel"),
    )
    return cancel_button
