import logging
from pathlib import Path

from omegaconf import OmegaConf
from telebot import TeleBot
from telebot.states import State, StatesGroup
from telebot.types import CallbackQuery, Message

from .markup import create_lang_menu_markup
from ..auth.service import update_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


class LanguageState(StatesGroup):
    """States for language selection in the bot conversation flow."""
    choose_language = State()  # State for choosing language


def register_handlers(bot: TeleBot):

    @bot.callback_query_handler(func=lambda call: call.data == "language")
    def change_language(call: CallbackQuery, data: dict):
        user = data["user"]
        lang = user.lang
        
        lang_menu_markup = create_lang_menu_markup(lang)
        bot.send_message(
            call.message.chat.id, strings[lang].title,
            reply_markup=lang_menu_markup
        )

        # Set the state to choose language
        data["state"].set(LanguageState.choose_language)

    @bot.callback_query_handler(state=LanguageState.choose_language)
    def set_language(call: CallbackQuery, data: dict):
        new_lang = call.data.strip("_")
        user = data["user"]
        db_session = data["db_session"]
        
        update_user(db_session, user.id, lang=new_lang)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=strings[new_lang].language_updated
        )
