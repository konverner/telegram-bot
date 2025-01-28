import os

from omegaconf import OmegaConf
from telebot import types
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
config_path = os.path.join(project_dir, "conf", "common.yaml")
config = OmegaConf.load(config_path)
strings = config.strings


def create_keyboard_markup(
    options: list[dict[str, str]],
    orientation: str = "vertical",
) -> InlineKeyboardMarkup:
    """Create an InlineKeyboardMarkup object from a list of options.
    Args:
        options: List of options to create the keyboard from.
        orientation: The orientation of the keyboard. Must be 'horizontal' or 'vertical'.
    Returns:
        InlineKeyboardMarkup: The created keyboard markup object

    """
    if orientation == "horizontal":
        keyboard_markup = InlineKeyboardMarkup(row_width=len(options))
    elif orientation == "vertical":
        keyboard_markup = InlineKeyboardMarkup(row_width=1)
    else:
        raise ValueError("Invalid orientation value. Must be 'horizontal' or 'vertical'")
    buttons = [InlineKeyboardButton(option["label"], callback_data=option["value"]) for option in options]
    keyboard_markup.add(*buttons)
    return keyboard_markup


def create_cancel_button(lang):
    cancel_button = InlineKeyboardMarkup(row_width=1)
    cancel_button.add(
        InlineKeyboardButton(strings[lang].cancel, callback_data="cancel"),
    )
    return cancel_button


# React to any text if not command
def register_handlers(bot):
    """Register common handlers"""

    @bot.callback_query_handler(func=lambda call: call.data == "cancel")
    def cancel_callback(call: types.CallbackQuery, data: dict):
        """Cancel current operation"""
        user = data["user"]
        bot.send_message(call.message.chat.id, strings[user.lang].cancelled)
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
