import logging
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup

from ..menu.markup import create_menu_markup
from .markup import (
    create_cancel_button,
    create_categories_list_markup,
    create_item_menu_markup,
    create_items_list_markup,
    create_items_menu_markup,
)
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


class ItemState(StatesGroup):
    """States for item-related operations in the bot conversation flow."""

    menu = State()  # Main item menu state
    my_items = State()  # Viewing user's items
    create_item = State()  # Creating a new item
    name = State()  # Entering item name
    content = State()  # Entering item content
    category = State()  # Selecting item category
    delete_item = State()  # Deleting an item


def register_handlers(bot: TeleBot) -> None:
    """
    Register all item-related handlers for the bot.

    Args:
        bot: The Telegram bot instance to register handlers for
    """
    logger.info("Registering item handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "item")
    def item_menu(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Handle the main item menu callback.

        Args:
            call: The callback query
            data: The data dictionary containing user and state information
        """
        user = data["user"]
        data["state"].set(ItemState.menu)

        markup = create_items_menu_markup(user.lang)

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].item_menu,
            reply_markup=markup,
        )

    @bot.callback_query_handler(func=lambda call: call.data == "create_item")
    def start_create_item(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Start the item creation process by showing category selection.

        Args:
            call: The callback query
            data: The data dictionary containing user, database session and state
        """
        user = data["user"]
        db_session = data["db_session"]
        categories = read_item_categories(db_session)

        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].choose_category,
            reply_markup=create_categories_list_markup(user.lang, categories),
        )
        data["state"].set(ItemState.name)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_item_"))
    def handle_delete_item(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Handle item deletion.

        Args:
            call: The callback query with item ID embedded in data
            data: The data dictionary containing user and database session
        """
        user = data["user"]
        db_session = data["db_session"]
        data["state"].set(ItemState.delete_item)

        # Extract item ID from callback data
        item_id = int(call.data.split("_")[2])
        delete_item(db_session, item_id)

        bot.send_message(
            user.id,
            strings[user.lang].item_deleted,
            reply_markup=create_menu_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "my_items")
    def show_my_items(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Display the user's items.

        Args:
            call: The callback query
            data: The data dictionary containing user and database session
        """
        user = data["user"]
        db_session = data["db_session"]
        data["state"].set(ItemState.my_items)

        # Get all items and filter by current user
        items = read_items(db_session)
        user_items = [item for item in items if item.owner_id == user.id]

        if not user_items:
            # Show empty state with back button
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton(
                    strings[user.lang].back_to_menu, callback_data="menu"
                )
            )

            bot.edit_message_text(
                chat_id=user.id,
                message_id=call.message.message_id,
                text=strings[user.lang].no_items,
                reply_markup=markup,
            )
            return

        # Show list of user's items
        markup = create_items_list_markup(user.lang, user_items)
        bot.send_message(
            chat_id=user.id, text=strings[user.lang].your_items, reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_item_"))
    def view_item(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Show details of a specific item.

        Args:
            call: The callback query with item ID embedded in data
            data: The data dictionary containing user and database session
        """
        user = data["user"]
        db_session = data["db_session"]

        # Extract item ID and fetch the item
        item_id = int(call.data.split("_")[2])
        item = read_item(db_session, item_id)

        if not item:
            bot.send_message(
                user.id,
                strings[user.lang].item_not_found,
                reply_markup=create_menu_markup(user.lang),
            )
            return

        # Get category name for display
        category = read_item_category(db_session, item.category)
        category_name = category.name if category else "Unknown"

        # Format item details message
        message_text = strings[user.lang].item_details.format(
            name=item.name,
            content=item.content,
            category=category_name,
            created_at=item.created_at.strftime("%Y-%m-%d %H:%M"),
        )

        # Show item details with action buttons
        markup = create_item_menu_markup(user.lang, item.id)
        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=message_text,
            reply_markup=markup,
            parse_mode="Markdown",
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
    def process_category(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """
        Process category selection during item creation.

        Args:
            call: The callback query with category ID embedded in data
            data: The data dictionary containing user and state
        """
        user = data["user"]

        # Extract and store category ID
        category_id = int(call.data.split("_")[1])
        data["state"].add_data(category=category_id)

        # Ask for item name
        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].enter_name,
            reply_markup=create_cancel_button(user.lang),
        )

    @bot.message_handler(state=ItemState.name)
    def process_name(message: types.Message, data: Dict[str, Any]) -> None:
        """
        Process the item name input.

        Args:
            message: The message containing the item name
            data: The data dictionary containing user and state
        """
        user = data["user"]

        # Store item name
        data["state"].add_data(name=message.text)

        # Ask for item content
        bot.send_message(
            user.id,
            strings[user.lang].enter_content,
            reply_markup=create_cancel_button(user.lang),
        )
        data["state"].set(ItemState.content)

    @bot.message_handler(state=ItemState.content)
    def process_content(message: types.Message, data: Dict[str, Any]) -> None:
        """
        Process the item content input and complete item creation.

        Args:
            message: The message containing the item content
            data: The data dictionary containing user, database session and state
        """
        user = data["user"]
        db_session = data["db_session"]

        # Store item content
        data["state"].add_data(content=message.text)

        # Create the item with all collected data
        with data["state"].data() as data_items:
            item = create_item(
                db_session,
                name=data_items["name"],
                content=data_items["content"],
                category=data_items["category"],
                owner_id=message.from_user.id,
            )

        # Confirm item creation
        bot.send_message(
            user.id,
            strings[user.lang].item_created.format(name=item.name),
            reply_markup=create_menu_markup(user.lang),
            parse_mode="Markdown",
        )

        # Clear the state
        data["state"].delete()
