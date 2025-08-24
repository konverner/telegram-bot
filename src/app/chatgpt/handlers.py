import logging
from pathlib import Path

from omegaconf import OmegaConf
from sqlalchemy.orm import Session
from telebot.states import State
from telebot.states.sync.context import StateContext, StatesGroup
from telebot.types import CallbackQuery, Message
from telebot.util import is_command

from .service import ChatGptService

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings

# Initialize OpenAI service
chatgpt_service = ChatGptService(config.app)


class ChatGptStates(StatesGroup):
    awaiting = State()


def register_handlers(bot):
    """Register handlers for the chat bot."""
    # Provide bot to the service
    chatgpt_service.set_bot(bot)

    @bot.callback_query_handler(func=lambda call: call.data == "chatgpt")
    def handle_chatgpt_callback(call: CallbackQuery, data: dict):
        user = data["user"]
        bot.send_message(call.message.chat.id, strings[user.lang].start)
        state = StateContext(call, bot)
        state.set(ChatGptStates.awaiting)

    @bot.message_handler(
        func=lambda message: not is_command(message.text),
        state=ChatGptStates.awaiting,
        content_types=["text", "photo", "document", "audio", "voice"],
    )
    def handle_template_document(message: Message, data: dict) -> None:
        user = data["user"]
        db_session: Session = data.get("db_session")

        try:
            if message.content_type == "document":
                chatgpt_service.handle_document(message, user, db_session)
            elif message.content_type == "photo":
                logger.info("Handling photo")
                chatgpt_service.handle_photo(message, user, db_session)
            elif message.content_type == "text":
                chatgpt_service.handle_text(message, user, db_session)
            else:
                bot.reply_to(message, strings[user.lang].unsupported_message_type)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if "Cannot preprocess image" in str(e):
                bot.reply_to(message, strings[user.lang].no_image_support)
            else:
                bot.reply_to(message, strings[user.lang].error)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if "Cannot preprocess image" in str(e):
                bot.reply_to(message, strings[user.lang].no_image_support)
            else:
                bot.reply_to(message, strings[user.lang].error)
