import logging
from pathlib import Path

from omegaconf import OmegaConf
from telebot.states import State
from telebot.states.sync.context import StateContext, StatesGroup
from telebot.types import Message

from .markup import create_admin_menu_markup, create_menu_markup

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


class MenuStates(StatesGroup):
    menu = State()
    admin = State()


def register_handlers(bot):
    """Register menu handlers"""
    logger.info("Registering menu handlers")

    @bot.message_handler(commands=["menu", "start"])
    def menu_menu_command(message: Message, data: dict):
        user = data["user"]

        # Set state
        state = StateContext(message, bot)
        state.set(MenuStates.menu)

        bot.send_message(
            message.chat.id,
            strings[user.lang].main_menu.title,
            reply_markup=create_menu_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "menu")
    def menu_menu_command(call, data: dict):
        user = data["user"]

        # Set state
        data["state"].set(MenuStates.menu)

        bot.send_message(
            call.message.chat.id,
            strings[user.lang].main_menu.title,
            reply_markup=create_menu_markup(user.lang),
        )

    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message: Message, data: dict):
        """Handler to show the admin menu."""
        user = data["user"]
        if user.role_id != 0:
            # Inform the user that they do not have admin rights
            bot.send_message(message.from_user.id, strings[user.lang].no_rights)
            return

        # Set state
        state = StateContext(message, bot)
        state.set(MenuStates.menu)

        # Send the admin menu
        bot.send_message(
            message.from_user.id,
            strings[user.lang].admin_menu.title,
            reply_markup=create_admin_menu_markup(user.lang),
        )
