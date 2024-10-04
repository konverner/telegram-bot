import logging
import os
from telegram_bot.db import crud
from telegram_bot.service.app import App

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = App("parameter")

def register_handlers(bot):
    @bot.message_handler(content_types=['voice', 'audio'])
    def get_audio_messages(message):
        user_id = message.from_user.id
        username = message.from_user.username
        user_message = message.text

        logger.info(
            msg="User event",
            extra={
                "user_id": user_id,
                "username": username,
                "user_message": user_message
                }
            )

        user = crud.get_user(user_id)
        if not user:
            user = crud.upsert_user(user_id, username)
        if message.voice:
            file_info = bot.get_file(message.voice.file_id)
        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)
        else:
            return
        downloaded_file = bot.download_file(file_info.file_path)

        for file_type in ("voice", "audio"):
            if not os.path.exists(f"./tmp/{user_id}/{file_type}"):
                os.makedirs(f"./tmp/{user_id}/{file_type}")
        with open(f"./tmp/{user_id}/{file_info.file_path}", 'wb') as new_file:
            new_file.write(downloaded_file)

        bot.send_message(
            message.chat.id,
            "Your audio message has been received and saved."
        )
