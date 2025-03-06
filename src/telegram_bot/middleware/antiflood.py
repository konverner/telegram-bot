from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware, CancelUpdate


class AntifloodMiddleware(BaseMiddleware):
    def __init__(self, bot: TeleBot, limit: int) -> None:
        """Middleware to prevent flooding
        Args:
            bot (TeleBot): TeleBot instance
            limit (int): Limit in seconds
        """
        self.bot = bot
        self.last_time: dict[str, str] = {}
        self.limit = limit
        self.update_types = ["message"]
        # Always specify update types, otherwise middlewares won't work

    def pre_process(self, message, data):
        if message.from_user.id not in self.last_time:
            # User is not in a dict, so lets add and cancel this function
            self.last_time[message.from_user.id] = message.date
            return
        if message.date - self.last_time[message.from_user.id] < self.limit:
            # User is flooding
            self.bot.send_message(message.chat.id, "You are making request too often")
            return CancelUpdate()
        self.last_time[message.from_user.id] = message.date

    def post_process(self, message, data, exception):
        pass
