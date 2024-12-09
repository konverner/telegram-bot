import logging
import random
from datetime import datetime
from typing import Any, Optional

import pytz  # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler
from omegaconf import OmegaConf
from telebot import TeleBot
from telebot.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from telegram_bot.api.handlers.common import create_cancel_button
from telegram_bot.db import crud
from telegram_bot.db.models import User

config = OmegaConf.load("./src/telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/telegram_bot/conf/admin/public_message.yaml")

# Define timezone
timezone = pytz.timezone(config.timezone)

# Initialize scheduler
scheduler = BackgroundScheduler()

# Dictionary to store user data during message scheduling
user_data: dict[str, Any] = {}

# Data structure to store scheduled messages
scheduled_messages: dict[str, dict] = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_keyboard_markup(lang: str) -> InlineKeyboardMarkup:
    """Create an InlineKeyboardMarkup object for the public message menu"""
    keyboard_markup = InlineKeyboardMarkup()
    for option in strings[lang].menu.options:
        keyboard_markup.add(InlineKeyboardButton(option.label, callback_data=option.value))
    return keyboard_markup


def send_scheduled_message(
    bot: TeleBot,
    user_id: int,
    media_type: str,
    message_id: str,
    message_text: Optional[str] = None,
    message_photo: Optional[str] = None,
):
    """Send a scheduled message to a user"""
    try:
        if media_type == "text":
            bot.send_message(chat_id=user_id, text=message_text)
        elif media_type == "photo":
            bot.send_photo(chat_id=user_id, caption=message_text or "", photo=message_photo, disable_notification=False)

        # Remove message from scheduled_messages
        if message_id in scheduled_messages:
            del scheduled_messages[message_id]

    except Exception as e:
        logger.error(f"Error sending scheduled message to {user_id}: {e}")


def list_scheduled_messages(bot: TeleBot, user: User):
    """List all scheduled messages"""
    if not scheduled_messages:
        bot.send_message(user.id, strings[user.lang].no_scheduled_messages)
        return

    response = strings[user.lang].list_public_messages + "\n"
    for message_id, message_data in scheduled_messages.items():
        scheduled_time = message_data["datetime"].strftime("%Y-%m-%d %H:%M")
        response += f"- {message_id}: {scheduled_time} ({config.timezone})\n"
    bot.send_message(user.id, response)


def cancel_scheduled_message(bot: TeleBot, user: User):
    """Cancel a scheduled message"""
    if not scheduled_messages:
        bot.send_message(user.id, strings[user.lang].no_scheduled_messages)
        return

    # Create keyboard for cancel options
    keyboard = InlineKeyboardMarkup()
    for message_id, message in scheduled_messages.items():
        job_label = f"{message_id}: {message['datetime'].strftime('%Y-%m-%d %H:%M')}"
        keyboard.add(InlineKeyboardButton(job_label, callback_data=f"cancel_{message_id}"))

    bot.send_message(user.id, strings[user.lang].cancel_message_prompt, reply_markup=keyboard)


def get_message_content(message, bot: TeleBot, user: User):
    """Get the message content and schedule the message"""
    try:
        media_type = "text" if message.text else "photo"
        content = message.text or message.caption or ""
        photo = message.photo[-1].file_id if message.photo else None

        scheduled_datetime = user_data[user.id]["datetime"]

        message_id = str(random.randint(100, 999))
        scheduled_messages[message_id] = {
            "id": message_id,
            "datetime": scheduled_datetime,
            "content": content,
            "media_type": media_type,
            "photo": photo,
            "jobs": [],
        }
        target_users = crud.read_users()
        for target_user in target_users:
            job = scheduler.add_job(
                send_scheduled_message,
                "date",
                run_date=scheduled_datetime,
                args=[bot, target_user.id, media_type, message_id, content, photo],
            )
            scheduled_messages[message_id]["jobs"].append(job.id)

        bot.send_message(
            user.id,
            strings[user.lang].message_scheduled_confirmation.format(
                message_id=message_id,
                n_users=len(target_users),
                send_datetime=scheduled_datetime.strftime("%Y-%m-%d %H:%M"),
                timezone=config.timezone,
            ),
        )
    finally:
        user_data.pop(user.id, None)


def register_handlers(bot: TeleBot):
    """Register public message handlers"""
    logger.info("Registering `public message` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "public_message")
    def query_handler(call: CallbackQuery, data: dict):
        user = data["user"]

        # Replace the message with the menu
        bot.edit_message_text(
            strings[user.lang].menu.title,
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_keyboard_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "schedule_public_message")
    def create_public_message_handler(call: CallbackQuery, data: dict):
        user = data["user"]

        # Replace the message with the menu
        sent_message = bot.edit_message_text(
            strings[user.lang].enter_datetime_prompt.format(timezone=config.timezone),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_cancel_button(user.lang),
        )

        bot.register_next_step_handler(sent_message, get_datetime_input, bot, user)

    @bot.callback_query_handler(func=lambda call: call.data == "list_scheduled_messages")
    def list_scheduled_messages_handler(call: CallbackQuery, data: dict):
        user = data["user"]
        list_scheduled_messages(bot, user)

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_scheduled_message")
    def cancel_scheduled_message_handler(call: CallbackQuery, data: dict):
        user = data["user"]
        cancel_scheduled_message(bot, user)

    def get_datetime_input(message: Message, bot: TeleBot, user: User):
        try:
            user_datetime = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            user_datetime_localized = timezone.localize(user_datetime)

            if user_datetime_localized < datetime.now(timezone):
                sent_message = bot.send_message(user.id, strings[user.lang].past_datetime_error)
                sent_message = bot.send_message(
                    message.chat.id,
                    strings[user.lang].enter_datetime_prompt.format(timezone=config.timezone),
                    reply_markup=create_cancel_button(user.lang),
                )
                bot.register_next_step_handler(sent_message, get_datetime_input, bot, user)
                return

            user_data[user.id] = {"datetime": user_datetime_localized}
            sent_message = bot.send_message(user.id, strings[user.lang].record_message_prompt)
            bot.register_next_step_handler(sent_message, get_message_content, bot, user)

        except ValueError:
            sent_message = bot.send_message(user.id, strings[user.lang].invalid_datetime_format)
            sent_message = bot.send_message(
                message.chat.id,
                strings[user.lang].enter_datetime_prompt.format(timezone=config.timezone),
                reply_markup=create_cancel_button(user.lang),
            )
            bot.register_next_step_handler(sent_message, get_datetime_input, bot, user)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("cancel_"))
    def handle_cancel_callback(call: CallbackQuery, data: dict):
        """Handle cancel callback"""
        user = data["user"]
        callback_data = call.data

        message_id = callback_data.replace("cancel_", "")
        if message_id in scheduled_messages:
            message_data = scheduled_messages[message_id]
            for job_id in message_data["jobs"]:
                try:
                    scheduler.remove_job(job_id)
                except Exception as e:
                    logger.error(f"Error removing job {job_id}: {e}")
            del scheduled_messages[message_id]
            bot.send_message(
                call.message.chat.id, strings[user.lang].cancel_message_confirmation.format(message_id=message_id)
            )
        else:
            bot.send_message(call.message.chat.id, strings[user.lang].message_not_found)


scheduler.start()
