import logging
from pathlib import Path

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup

from ..database.core import get_session
from ..menu.markup import create_menu_markup
from .markup import create_cancel_button, create_item_menu_markup, create_items_list_markup, create_items_menu_markup
from .service import (
    create_item,
    delete_item,
    read_item,
    read_item_categories,
    read_item_category,
    read_items,
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings

# Load the database session
db_session = get_session()

# Define States
class ItemState(StatesGroup):
    """ Item states """
    menu = State()
    my_items = State()
    create_item = State()
    name = State()
    content = State()
    category = State()
    delete_item = State()


def register_handlers(bot: TeleBot):
    """Register item handlers"""
    logger.info("Registering item handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "item")
    def item_menu(call: types.CallbackQuery, data: dict):
        user = data["user"]
        data["state"].set(ItemState.menu)

        markup = create_items_menu_markup(user.lang)

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].item_menu,
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data == "create_item")
    def start_create_item(call: types.CallbackQuery, data: dict):
        user = data["user"]
        categories = read_item_categories(db_session)
        markup = types.InlineKeyboardMarkup()
        for category in categories:
            markup.add(types.InlineKeyboardButton(category.name, callback_data=f"category_{category.id}"))

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].choose_category,
            reply_markup=markup
        )
        data["state"].set(ItemState.name)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_item_"))
    def hanlder_delete_item(call: types.CallbackQuery, data: dict):
        user = data["user"]
        data["state"].set(ItemState.delete_item)
        item_id = int(call.data.split("_")[2])
        print(f"Deleting item with ID: {item_id}")
        delete_item(db_session, item_id)
        print(f"Item with ID {item_id} deleted.")
        bot.send_message(
            user.id, strings[user.lang].item_deleted,
            reply_markup=create_menu_markup(user.lang)
        )


    @bot.callback_query_handler(func=lambda call: call.data == "my_items")
    def show_my_items(call: types.CallbackQuery, data: dict):
        user = data["user"]
        data["state"].set(ItemState.my_items)

        items = read_items(db_session)

        # Filter items by the current user
        user_items = [item for item in items if item.owner_id == user.id]

        if not user_items:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(strings[user.lang].back_to_menu, callback_data="menu"))

            bot.edit_message_text(
                chat_id=user.id,
                message_id=call.message.message_id,
                text=strings[user.lang].no_items,
                reply_markup=markup
            )
            return

        markup = create_items_list_markup(user.lang, user_items)

        bot.send_message(
            chat_id=user.id,
            text=strings[user.lang].your_items,
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_item_"))
    def view_item(call: types.CallbackQuery, data: dict):
        user = data["user"]
        item_id = int(call.data.split("_")[2])
        item = read_item(db_session, item_id)

        if not item:
            bot.send_message(user.id, strings[user.lang].item_not_found, reply_markup=create_menu_markup(user.lang))
            return

        # Get category name
        category = read_item_category(db_session, item.category)
        category_name = category.name if category else "Unknown"

        message_text = strings[user.lang].item_details.format(
            name=item.name,
            content=item.content,
            category=category_name,
            created_at=item.created_at.strftime("%Y-%m-%d %H:%M")
        )

        markup = create_item_menu_markup(user.lang, item.id)

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
    def process_category(call: types.CallbackQuery, data: dict):
        user = data["user"]
        category_id = int(call.data.split("_")[1])
        data["state"].add_data(category=category_id)

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].enter_name,
            reply_markup=create_cancel_button(user.lang)
        )


    @bot.message_handler(state=ItemState.name)
    def process_name(message: types.Message, data: dict):
        user = data["user"]
        data["state"].add_data(name=message.text)

        bot.send_message(
            user.id,
            strings[user.lang].enter_content,
            reply_markup=create_cancel_button(user.lang)
        )
        data["state"].set(ItemState.content)


    @bot.message_handler(state=ItemState.content)
    def process_content(message: types.Message, data: dict):
        user = data["user"]
        data["state"].add_data(content=message.text)
        with data["state"].data() as data_items:
            # Create item in the database
            item = create_item(
                db_session,
                name=data_items['name'], content=data_items['content'],
                category=data_items['category'], owner_id=message.from_user.id
                )

        bot.send_message(
            user.id,
            strings[user.lang].item_created.format(name=item.name),
            reply_markup=create_menu_markup(user.lang),
            parse_mode="Markdown"
        )
        data["state"].delete()
