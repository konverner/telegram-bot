from omegaconf import OmegaConf
from telebot.types import Message

# load config from strings.yaml
strings = OmegaConf.load("./src/telegram_bot/conf/welcome.yaml")


def register_handlers(bot):
    """Register welcome handlers"""

    @bot.message_handler(commands=["start"])
    def send_welcome(message: Message, data: dict):
        user = data["user"]
        bot.reply_to(message, strings[user.lang].hello.format(name=user.name))
