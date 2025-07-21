import logging
from pathlib import Path
from typing import Optional

from markitdown import MarkItDown
from omegaconf import OmegaConf
from PIL import Image
from sqlalchemy.orm import Session
from telebot.states import State
from telebot.states.sync.context import StateContext, StatesGroup
from telebot.types import CallbackQuery, Message
from telebot.util import is_command

from ..auth.models import User
from ..plugins.openai import schemas as openai_schemas
from ..plugins.openai.client import LLM
from ..plugins.openai.utils import download_file_in_memory
from .service import create_message, read_chat_history

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Initialize MarkItDown
markitdown = MarkItDown()

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


class ChatGptStates(StatesGroup):
    awaiting = State()


def register_handlers(bot):
    """Register handlers for the app_template_document."""

    @bot.callback_query_handler(func=lambda call: call.data == "chatgpt")
    def handle_chatgpt_callback(call: CallbackQuery, data: dict):
        user = data["user"]
        bot.send_message(call.message.chat.id, strings[user.lang].start)

        state = StateContext(call, bot)
        state.set(ChatGptStates.awaiting)

    @bot.message_handler(
        state=ChatGptStates.awaiting,
        func=lambda message: not is_command(message.text),
    )
    def handle_chatgpt_input(message: Message, data: dict) -> None:
        user = data["user"]
        db_session = data["db_session"]

        try:
            if message.content_type == "document":
                handle_document(message, user, db_session)
            elif message.content_type == "photo":
                logger.info("Handling photo")
                handle_photo(message, user, db_session)
            elif message.content_type == "text":
                handle_text(message, user, db_session)
            else:
                bot.reply_to(message, strings[user.lang].unsupported_message_type)
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            if "Cannot preprocess image" in str(e):
                bot.reply_to(message, strings[user.lang].no_image_support)
            else:
                bot.reply_to(message, strings[user.lang].error)

            # Delete state
            state = StateContext(message, bot)
            state.delete()

    def handle_photo(message: Message, user: User, db_session: Session):
        user_id = int(message.chat.id)
        user_message = message.caption if message.caption else ""
        image = None

        # Download the file
        file_object = download_file_in_memory(bot, message.photo[-1].file_id)
        image = Image.open(file_object)

        process_message(user_id, user_message, user, image, db_session)

    def handle_document(message: Message, user: User, db_session: Session):
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

        process_message(user_id, user_message, user, db_session)

    def handle_text(message: Message, user: User, db_session: Session):
        user_id = int(message.chat.id)
        user_message = message.text
        process_message(user_id, user_message, user, db_session)

    def process_message(
        user_id: int,
        user_message: str,
        user: User,
        db_session: Session,
        image: Optional[str] = None,
    ):
        # Truncate the user's message
        user_message = user_message[: config.app.max_input_length]

        # Create a message in chat history
        create_message(db_session, user_id, "user", content=user_message)

        # Retrieve chat history
        db_chat_history = read_chat_history(db_session, user_id)

        # Convert chat history to a list of Message objects using model_validate
        openai_chat_history = [
            openai_schemas.Message(
                id=msg.id,
                chat_id=msg.chat_id,
                role=msg.role,
                content=msg.content,
                created_at=msg.created_at,
            )
            for msg in db_chat_history
        ]

        # Load the LLM model
        llm = LLM(config.app.llm, system_prompt=config.app.llm.system_prompt)

        # Generate and send the final response
        logger.info(f"User message: {user_message}")

        if llm.config.stream:
            # Inform the user about processing
            sent_msg = bot.send_message(user_id, "...")
            accumulated_response = ""

            # Generate response and send chunks
            for idx, chunk in enumerate(llm.invoke(openai_chat_history, image=image)):
                accumulated_response += chunk.content
                if idx % 20 == 0:
                    try:
                        bot.edit_message_text(
                            accumulated_response,
                            chat_id=user_id,
                            message_id=sent_msg.message_id,
                        )
                    except Exception as e:
                        logger.error(f"Failed to edit message: {e}")
                        continue
                if idx > 200:
                    continue
            bot.edit_message_text(
                accumulated_response.replace("<end_of_turn>", ""),
                chat_id=user_id,
                message_id=sent_msg.message_id,
            )
            create_message(
                db_session, user_id, "assistant", content=accumulated_response
            )
        else:
            # Generate and send the final response
            response = llm.invoke(openai_chat_history, image=image)
            bot.send_message(user_id, response.response_content)
            create_message(
                db_session, user_id, "assistant", content=response.response_content
            )
