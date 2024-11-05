import logging
from typing import Optional
from telebot.handler_backends import BaseMiddleware
from telebot.types import Message

from telegram_bot.db import crud

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.update_types = ['message']

    def pre_process(self, message: Message, data: Optional[dict] = None):
        user = crud.upsert_user(
            id=message.from_user.id,
            name=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
        crud.add_message(
            username=message.from_user.username,
            text=message.text
        )
        logger.info("User event", extra={"user": message.from_user.username, "user_message": message.text})
        if data:
            data['user'] = user

    def post_process(self, message, data, exception):
        pass
