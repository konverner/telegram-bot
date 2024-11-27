import logging
import logging.config
from datetime import datetime

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from omegaconf import OmegaConf
from telebot import types

from telegram_bot.api.handlers.common import create_cancel_button
from telegram_bot.db import crud

config = OmegaConf.load("./src/telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/telegram_bot/conf/admin.yaml")

# Define Paris timezone
timezone = pytz.timezone(config.timezone)

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Dictionary to store user data during message scheduling
user_data = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_keyboard_markup(lang: str) -> types.InlineKeyboardMarkup:
    keyboard_markup = types.InlineKeyboardMarkup()
    for option in strings[lang].public_message.menu.options:
        keyboard_markup.add(types.InlineKeyboardButton(option.label, callback_data=option.value))
    return keyboard_markup

# Function to send a scheduled message
def send_scheduled_message(bot, user_id, media_type, message_text: str = None, message_photo: str = None):
    if media_type == 'text':
        bot.send_message(chat_id=user_id, text=message_text)
    elif media_type == 'photo':
        # Fetch the photo by file ID
        if message_text:
            bot.send_photo(chat_id=user_id, caption=message_text, photo=message_photo, disable_notification=False)
        else:
            bot.send_photo(chat_id=user_id, photo=message_photo, disable_notification=False)


# Function to list all scheduled messages
def list_scheduled_messages(bot, user):
    jobs = scheduler.get_jobs()
    if not jobs:
        bot.send_message(
            user.id,
            strings[user.lang].public_message.no_scheduled_messages
        )
        return

    response = strings[user.lang].public_message.list_public_messages+ "\n"
    for job in jobs:
        job_data = job.args
        scheduled_time = job.next_run_time.strftime('%Y-%m-%d %H:%M')
        response += f"- {scheduled_time} ({config.timezone}): {job_data[2]}\n"

    bot.send_message(user.id, response)


# React to any text if not command
def register_handlers(bot):
    """ Register `public message` handlers """
    logger.info("Registering `public message` handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "public_message")
    def query_handler(call: types.CallbackQuery, data: dict):
        user = data["user"]

        # Show buttons for creating a public message or listing scheduled messages
        bot.send_message(
            user.id, strings[user.lang].public_message.menu.title,
            reply_markup=create_keyboard_markup(user.lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "schedule_public_message")
    def create_public_message_handler(call: types.CallbackQuery, data: dict):
        user = data["user"]

        # Ask user to provide the date and time
        sent_message = bot.send_message(
            user.id, strings[user.lang].public_message.enter_datetime_prompt.format(timezone=config.timezone),
            reply_markup=create_cancel_button(user.lang)
        )
        # Move to the next step: receiving the datetime input
        bot.register_next_step_handler(sent_message, get_datetime_input, bot, user)

    @bot.callback_query_handler(func=lambda call: call.data == "list_scheduled_messages")
    def list_scheduled_messages_handler(call: types.CallbackQuery):
        user = call.from_user
        list_scheduled_messages(bot, user.id)

    # Handler to capture the datetime input from the user
    def get_datetime_input(message, bot, user):
        user_input = message.text
        try:
            # Parse the user's input into a datetime object
            user_datetime_obj = datetime.strptime(user_input, '%Y-%m-%d %H:%M')
            user_datetime_localized = timezone.localize(user_datetime_obj)

            # Check that date is not at the past
            if user_datetime_localized < datetime.now(timezone):
                bot.send_message(user.id, strings.past_datetime_error[user.lang])

                # Prompt the user again
                sent_message = bot.send_message(
                    user.id, strings.enter_datetime_prompt[user.lang].format(timezone=config.timezone),
                    reply_markup=create_cancel_button(user.lang)
                )
                bot.register_next_step_handler(sent_message, get_datetime_input, bot, user)
                return

            # Store the datetime and move to the next step (waiting for the message content)
            user_data[user.id] = {'datetime': user_datetime_localized}
            sent_message = bot.send_message(user.id, strings.record_message_prompt[user.lang], reply_markup=create_cancel_button(strings, user.lang))

            # Move to the next step: receiving the custom message
            bot.register_next_step_handler(sent_message, get_message_content, bot, user)

        except ValueError:
            # Handle invalid date format
            sent_message = bot.send_message(user.id, strings.invalid_datetime_format[user.lang])
            # Prompt the user again
            sent_message = bot.send_message(
                user.id, strings.enter_datetime_prompt[user.lang].format(timezone=config.timezone),
                reply_markup=create_cancel_button(user.lang)
            )
            bot.register_next_step_handler(sent_message, get_datetime_input, bot, user)

    # Handler to capture the custom message from the user
    def get_message_content(message, bot, user):
        user_message = None
        photo_file = None
        if message.text:
            user_message = message.text
            media_type = 'text'
        elif message.photo:
            # Get the highest quality image (last item in the list)
            photo_file = message.photo[-1].file_id
            user_message = message.caption
            media_type = 'photo'

        # Retrieve the previously stored datetime
        scheduled_datetime = user_data[user.id]['datetime']

        # Schedule the message for the specified datetime
        tarread_users = crud.read_users()
        for tarread_user in tarread_users:
            scheduler.add_job(
                send_scheduled_message, 'date',
                run_date=scheduled_datetime, 
                args=[bot, tarread_user.id, media_type, user_message, photo_file]
            )

        # Inform the user that the message has been scheduled
        response = strings.message_scheduled_confirmation[user.lang].format(
            n_users = len(tarread_users),
            send_datetime = scheduled_datetime.strftime('%Y-%m-%d %H:%M'),
            timezone = config.timezone
        )
        bot.send_message(user.id, response)

        # Clear the user data to avoid confusion
        del user_data[user.id]

# Start the scheduler
scheduler.start()
