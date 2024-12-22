from telebot import TeleBot
from telegram_bot.api.handlers.apps import audio, google_drive, llm, menu, resource


def register_handlers(bot: TeleBot):
    resource.register_handlers(bot)
    audio.register_handlers(bot)
    llm.register_handlers(bot)
    google_drive.register_handlers(bot)
    menu.register_handlers(bot)
