import logging
import logging.config
import os

import telebot
from dotenv import find_dotenv, load_dotenv
from omegaconf import OmegaConf
from telebot.states.sync.middleware import StateMiddleware

from .handlers import admin, apps
from .middlewares.antiflood import AntifloodMiddleware
from .middlewares.user import UserCallbackMiddleware, UserMessageMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
config_path = os.path.join(project_dir, "conf", "config.yaml")
config = OmegaConf.load(config_path)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error(msg="BOT_TOKEN is not set in the environment variables.")
    exit(1)


def start_bot():
    logger.info(f"Starting {config.name} v{config.version}")

    bot = telebot.TeleBot(BOT_TOKEN, use_class_middlewares=True)

    # handlers
    apps.register_handlers(bot)
    admin.register_handlers(bot)

    # middlewares
    if config.antiflood.enabled:
        logger.info(f"Antiflood middleware enabled with time window: {config.antiflood.time_window_seconds} seconds")
        bot.setup_middleware(AntifloodMiddleware(bot, config.antiflood.time_window_seconds))
    bot.setup_middleware(StateMiddleware(bot))
    bot.setup_middleware(UserMessageMiddleware(bot))
    bot.setup_middleware(UserCallbackMiddleware(bot))

    # Add custom filters
    bot.add_custom_filter(telebot.custom_filters.StateFilter(bot))

    logger.info(f"Bot {bot.get_me().username} has started")
    bot.infinity_polling(timeout=190)
