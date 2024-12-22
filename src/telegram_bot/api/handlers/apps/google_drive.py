import logging
import os
import re
import tempfile

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup
from telebot.states.sync.context import StateContext
from telegram_bot.core.google_drive import GoogleDriveService

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

config = OmegaConf.load("./src/telegram_bot/conf/apps/google_drive.yaml")
strings = config.strings

# Initialize Google Drive service
google_drive_service = GoogleDriveService()


# Define States
class GoogleDriveState(StatesGroup):
    awaiting_for_file = State()


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_\-\.]", "_", filename)


def register_handlers(bot: TeleBot):
    """Register resource handlers"""
    logger.info("Registering resource handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "google_drive")
    def google_drive(call: types.CallbackQuery, data: dict):
        user = data["user"]

        # Set state
        data["state"].set(GoogleDriveState.awaiting_for_file)

        bot.send_message(call.message.chat.id, strings[user.lang].ask_for_file)

    @bot.message_handler(
        content_types=["document", "photo", "video", "audio"], state=GoogleDriveState.awaiting_for_file
    )
    def handle_file_upload(message: types.Message, data: dict):
        user = data["user"]
        state = StateContext(message, bot)

        temp_path = None
        try:
            if message.content_type == "photo":
                file_object = message.photo[-1]
            elif message.content_type == "video":
                file_object = message.video
            elif message.content_type == "audio":
                file_object = message.audio
            elif message.content_type == "document":
                file_object = message.document
            else:
                bot.send_message(message.chat.id, strings[user.lang].unsupported_file_type)
                return

            file_info = bot.get_file(file_object.file_id)

            handle, temp_path = tempfile.mkstemp()
            with os.fdopen(handle, "wb") as temp_file:
                downloaded_file = bot.download_file(file_info.file_path)
                temp_file.write(downloaded_file)

            if message.content_type == "document":
                sanitized_filename = sanitize_filename(file_object.file_name)
            else:
                sanitized_filename = file_info.file_path

            folder_id = google_drive_service.get_folder_id(str(message.from_user.id))
            if not folder_id:
                folder = google_drive_service.create_folder(str(message.from_user.id))
                folder_id = folder["id"]

            uploaded_file = google_drive_service.upload_file(temp_path, folder_id, sanitized_filename)
            file_link = f"https://drive.google.com/file/d/{uploaded_file['id']}/view?usp=sharing"
            bot.send_message(message.chat.id, strings[user.lang].positive_result.format(file_link=file_link))

        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            bot.send_message(message.chat.id, strings[user.lang].negative_result.format(e))
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.error(f"Error deleting temporary file: {e}")

        # Remove state
        data["state"].delete()
