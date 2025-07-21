import logging
import os
from pathlib import Path

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf
from telebot.states.sync.middleware import StateMiddleware

from .admin.handlers import register_handlers as admin_handlers
from .auth.data import init_roles_table, init_superuser
from .chatgpt.handlers import register_handlers as chatgpt_handlers
from .database.core import SessionLocal, create_tables, drop_tables
from .items.data import init_item_categories_table
from .items.handlers import register_handlers as items_handlers
from .menu.handlers import register_handlers as menu_handlers
from .language.handler import register_handlers as language_handlers
from .middleware.antiflood import AntifloodMiddleware
from .middleware.database import DatabaseMiddleware
from .middleware.user import UserCallbackMiddleware, UserMessageMiddleware
from .plugins.google_sheets.handlers import register_handlers as google_sheets_handlers
from .plugins.yt_dlp.handlers import register_handlers as ydl_handlers
from .public_message.handlers import register_handlers as public_message_handlers
from .users.handlers import register_handlers as users_handlers

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")

# Load and get environment variables
load_dotenv(find_dotenv(usecwd=True))
SUPERUSER_USERNAME = os.getenv("SUPERUSER_USERNAME")
SUPERUSER_USER_ID = os.getenv("SUPERUSER_USER_ID")


def start_bot():
    """Start the Telegram bot with configuration, middlewares, and handlers."""
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    if not BOT_TOKEN:
        logging.critical("BOT_TOKEN is not set in environment variables")
        raise ValueError("BOT_TOKEN environment variable is required")

    logger.info(f"Initializing {config.name} v{config.version}")

    try:
        bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)
        _setup_middlewares(bot)
        _register_handlers(bot)
        bot.add_custom_filter(telebot.custom_filters.StateFilter(bot))

        bot_info = bot.get_me()
        logger.info(
            f"Bot {bot_info.username} (ID: {bot_info.id}) initialized successfully"
        )

        _start_polling_loop(bot)

    except Exception as e:
        logging.critical(f"Failed to start bot: {str(e)}")
        raise


def _setup_middlewares(bot):
    """Configure bot middlewares."""
    if config.antiflood.enabled:
        logger.info(
            f"Enabling antiflood (window: {config.antiflood.time_window_seconds}s)"
        )
        bot.setup_middleware(
            AntifloodMiddleware(bot, config.antiflood.time_window_seconds)
        )

    bot.setup_middleware(StateMiddleware(bot))
    bot.setup_middleware(DatabaseMiddleware(bot))
    bot.setup_middleware(UserMessageMiddleware(bot))
    bot.setup_middleware(UserCallbackMiddleware(bot))


def _register_handlers(bot):
    """Register all bot handlers."""
    handlers = [
        admin_handlers,
        chatgpt_handlers,
        menu_handlers,
        google_sheets_handlers,
        public_message_handlers,
        ydl_handlers,
        users_handlers,
        items_handlers,
        language_handlers
    ]
    for handler in handlers:
        handler(bot)


def _start_polling_loop(bot):
    """Start the main bot polling loop with error handling."""
    logger.info("Starting bot polling...")
    bot.polling(none_stop=True, interval=0, timeout=60, long_polling_timeout=60)


def init_db():
    """Initialize the database for applications."""
    # Create tables
    create_tables()

    # Create a new database session directly using SessionLocal
    db_session = SessionLocal()

    init_roles_table(db_session)

    # Add admin to user table
    if SUPERUSER_USER_ID:
        init_superuser(db_session, SUPERUSER_USER_ID, SUPERUSER_USERNAME)
        logger.info(f"Superuser {SUPERUSER_USERNAME} added successfully.")

    init_item_categories_table(db_session)

    db_session.close()

    logger.info("Database initialized")


if __name__ == "__main__":
    drop_tables()
    init_db()
    start_bot()
