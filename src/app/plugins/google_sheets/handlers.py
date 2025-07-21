import logging
from pathlib import Path

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup
from telebot.states.sync.context import StateContext

from ...menu.markup import create_menu_markup
from .client import GoogleSheetsClient
from .markup import create_cancel_button, create_worksheet_selection_markup
from .utils import is_valid_date, is_valid_phone_number

# Set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings

google_sheets = GoogleSheetsClient(share_emails=config.app.share_emails)

# Define States
class GoogleSheetsState(StatesGroup):
    """Google Sheets states"""

    first_name = State()
    second_name = State()
    phone_number = State()
    birthday = State()
    select_worksheet = State()
    worksheet_name = State()


def register_handlers(bot: TeleBot):
    """Register resource handlers"""
    logger.info("Registering resource handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_google_sheets")
    def cancel(call: types.CallbackQuery, data: dict):
        user = data["user"]
        state = StateContext(call, bot)
        state.delete()
        bot.edit_message_text(
            strings[user.lang].operation_cancelled,
            call.message.chat.id,
            call.message.message_id,
        )

        # Send the main menu
        bot.send_message(
            call.message.chat.id,
            strings[user.lang].main_menu,
            reply_markup=create_menu_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "google_sheets")
    def start(call: types.CallbackQuery, data: dict):
        user = data["user"]
        state = StateContext(call, bot)
        state.set(GoogleSheetsState.first_name)

        bot.edit_message_text(
            strings[user.lang].welcome,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_cancel_button(user.lang),
        )

    @bot.message_handler(state=GoogleSheetsState.first_name)
    def get_first_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        state.set(GoogleSheetsState.second_name)
        state.add_data(first_name=message.text)
        bot.send_message(
            message.chat.id,
            strings[user.lang].enter_second_name,
            reply_markup=create_cancel_button(user.lang),
        )

    @bot.message_handler(state=GoogleSheetsState.second_name)
    def get_second_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        state.set(GoogleSheetsState.phone_number)
        state.add_data(second_name=message.text)
        bot.send_message(
            message.chat.id,
            strings[user.lang].enter_phone_number,
            reply_markup=create_cancel_button(user.lang),
        )

    @bot.message_handler(state=GoogleSheetsState.phone_number)
    def get_phone_number(message: types.Message, data: dict):
        user = data["user"]
        if not is_valid_phone_number(message.text):
            bot.send_message(
                message.chat.id,
                strings[user.lang].invalid_phone_number,
                reply_markup=create_cancel_button(user.lang),
            )
            return
        state = StateContext(message, bot)
        state.set(GoogleSheetsState.birthday)
        state.add_data(phone_number=message.text)
        bot.send_message(
            message.chat.id,
            strings[user.lang].enter_birthday,
            reply_markup=create_cancel_button(user.lang),
        )

    @bot.message_handler(state=GoogleSheetsState.birthday)
    def get_birthday(message: types.Message, data: dict):
        user = data["user"]
        if not is_valid_date(message.text):
            bot.send_message(
                message.chat.id,
                strings[user.lang].invalid_date_format,
                reply_markup=create_cancel_button(user.lang),
            )
            return
        state = StateContext(message, bot)
        state.add_data(birthday=message.text)

        # Create google sheet for the user
        user_id_str = str(user.id)
        try:
            sheet = google_sheets.get_sheet(user_id_str)
        except Exception:
            logger.info(f"Google Sheet for user {user_id_str} not found")
            sheet = google_sheets.create_sheet(user_id_str)

        # Get existing worksheets
        worksheet_names = google_sheets.get_table_names(sheet)
        markup = create_worksheet_selection_markup(worksheet_names, user.lang)

        state.set(GoogleSheetsState.select_worksheet)
        bot.send_message(
            message.chat.id, strings[user.lang].select_worksheet, reply_markup=markup
        )

    @bot.callback_query_handler(state=GoogleSheetsState.select_worksheet)
    def choose_worksheet(call: types.CallbackQuery, data: dict):
        user = data["user"]
        state = StateContext(call, bot)
        worksheet_choice = call.data

        if worksheet_choice == "create_new":
            state.set(GoogleSheetsState.worksheet_name)
            bot.send_message(
                call.message.chat.id,
                strings[user.lang].enter_worksheet_name,
                reply_markup=create_cancel_button(user.lang),
            )
        else:
            sheet = google_sheets.get_sheet(str(user.id))
            with state.data() as data_items:
                google_sheets.add_row(
                    sheet, worksheet_choice, list(data_items.values())
                )
                logger.info(f"Data added to Google Sheet: {data_items}")

            public_link = google_sheets.get_public_link(sheet)

            bot.send_message(
                call.message.chat.id,
                strings[user.lang].resource_created.format(public_link=public_link),
            )
            state.delete()

    @bot.message_handler(state=GoogleSheetsState.worksheet_name)
    def get_worksheet_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        worksheet_name = message.text

        user_id_str = str(user.id)

        # Create google sheet for the user
        try:
            sheet = google_sheets.get_sheet(user_id_str)
        except Exception:
            logger.info(f"Google Sheet for user {user_id_str} not found")
            sheet = google_sheets.create_sheet(user_id_str)

        # Create worksheet for the user if it doesn't exist
        try:
            google_sheets.create_worksheet(sheet, worksheet_name)
        except Exception:
            logging.info(f"Worksheet {worksheet_name} already exists")

        with state.data() as data_items:
            google_sheets.add_row(sheet, worksheet_name, list(data_items.values()))
            logger.info(f"Data added to Google Sheet: {data_items}")

        public_link = google_sheets.get_public_link(sheet)

        bot.send_message(
            message.chat.id,
            strings[user.lang].resource_created.format(public_link=public_link),
        )
        state.delete()
