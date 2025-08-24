import json
import logging
from datetime import datetime

from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware
from telebot.types import CallbackQuery, Message

from ..users.service import upsert_user

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class UserMessageMiddleware(BaseMiddleware):
    """Middleware to log user messages"""

    def __init__(self, bot: TeleBot) -> None:
        """Initialize the middleware."""
        self.bot = bot
        self.update_types = ["message"]

    def pre_process(self, message: Message, data: dict):
        """Pre-process the message"""

        db_session = data["db_session"]
        user = upsert_user(
            db_session,
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
        )

        # Check if user is blocked
        if user.is_blocked:
            self.bot.send_message(user.id, "You have been blocked from using this bot.")
            self.bot.answer_callback_query(message.id, "You have been blocked from using this bot.")
            return

        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": user.id,
            "event_type": "message",
            "state": data["state"].get(),
            "content": message.text,
            "content_type": message.content_type,
        }

        logger.info(json.dumps(event, ensure_ascii=False))

        # Set the user data to the data dictionary
        data["user"] = user

    def post_process(self, message, data, exception):
        """Post-process the message"""
        pass


class UserCallbackMiddleware(BaseMiddleware):
    """Middleware to log user callbacks"""

    def __init__(self, bot: TeleBot) -> None:
        """Initialize the middleware."""
        self.bot = bot
        self.update_types = ["callback_query"]

    def pre_process(self, callback_query: CallbackQuery, data: dict):
        """Pre-process the callback query"""
        db_session = data["db_session"]
        user = upsert_user(
            db_session,
            user_id=callback_query.from_user.id,
            username=callback_query.from_user.username,
            first_name=callback_query.from_user.first_name,
            last_name=callback_query.from_user.last_name,
        )

        # Check if user is blocked
        if user.is_blocked:
            self.bot.send_message(user.id, "You have been blocked from using this bot.")
            self.bot.answer_callback_query(callback_query.id, "You have been blocked from using this bot.")
            return

        event = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "user_id": user.id,
            "event_type": "callback",
            "state": data["state"].get(),
            "content": callback_query.data,
            "content_type": "callback_data",
        }
        logger.info(json.dumps(event, ensure_ascii=False))

        # Set the user data to the data dictionary
        data["user"] = user

    def post_process(self, callback_query, data, exception):
        """Post-process the callback query"""
        pass
