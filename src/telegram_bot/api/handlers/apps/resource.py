import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup
from telebot.states.sync.context import StateContext
from telegram_bot.api.handlers.common import create_cancel_button, create_keyboard_markup

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

strings = OmegaConf.load("./src/telegram_bot/conf/apps/resource.yaml")


# Define States
class ResourceState(StatesGroup):
    first_name = State()
    second_name = State()
    phone_number = State()
    birthday = State()


# Helper functions
def is_valid_phone_number(phone_number):
    return phone_number.isdigit() and len(phone_number) in [10, 11]


def is_valid_date(date_str):
    try:
        datetime.strptime(date_str, "%d-%m-%Y")
        return True
    except ValueError:
        return False


# Utility: Cleanup old files
def cleanup_files(user_dir: str, retention_period_days: int = 2):
    """Delete files older than retention_period_days"""
    now = datetime.now()
    for root, _, files in os.walk(user_dir):
        for file in files:
            file_path = os.path.join(root, file)
            file_creation_time = datetime.fromtimestamp(os.path.getctime(file_path))
            if now - file_creation_time > timedelta(days=retention_period_days):
                os.remove(file_path)
                logger.info(f"Deleted old file: {file_path}")


def create_resource(user_id: int, name: str, data_items: list[dict]) -> str:
    """Create csv file"""

    # Create user directory
    user_dir = f"./tmp/{user_id}"
    print(user_dir)
    os.makedirs(user_dir, exist_ok=True)

    # Cleanup old files
    cleanup_files(user_dir)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{timestamp}_{name}.csv"
    filepath = os.path.join(user_dir, filename)

    # Create and save Excel file
    df = pd.DataFrame(data_items)
    df.to_csv(filepath, index=False)

    return filename


def register_handlers(bot: TeleBot):
    """Register resource handlers"""
    logger.info("Registering resource handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "resource")
    def start(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)

        state.set(ResourceState.first_name)

        bot.send_message(message.chat.id, strings.en.welcome, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=ResourceState.first_name)
    def get_first_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        state.set(ResourceState.second_name)
        state.add_data(first_name=message.text)
        bot.send_message(message.chat.id, strings.en.enter_second_name, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=ResourceState.second_name)
    def get_second_name(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)
        state.set(ResourceState.phone_number)
        state.add_data(second_name=message.text)
        bot.send_message(message.chat.id, strings.en.enter_phone_number, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=ResourceState.phone_number)
    def get_phone_number(message: types.Message, data: dict):
        user = data["user"]
        if not is_valid_phone_number(message.text):
            bot.send_message(
                message.chat.id, strings.en.invalid_phone_number, reply_markup=create_cancel_button(user.lang)
            )
            return
        state = StateContext(message, bot)
        state.set(ResourceState.birthday)
        state.add_data(phone_number=message.text)
        bot.send_message(message.chat.id, strings.en.enter_birthday, reply_markup=create_cancel_button(user.lang))

    @bot.message_handler(state=ResourceState.birthday)
    def get_birthday(message: types.Message, data: dict):
        user = data["user"]
        if not is_valid_date(message.text):
            bot.send_message(
                message.chat.id, strings.en.invalid_date_format, reply_markup=create_cancel_button(user.lang)
            )
            return
        state = StateContext(message, bot)
        state.add_data(birthday=message.text)
        with state.data() as data_items:
            print(data_items)
            filename = create_resource(user.id, user.id, data_items=[data_items])
        print(filename)
        download_button = create_keyboard_markup(
            [{"label": strings.en.get_resource, "value": f"GET {filename}"}],
        )
        bot.send_message(
            message.chat.id,
            "Your data has been recorded. You can download the file below:",
            parse_mode="HTML",
            reply_markup=download_button,
        )
        state.delete()

    @bot.callback_query_handler(func=lambda call: call.data.startswith("GET"))
    def get_resource(call: types.CallbackQuery, data: dict):
        """Download resource from user's folder"""
        user = data["user"]
        filename = call.data.split(" ")[1]
        file_path = os.path.join("./tmp", str(user.id), filename)
        logger.info(f"Requesting file: {file_path}")
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                bot.send_document(user.id, file, visible_file_name=filename)
        else:
            bot.answer_callback_query(call.id, strings.file_not_found[user.lang])
