import logging

from telegram_bot.db import crud
from telegram_bot.service.app import App

logger = logging.getLogger(__name__)
app = App("parameter")


def register_handlers(bot):

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        username = message.from_user.username
        user_message = message.text

        logger.info(
            msg="User event",
            extra={
                "user_id": user_id,
                "username": username,
                "user_message": user_message
                }
            )

        user = crud.get_user(user_id)
        if not user:
            user = crud.upsert_user(user_id, username)

        response = app.run(message.text)
        bot.reply_to(message, response)
