"""Handler to show information about the application configuration."""
import logging
import logging.config
from pathlib import Path

from omegaconf import OmegaConf
from telebot.types import CallbackQuery

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


# React to any text if not command
def register_handlers(bot):
    """Register common handlers"""

    @bot.callback_query_handler(func=lambda call: call.data == "cancel")
    def cancel_callback(call: CallbackQuery, data: dict):
        """Cancel current operation"""
        user = data["user"]
        bot.send_message(call.message.chat.id, strings[user.lang].cancelled)
        bot.clear_step_handler_by_chat_id(chat_id=call.message.chat.id)
