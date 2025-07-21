import logging
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from omegaconf import OmegaConf
from telebot import TeleBot
from telebot.types import CallbackQuery, Message

from ..admin.markup import create_admin_menu_markup
from ..auth.service import read_users
from ..markup import create_cancel_button
from .markup import create_keyboard_markup
from .service import (
    cancel_scheduled_message,
    list_scheduled_messages,
    send_scheduled_message,
)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings

# Define timezone
timezone = pytz.timezone(config.app.timezone)

# Initialize and start scheduler
scheduler = BackgroundScheduler(timezone=timezone)
scheduler.start()

# Dictionary to store user data during message scheduling
user_data: dict[str, Any] = {}

# Data structure to store scheduled messages
scheduled_messages: dict[str, dict] = {}

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def register_handlers(bot: TeleBot):
    """Register public message handlers"""
    logger.info("Registering `public message` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "cancel_public_message")
    def cancel(call: CallbackQuery, data: dict):
        user = data["user"]
        data["state"].delete()
        bot.edit_message_text(
            strings[user.lang].operation_cancelled,
            call.message.chat.id,
            call.message.message_id,
        )

        # Send the main menu
        bot.send_message(
            call.message.chat.id,
            strings[user.lang].main_menu,
            reply_markup=create_admin_menu_markup(user.lang),
        )

    @bot.callback_query_handler(func=lambda call: call.data == "public_message")
    def query_handler(call: CallbackQuery, data: dict):
        user = data["user"]

        # Replace the message with the menu
        bot.edit_message_text(
            chat_id=user.id,
            message_id=call.message.message_id,
            text=strings[user.lang].menu.title,
            reply_markup=create_keyboard_markup(user.lang),
        )

    @bot.callback_query_handler(
        func=lambda call: call.data == "schedule_public_message"
    )
    def create_public_message_handler(call: CallbackQuery, data: dict):
        user = data["user"]

        # Replace the message with the menu
        sent_message = bot.edit_message_text(
            strings[user.lang].enter_datetime_prompt.format(
                timezone=config.app.timezone,
                datetime_example=datetime.now(timezone).strftime("%Y-%m-%d %H:%M"),
            ),
            call.message.chat.id,
            call.message.message_id,
            reply_markup=create_cancel_button(user.lang),
            parse_mode="Markdown",
        )

        bot.register_next_step_handler(sent_message, get_datetime_input, bot, data)

    @bot.callback_query_handler(
        func=lambda call: call.data == "list_scheduled_messages"
    )
    def list_scheduled_messages_handler(call: CallbackQuery, data: dict):
        user = data["user"]
        list_scheduled_messages(bot, user, scheduled_messages)

    @bot.callback_query_handler(
        func=lambda call: call.data == "cancel_scheduled_message"
    )
    def cancel_scheduled_message_handler(call: CallbackQuery, data: dict):
        user = data["user"]
        cancel_scheduled_message(bot, user, scheduled_messages)

    def get_datetime_input(message: Message, bot: TeleBot, data: dict):
        user = data["user"]
        try:
            user_datetime = datetime.strptime(message.text, "%Y-%m-%d %H:%M")
            user_datetime_localized = timezone.localize(user_datetime)

            if user_datetime_localized < datetime.now(timezone):
                sent_message = bot.send_message(
                    user.id, strings[user.lang].past_datetime_error
                )
                sent_message = bot.send_message(
                    message.chat.id,
                    strings[user.lang].enter_datetime_prompt.format(
                        timezone=config.app.timezone,
                        datetime_example=datetime.now(timezone).strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                    ),
                    reply_markup=create_cancel_button(user.lang),
                    parse_mode="Markdown",
                )
                bot.register_next_step_handler(
                    sent_message, get_datetime_input, bot, data
                )
                return

            user_data[user.id] = {"datetime": user_datetime_localized}
            sent_message = bot.send_message(
                user.id, strings[user.lang].record_message_prompt
            )
            bot.register_next_step_handler(
                sent_message, get_message_content, bot, data, user_data, scheduler
            )

        except ValueError:
            sent_message = bot.send_message(
                user.id, strings[user.lang].invalid_datetime_format
            )
            sent_message = bot.send_message(
                message.chat.id,
                strings[user.lang].enter_datetime_prompt.format(
                    timezone=config.app.timezone
                ),
                reply_markup=create_cancel_button(user.lang),
            )
            bot.register_next_step_handler(sent_message, get_datetime_input, bot, data)


def get_message_content(
    message: Message,
    bot: TeleBot,
    data: dict,
    user_data: dict[int, dict],
    scheduler: Any,
):
    """Get the message content and schedule the message"""
    user = data["user"]
    db_session = data["db_session"]
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
        print(f"Created message: {message_id}")

        target_users = read_users(db_session)
        for target_user in target_users:
            # add random delay to avoid spamming
            scheduled_datetime += timedelta(seconds=random.randint(5, 30))

            job = scheduler.add_job(
                send_scheduled_message,
                trigger=DateTrigger(run_date=scheduled_datetime),
                args=[bot, target_user.id, media_type, content, photo],
                misfire_grace_time=10,
            )

            scheduled_messages[message_id]["jobs"].append(job)
        bot.send_message(
            user.id,
            strings[user.lang].message_scheduled_confirmation.format(
                message_id=message_id,
                n_users=len(target_users),
                send_datetime=scheduled_datetime.strftime("%Y-%m-%d %H:%M"),
                timezone=config.app.timezone,
            ),
        )
    finally:
        user_data.pop(user.id, None)

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
                call.message.chat.id,
                strings[user.lang].cancel_message_confirmation.format(
                    message_id=message_id
                ),
            )
        else:
            bot.send_message(call.message.chat.id, strings[user.lang].message_not_found)
