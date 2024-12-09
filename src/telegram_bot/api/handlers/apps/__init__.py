from telebot import TeleBot

from telegram_bot.api.handlers.apps import audio, resource


def register_handlers(bot: TeleBot):
    resource.register_handlers(bot)
    audio.register_handlers(bot)

