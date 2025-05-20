import logging
from pathlib import Path
from typing import Optional

from omegaconf import OmegaConf
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from ..auth.models import User


# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings

# Logging
# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# def send_scheduled_message(
#     bot: TeleBot,
#     user_id: int,
#     media_type: str,
#     message_text: Optional[str] = None,
#     message_photo: Optional[str] = None
# ):
#     """Send a scheduled message to a user"""
#     try:
#         logger.info(f"Sending scheduled message to {user_id}")
#         if media_type == "text":
#             bot.send_message(chat_id=user_id, text=message_text)
#         elif media_type == "photo":
#             bot.send_photo(chat_id=user_id, caption=message_text or "", photo=message_photo, disable_notification=False)

#     except Exception as e:
#         logger.error(f"Error sending scheduled message to {user_id}: {e}")


def send_scheduled_message(
    bot: TeleBot,
    user_id: int,
    media_type: str,
    message_text: Optional[str] = None,
    message_photo: Optional[str] = None,
):
    """Send a scheduled message to a user"""
    if media_type == "text":
        print(f"Sending scheduled message: {message_text}")
        bot.send_message(user_id, message_text)
    if media_type == "photo":
        bot.send_photo(
            chat_id=user_id,
            caption=message_text or "",
            photo=message_photo,
            disable_notification=False,
        )


def list_scheduled_messages(
    bot: TeleBot, user: User, scheduled_messages: dict[str, dict]
):
    """List all scheduled messages"""
    if not scheduled_messages:
        bot.send_message(user.id, strings[user.lang].no_scheduled_messages)
        return

    response = strings[user.lang].list_public_messages + "\n"
    for message_id, message_data in scheduled_messages.items():
        scheduled_time = message_data["datetime"].strftime("%Y-%m-%d %H:%M")
        response += f"- {message_id}: {scheduled_time} ({config.app.timezone})\n"
    bot.send_message(user.id, response)


def cancel_scheduled_message(
    bot: TeleBot, user: User, scheduled_messages: dict[str, dict]
):
    """Cancel a scheduled message"""
    if not scheduled_messages:
        bot.send_message(user.id, strings[user.lang].no_scheduled_messages)
        return

    # Create keyboard for cancel options
    keyboard = InlineKeyboardMarkup()
    for message_id, message in scheduled_messages.items():
        job_label = f"{message_id}: {message['datetime'].strftime('%Y-%m-%d %H:%M')}"
        keyboard.add(
            InlineKeyboardButton(job_label, callback_data=f"cancel_{message_id}")
        )

    bot.send_message(
        user.id, strings[user.lang].cancel_message_prompt, reply_markup=keyboard
    )
