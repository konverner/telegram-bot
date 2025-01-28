import logging
import os
from datetime import datetime, timedelta

import pandas as pd

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup

from ....db import crud
from ..common import create_cancel_button
from .menu import create_main_menu_button

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf" , "apps", "item.yaml")
config = OmegaConf.load(config_path)
strings = config.strings

# Define States
class ItemState(StatesGroup):
    """ Item states """
    category = State()
    name = State()
    content = State()


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


def create_item(user_id: int, name: str, data_items: list[dict]) -> str:
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
    """Register item handlers"""
    logger.info("Registering item handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "item")
    def start(call: types.CallbackQuery, data: dict):
        user = data["user"]
        categories = crud.read_item_categories()
        markup = types.InlineKeyboardMarkup()
        for category in categories:
            markup.add(types.InlineKeyboardButton(category.name, callback_data=f"category_{category.id}"))
        bot.send_message(user.id, strings[user.lang].choose_category, reply_markup=markup)
        data["state"].set(ItemState.category)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
    def process_category(call: types.CallbackQuery, data: dict):
        user = data["user"]
        category_id = int(call.data.split("_")[1])
        data["state"].add_data(category=category_id)

        bot.send_message(user.id, strings[user.lang].enter_name, reply_markup=create_cancel_button(user.lang))
        data["state"].set(ItemState.name)

    @bot.message_handler(state=ItemState.name)
    def process_name(message: types.Message, data: dict):
        user = data["user"]
        data["state"].add_data(name=message.text)
        bot.send_message(user.id, strings[user.lang].enter_content, reply_markup=create_cancel_button(user.lang))
        data["state"].set(ItemState.content)

    @bot.message_handler(state=ItemState.content)
    def process_content(message: types.Message, data: dict):
        user = data["user"]
        data["state"].add_data(content=message.text)
        with data["state"].data() as data_items:
            # Create item in the database
            item = crud.create_item(
                name=data_items['name'], content=data_items['content'],
                category=data_items['category'], owner_id=message.from_user.id
                )

        bot.send_message(
            user.id,
            strings[user.lang].item_created.format(name=item.name),
            reply_markup=create_main_menu_button(user.lang),
            parse_mode="Markdown"
        )
        data["state"].delete()
