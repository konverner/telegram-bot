import logging
import os

from telebot.types import Message

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def register_handlers(bot):
    @bot.message_handler(content_types=["voice", "audio"])
    def get_audio_messages(message: Message, data: dict):
        user = data["user"]
        if message.voice:
            file_info = bot.get_file(message.voice.file_id)
        elif message.audio:
            file_info = bot.get_file(message.audio.file_id)
        else:
            return
        downloaded_file = bot.download_file(file_info.file_path)

        for file_type in ("voice", "audio"):
            if not os.path.exists(f"./tmp/{user.id}/{file_type}"):
                os.makedirs(f"./tmp/{user.id}/{file_type}")
        with open(f"./tmp/{user.id}/{file_info.file_path}", "wb") as new_file:
            new_file.write(downloaded_file)

        bot.send_message(message.chat.id, "Your audio message has been received and saved.")
