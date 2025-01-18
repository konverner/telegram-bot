import logging

from omegaconf import OmegaConf
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from telegram_bot.db import crud

# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app_config = OmegaConf.load("./src/telegram_bot/conf/apps/language.yaml")
app_strings = app_config.strings

def create_lang_menu_markup(strings):
    lang_menu_markup = InlineKeyboardMarkup(row_width=1)
    lang_menu_markup.add(
        InlineKeyboardButton(strings.language_en, callback_data="_en"),
        InlineKeyboardButton(strings.language_ru, callback_data="_ru")
    )
    return lang_menu_markup

# Define States
class LanguageState:
    select_language = "select_language"

def register_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda call: call.data == "language")
    def change_language(call: CallbackQuery, data: dict):
        user = data["user"]

        data["state"] = LanguageState.select_language

        lang_menu_markup = create_lang_menu_markup(app_strings[user.lang])

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=app_strings[user.lang].select_language,
            reply_markup=lang_menu_markup
        )

    @bot.callback_query_handler(func=lambda call: call.data in ["_en", "_ru"])
    def set_language(call: CallbackQuery, data: dict):
        new_lang = call.data.strip("_")
        user = data["user"]
        crud.update_user(id=user.id, lang=new_lang)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=app_strings[new_lang].language_updated
        )

        data["state"].delete()
