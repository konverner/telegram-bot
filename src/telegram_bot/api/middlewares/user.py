import logging

from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware
from telebot.types import CallbackQuery, Message

from db import crud

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserMessageMiddleware(BaseMiddleware):
    """Middleware to log user messages"""

    def __init__(self, bot: TeleBot) -> None:
        self.bot = bot
        self.update_types = ["message"]

    def pre_process(self, message: Message, data: dict):
        """Pre-process the message"""
        user = crud.upsert_user(
            id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )
        event = crud.create_event(
            user_id=user.id, content=message.text, content_type=message.content_type,
            event_type="message", state=data["state"].get()
        )

        # Log event to the console
        logger.info(event.dict())

        # Set the user data to the data dictionary
        data["user"] = user

    def post_process(self, message, data, exception):
        pass


class UserCallbackMiddleware(BaseMiddleware):
    """Middleware to log user callbacks"""
    def __init__(self, bot: TeleBot) -> None:
        self.bot = bot
        self.update_types = ["callback_query"]

    def pre_process(self, callback_query: CallbackQuery, data: dict):
        """Pre-process the callback query"""

        user = crud.upsert_user(
            id=callback_query.from_user.id,
            username=callback_query.from_user.username,
            first_name=callback_query.from_user.first_name,
            last_name=callback_query.from_user.last_name,
        )
        event = crud.create_event(
            user_id=user.id, content=callback_query.data, content_type="callback_data",
            event_type="callback", state=data["state"].get()
        )

        # Log event to the console
        logger.info(event.dict())

        # Set the user data to the data dictionary
        data["user"] = user

    def post_process(self, callback_query, data, exception):
        pass
