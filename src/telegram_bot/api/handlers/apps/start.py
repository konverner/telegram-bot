import logging.config
import os

from omegaconf import OmegaConf
from telebot.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configurations
project_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
config_path = os.path.join(project_dir, "conf" , "apps", "start.yaml")
config = OmegaConf.load(config_path)
strings = config.strings


def register_handlers(bot):
    """Register menu handlers"""
    logger.info("Registering `start` handlers")

    @bot.message_handler(commands=["start"])
    def menu_menu_command(message: Message, data: dict):
        user = data["user"]

        bot.send_message(message.chat.id, strings[user.lang].description)
