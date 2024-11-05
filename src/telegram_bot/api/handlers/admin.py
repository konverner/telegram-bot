import logging
import logging.config
import os
from datetime import datetime

import pytz  # type: ignore
from apscheduler.schedulers.background import BackgroundScheduler
from omegaconf import OmegaConf
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram_bot.db import crud

config = OmegaConf.load("./src/telegram_bot/conf/config.yaml")
strings = OmegaConf.load("./src/telegram_bot/conf/strings.yaml")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define Paris timezone
timezone = pytz.timezone(config.timezone)

# Initialize the scheduler
scheduler = BackgroundScheduler()

# Dictionary to store user data during message scheduling
user_data = {}

def create_admin_menu_markup(strings, lang) -> InlineKeyboardMarkup:
    menu_markup = InlineKeyboardMarkup(row_width=1)
    menu_markup.add(
        InlineKeyboardButton(strings.admin_menu.send_message[lang], callback_data="_public_message"),
        InlineKeyboardButton(strings.admin_menu.add_admin[lang], callback_data="_add_admin"),
        InlineKeyboardButton(strings.admin_menu.export_data[lang], callback_data="_export_data"),
    )
    return menu_markup


# Function to send a scheduled message
def send_scheduled_message(bot, chat_id, message_text):
    bot.send_message(chat_id, message_text)


# React to any text if not command
def register_handlers(bot):
    @bot.message_handler(commands=["admin"])
    def admin_menu_command(message: Message, data: dict):
        user = data["user"]
        print(user.__dict__)
        if user.role != "admin":
            # Inform the user that they do not have admin rights
            bot.send_message(message.from_user.id, strings.no_rights[user.lang])
            return

        # Send the admin menu
        bot.send_message(
            message.from_user.id, strings.admin_menu.title[user.lang],
            reply_markup=create_admin_menu_markup(strings, user.lang)
        )

    @bot.callback_query_handler(func=lambda call: call.data == "_public_message")
    def query_handler(call):
        user_id = call.from_user.id
        user = crud.get_user(call.from_user.username)

        if user.role != "admin":
            # Inform that the user does not have admin rights
            bot.send_message(user_id, strings.no_rights[user.lang])
            return

        # Ask user to provide the date and time
        sent_message = bot.send_message(user_id, strings.enter_datetime_prompt[user.lang])
        # Move to the next step: receiving the datetime input
        bot.register_next_step_handler(sent_message, get_datetime_input, bot, user_id, user.lang)

    # Handler to capture the datetime input from the user
    def get_datetime_input(message, bot, user_id, lang):
        user_input = message.text
        try:
            # Parse the user's input into a datetime object
            user_datetime_obj = datetime.strptime(user_input, '%Y-%m-%d %H:%M')
            user_datetime_localized = timezone.localize(user_datetime_obj)

            # Store the datetime and move to the next step (waiting for the message content)
            user_data[user_id] = {'datetime': user_datetime_localized}
            bot.send_message(user_id, strings.record_message_prompt)

            # Move to the next step: receiving the custom message
            bot.register_next_step_handler(message, get_message_content, bot, user_id, lang)

        except ValueError:
            # Handle invalid date format
            bot.send_message(user_id, strings.invalid_datetime_format)
            # Prompt the user again
            bot.register_next_step_handler(message, get_datetime_input, bot, user_id, lang)

    # Handler to capture the custom message from the user
    def get_message_content(message, bot, user_id, lang):
        user_message = message.text

        # Retrieve the previously stored datetime
        scheduled_datetime = user_data[user_id]['datetime']

        # Schedule the message for the specified datetime
        users = crud.get_users()
        for user in users:
            print(user.user_id)
            scheduler.add_job(
                send_scheduled_message, 'date',
                run_date=scheduled_datetime,
                args=[bot, user.user_id, user_message]
        )

        # Inform the user that the message has been scheduled
        response = strings.message_scheduled_confirmation.format(
            n_users = len(users),
            send_datetime = scheduled_datetime.strftime('%Y-%m-%d %H:%M'),
            timezone = config.timezone
        )
        bot.send_message(user_id, response)

        # Clear the user data to avoid confusion
        del user_data[user_id]

    @bot.callback_query_handler(func=lambda call: call.data == "_export_data")
    def export_data_handler(call):
        user_id = call.from_user.id
        user = crud.get_user(call.from_user.username)

        if user.role != "admin":
            # inform that the user does not have rights
            bot.send_message(call.from_user.id, strings.no_rights)
            return

        # Export data
        tables = ['messages', 'users']
        export_dir = f'./data/{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        os.makedirs(export_dir)
        try:
            crud.export_all_tables(export_dir)
            for table in tables:
                # save as excel in temp folder and send to a user
                filename = f"{export_dir}/{table}.csv"
                bot.send_document(user_id, open(filename, 'rb'))
                # remove the file
                os.remove(filename)
        except Exception as e:
            bot.send_message(user_id, str(e))
            logger.error(f"Error exporting data: {e}")


# Start the scheduler
scheduler.start()

