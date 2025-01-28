import logging
import os
from datetime import datetime

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup
from telebot.states.sync.context import StateContext

from ....core.google_sheets import GoogleSheetsClient
from ..common import create_cancel_button

# Set logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf" , "apps", "google_sheets.yaml")
config = OmegaConf.load(config_path)
app_config = config.app
strings = config.strings

google_sheets = GoogleSheetsClient(share_emails=app_config.share_emails)


# Define States
class GoogleSheetsState(StatesGroup):
    """ Google Sheets states """
    first_name = State()
    second_name = State()
    phone_number = State()
    birthday = State()
    select_worksheet = State()
    worksheet_name = State()


# Helper functions
def is_valid_phone_number(phone_number):
    return phone_number.isdigit() and len(phone_number) in [10, 11]


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False


def register_handlers(bot: TeleBot):
    """Register resource handlers"""
    logger.info("Registering resource handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "google_sheets")
    def start(call: types.CallbackQuery, data: dict):
        user = data["user"]
        state = StateContext(call, bot)

        state.set(GoogleSheetsState.first_name)

        bot.send_message(call.message.chat.id, strings.en.welcome, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=GoogleSheetsState.first_name)
    def get_first_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        state.set(GoogleSheetsState.second_name)
        state.add_data(first_name=message.text)
        bot.send_message(message.chat.id, strings.en.enter_second_name, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=GoogleSheetsState.second_name)
    def get_second_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        state.set(GoogleSheetsState.phone_number)
        state.add_data(second_name=message.text)
        bot.send_message(message.chat.id, strings.en.enter_phone_number, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=GoogleSheetsState.phone_number)
    def get_phone_number(message: types.Message, data: dict):
        user = data["user"]
        if not is_valid_phone_number(message.text):
            bot.send_message(
                message.chat.id, strings.en.invalid_phone_number, reply_markup=create_cancel_button(user.lang)
            )
            return
        state = StateContext(message, bot)
        state.set(GoogleSheetsState.birthday)
        state.add_data(phone_number=message.text)
        bot.send_message(message.chat.id, strings.en.enter_birthday, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=GoogleSheetsState.birthday)
    def get_birthday(message: types.Message, data: dict):
        user = data["user"]
        if not is_valid_date(message.text):
            bot.send_message(
                message.chat.id, strings.en.invalid_date_format, reply_markup=create_cancel_button(user.lang)
            )
            return
        state = StateContext(message, bot)
        state.add_data(birthday=message.text)

        # Create google sheet for the user
        user_id_str = str(user.id)
        try:
            sheet = google_sheets.get_sheet(user_id_str)
        except:
            sheet = google_sheets.create_sheet(user_id_str)

        # Get existing worksheets
        worksheet_names = google_sheets.get_table_names(sheet)
        worksheet_buttons = [types.InlineKeyboardButton(text=name, callback_data=name) for name in worksheet_names]
        worksheet_buttons.append(
            types.InlineKeyboardButton(text=strings[user.lang].create_new_worksheet, callback_data="create_new")
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(*worksheet_buttons)

        state.set(GoogleSheetsState.select_worksheet)
        bot.send_message(message.chat.id, strings[user.lang].select_worksheet, reply_markup=markup)

    @bot.callback_query_handler(state=GoogleSheetsState.select_worksheet)
    def choose_worksheet(call: types.CallbackQuery, data: dict):
        user = data["user"]
        state = StateContext(call, bot)
        worksheet_choice = call.data

        if worksheet_choice == "create_new":
            state.set(GoogleSheetsState.worksheet_name)
            bot.send_message(
                call.message.chat.id, strings.en.enter_worksheet_name, reply_markup=create_cancel_button(user.lang)
            )
        else:
            sheet = google_sheets.get_sheet(str(user.id))
            with state.data() as data_items:
                google_sheets.add_row(sheet, worksheet_choice, list(data_items.values()))
                logger.info(f"Data added to Google Sheet: {data_items}")

            public_link = google_sheets.get_public_link(sheet)

            bot.send_message(call.message.chat.id, strings[user.lang].resource_created.format(public_link=public_link))
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
        except:
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

        bot.send_message(message.chat.id, strings[user.lang].resource_created.format(public_link=public_link))
        state.delete()
