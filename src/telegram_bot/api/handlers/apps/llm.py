import logging
from typing import Optional

from markitdown import MarkItDown
from omegaconf import OmegaConf
from PIL import Image
from telebot import TeleBot
from telebot.states import State, StatesGroup
from telebot.types import CallbackQuery, Message
from telebot.util import is_command
from telegram_bot.core.llm import LLM
from telegram_bot.core.utils import download_file_in_memory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MarkItDown
markitdown = MarkItDown()

# Load configurations
config = OmegaConf.load("./src/telegram_bot/conf/apps/llm.yaml")


class LLMStates(StatesGroup):
    """States for the LLM app"""

    awaiting_query = State()


def register_handlers(bot: TeleBot):
    """Register LLM handlers"""
    logger.info("Registering LLM handlers")

    @bot.callback_query_handler(func=lambda call: call.data == "llm")
    def llm_prompt(call: CallbackQuery, data: dict):
        user = data["user"]
        bot.send_message(user.id, config.strings[user.lang].hello)

        # Set state
        data["state"].set(LLMStates.awaiting_query)

    @bot.message_handler(
        func=lambda message: not is_command(message.text),
        content_types=["text", "photo", "document"],
        state=LLMStates.awaiting_query,
    )
    def invoke_chatbot(message: Message, data: dict):
        user = data["user"]
        try:
            if message.content_type == "document":
                handle_document(message)
            elif message.content_type == "photo":
                handle_photo(message)
            elif message.content_type == "text":
                handle_text(message)
            else:
                bot.reply_to(message, "Unsupported content type.")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if "Cannot preprocess image" in str(e):
                bot.reply_to(message, config.strings[user.lang].no_image_support)
            else:
                bot.reply_to(message, config.strings[user.lang].error)

        finally:
            # Remove state
            data["state"].delete()

    def handle_photo(message: Message):
        user_id = int(message.chat.id)
        user_message = message.caption if message.caption else ""
        image = None

        # Download the file
        file_object = download_file_in_memory(bot, message.photo[-1].file_id)
        image = Image.open(file_object)

        process_message(user_id, user_message, image)

    def handle_document(message: Message):
        user_id = int(message.chat.id)
        user_message = message.caption if message.caption else ""

        file_object = download_file_in_memory(bot, message.document.file_id)

        try:
            result = markitdown.convert_stream(file_object)
            user_message += "\n" + result.text_content
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            bot.reply_to(message, "An error occurred while processing your file.")
            return

        process_message(user_id, user_message)

    def handle_text(message: Message):
        user_id = int(message.chat.id)
        user_message = message.text
        process_message(user_id, user_message)

    def process_message(user_id: int, user_message: str, image: Optional[str] = None):
        # Truncate the user's message
        user_message = user_message[: config.app.max_input_length]

        # Load the LLM model
        llm = LLM(config.app.custom)
        logger.info(f"Loaded LLM model with config: {config.app.custom}")

        if llm.config.stream:
            # Inform the user about processing
            sent_msg = bot.send_message(user_id, "...")
            accumulated_response = ""

            # Generate response and send chunks
            for idx, chunk in enumerate(llm.invoke(user_message, image=image)):
                accumulated_response += chunk.content
                if idx % 20 == 0:
                    try:
                        bot.edit_message_text(accumulated_response, chat_id=user_id, message_id=sent_msg.message_id)
                    except Exception as e:
                        logger.error(f"Failed to edit message: {e}")
                        continue
                if idx > 200:
                    break
            bot.edit_message_text(
                accumulated_response.replace("<end_of_turn>", ""), chat_id=user_id, message_id=sent_msg.message_id
            )
        else:
            # Generate and send the final response
            response = llm.invoke(user_message, image=image)
            bot.send_message(user_id, response)
