import logging.config

from omegaconf import OmegaConf
from telebot.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = OmegaConf.load("./src/telegram_bot/conf/apps/start.yaml")
strings = config.strings


def register_handlers(bot):
    """Register menu handlers"""
    logger.info("Registering `start` handlers")

    @bot.message_handler(commands=["start"])
    def menu_menu_command(message: Message, data: dict):
        user = data["user"]

        bot.send_message(message.chat.id, strings[user.lang].description)
