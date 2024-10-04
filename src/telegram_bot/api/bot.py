import logging
import logging.config
import os

import telebot
from dotenv import find_dotenv, load_dotenv

from telegram_bot.api.handlers import welcome, audio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))  # Load environment variables from .env file
BOT_TOKEN = os.getenv("BOT_TOKEN")

if BOT_TOKEN is None:
    logger.error(msg="BOT_TOKEN is not set in the environment variables.")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

welcome.register_handlers(bot)
audio.register_handlers(bot)

def start_bot():
    logger.info(msg=f"Bot `{str(bot.get_me().username)}` has started")
    #bot.infinity_polling()
    bot.polling()