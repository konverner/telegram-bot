from telebot import TeleBot

from telegram_bot.api.handlers.apps import audio, google_drive, google_sheets, llm, menu, resource, start


def register_handlers(bot: TeleBot):
    start.register_handlers(bot)
    resource.register_handlers(bot)
    audio.register_handlers(bot)
    llm.register_handlers(bot)
    google_drive.register_handlers(bot)
    google_sheets.register_handlers(bot)
    menu.register_handlers(bot)
