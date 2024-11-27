import logging

from omegaconf import OmegaConf
from telebot.types import Message

from telegram_bot.db.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# load config from strings.yaml
strings = OmegaConf.load("./src/telegram_bot/conf/welcome.yaml")


def register_handlers(bot):
    @bot.message_handler(commands=["start"])
    def send_welcome(message: Message, data: User):
        user = data["user"]
        bot.reply_to(message, strings[user.lang].hello.format(name=user.name))
