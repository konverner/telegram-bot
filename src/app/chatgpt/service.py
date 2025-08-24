import logging
from pathlib import Path
from typing import Any, Optional

from markitdown import MarkItDown
from omegaconf import OmegaConf
from PIL import Image as PILImage

from ..plugins.telegram_openai.client import OpenAiClient
from ..plugins.telegram_openai.schemas import ModelConfig
from .models import Chat
from .models import Message as ChatMessage
from .utils import download_file_in_memory

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


class ChatGptService:
    """Service for general conversational replies."""

    def __init__(self, config: dict):
        self.model_config = ModelConfig(**config.llm) if "llm" in config else ModelConfig(**config)
        self.llm = OpenAiClient(config=self.model_config)
        # system_prompt can be at app.system_prompt or just system_prompt depending on how ctor called
        self.system_prompt_template = getattr(config, "system_prompt", None) or getattr(config, "app", {}).get(
            "system_prompt", ""
        )
        self.history_limit = int(getattr(config, "chat_history_limit", None) or config.get("chat_history_limit", 6))
        self.bot: Optional[Any] = None
        self.markitdown = MarkItDown()

    def set_bot(self, bot: Any) -> None:
        self.bot = bot

    def _get_system_prompt(self) -> str:
        return self.system_prompt_template

    def _coerce_text(self, result: Any) -> str:
        # Make best effort to extract a text reply out of various possible return types
        if result is None:
            return ""
        if isinstance(result, str):
            return result
        # Common patterns
        for attr in ("content", "text", "message", "output"):
            if hasattr(result, attr):
                val = getattr(result, attr)
                if isinstance(val, str):
                    return val
        # Fallback to string conversion
        return str(result)

    def generate_reply(self, chat_history: list[dict[str, str]], image: Optional[Any] = None) -> str:
        """
        Generate assistant reply using chat history and optional image.
        chat_history: list of {role: 'user'|'assistant'|'system', content: str}
        image: optional PIL.Image.Image
        """
        # Enforce history limit
        history = chat_history[-self.history_limit :] if self.history_limit else chat_history
        system_prompt = self._get_system_prompt()

        try:
            # Prefer native multi-turn call
            reply_text = self.llm.chat(system_prompt=system_prompt, messages=history, image=image).strip()
            if not reply_text:
                # Fallback: flatten history into a single prompt
                flattened = []
                for m in history:
                    role = m.get("role", "user")
                    content = m.get("content", "")
                    flattened.append(f"{role}: {content}")
                flattened.append("assistant:")
                reply_text = self.llm.chat(system_prompt=system_prompt, user_text="\n".join(flattened)).strip()

            if not reply_text:
                logger.warning("LLM returned empty reply; sending generic fallback.")
                reply_text = "…"
            return reply_text

        except Exception as e:
            logger.error(f"Error generating reply: {e}")
            raise

    # ---- moved from handlers ----

    def get_or_create_chat(self, db_session, user_id: int) -> Chat:
        chat = db_session.query(Chat).filter(Chat.user_id == user_id).first()
        if not chat:
            chat = Chat(user_id=user_id, name=None)
            db_session.add(chat)
            db_session.commit()
            db_session.refresh(chat)
        return chat

    def save_message(self, db_session, chat: Chat, role: str, content: str) -> None:
        msg = ChatMessage(chat_id=chat.id, role=role, content={}.get("content", content) or content)
        db_session.add(msg)
        db_session.commit()

    def get_chat_history(self, db_session, chat: Chat, limit: int) -> list[dict[str, str]]:
        q = db_session.query(ChatMessage).filter(ChatMessage.chat_id == chat.id).order_by(ChatMessage.created_at.asc())
        messages = q.all()
        messages = messages[-limit:] if limit and len(messages) > limit else messages
        return [{"role": m.role, "content": m.content} for m in messages]

    def handle_photo(self, message: Any, user: Any, db_session) -> None:
        assert self.bot is not None, "Bot is not set on ChatGptService. Call set_bot(bot) first."
        user_id = int(message.chat.id)
        user_message = message.caption if message.caption else ""
        file_object = download_file_in_memory(self.bot, message.photo[-1].file_id)
        image = PILImage.open(file_object)
        self.process_message(db_session, user_id, user_message, user, image)

    def handle_document(self, message: Any, user: Any, db_session) -> None:
        assert self.bot is not None, "Bot is not set on ChatGptService. Call set_bot(bot) first."
        user_id = int(message.chat.id)
        user_message = message.caption if message.caption else ""
        file_object = download_file_in_memory(self.bot, message.document.file_id)
        try:
            result = self.markitdown.convert_stream(file_object)
            user_message += ("\n" if user_message else "") + result.text_content
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            self.bot.reply_to(message, strings[user.lang].error)
            return
        self.process_message(db_session, user_id, user_message, user)

    def handle_text(self, message: Any, user: Any, db_session) -> None:
        user_id = int(message.chat.id)
        user_message = message.text
        self.process_message(db_session, user_id, user_message, user)

    def process_message(
        self,
        db_session,
        user_id: int,
        user_message: str,
        user: Any,
        image: Optional[PILImage.Image] = None,
    ) -> None:
        assert self.bot is not None, "Bot is not set on ChatGptService. Call set_bot(bot) first."
        # Truncate the user's message
        user_message = (user_message or "")[: config.app.max_input_length]

        # Persist user message
        chat = self.get_or_create_chat(db_session, user.id)
        self.save_message(db_session, chat, role="user", content=user_message if user_message else "[attachment]")

        # Build recent history for the model
        history = self.get_chat_history(db_session, chat, limit=self.history_limit)

        logger.info(f"User message: {user_message}")

        try:
            reply_text = self.generate_reply(chat_history=history, image=image)
        except Exception as e:
            logger.error(f"Error invoking LLM: {e}")
            self.bot.send_message(user_id, strings[user.lang].error)
            return

        logger.info(f"Response content: {reply_text}")

        # Persist assistant message
        self.save_message(db_session, chat, role="assistant", content=reply_text)

        # Send reply
        self.bot.send_message(user_id, reply_text)
