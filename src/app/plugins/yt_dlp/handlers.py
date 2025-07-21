import logging
import re
from pathlib import Path
from typing import Any, Dict

from omegaconf import OmegaConf
from telebot import TeleBot, types
from telebot.states import State, StatesGroup  # Correct import for sync/async
from telebot.states.sync.context import (
    StateContext,
)  # Import StateContext if using sync

from ...menu.markup import create_menu_markup  # Assuming menu markup is in parent dir
from .markup import (
    create_back_to_menu_button,
    create_cancel_button,
    create_format_selection_markup,
)
from .service import DownloadError, download_youtube_content

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load configuration
CURRENT_DIR = Path(__file__).parent
config = OmegaConf.load(CURRENT_DIR / "config.yaml")
strings = config.strings


YOUTUBE_URL_PATTERN = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})"


class YouTubeDLState(StatesGroup):
    """States for YouTube download conversation flow."""

    awaiting_url = State()
    awaiting_format = State()


def register_handlers(bot: TeleBot) -> None:  # Pass state_storage if needed
    """
    Register all YouTube download related handlers for the bot.

    Args:
        bot: The Telegram bot instance.
    """
    logger.info("Registering YouTube Downloader handlers")

    # Handler to trigger the YouTube download feature (e.g., from main menu)
    @bot.callback_query_handler(func=lambda call: call.data == "yt_dlp")
    def start_yt_dlp(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """Starts the YouTube download process by asking for the URL."""
        user = data["user"]  # Assuming user object is in data
        state: StateContext = data["state"]  # Assuming state context is in data
        lang = user.lang if hasattr(user, "lang") else "en"  # Get user language

        state.set(YouTubeDLState.awaiting_url)
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=strings[lang].enter_url,
            reply_markup=create_cancel_button(
                lang, callback_data="menu"
            ),  # Cancel goes back to main menu
        )

    # Handler to automatically detect YouTube links in any message (outside specific states)
    @bot.message_handler(
        func=lambda message: re.search(YOUTUBE_URL_PATTERN, message.text) is not None,
        content_types=["text"],
        state=None,
    )
    def handle_youtube_link(message: types.Message, data: Dict[str, Any]) -> None:
        """Detects a YouTube link in a message and prompts for download format."""
        user = data["user"]
        state: StateContext = data["state"]
        lang = user.lang if hasattr(user, "lang") else "en"
        url = message.text

        match = re.search(YOUTUBE_URL_PATTERN, url)
        if match:
            detected_url = match.group(0)  # Get the full matched URL
            logger.info(
                f"Detected YouTube URL: {detected_url} from user {message.from_user.id}"
            )

            state.set(YouTubeDLState.awaiting_format)
            state.add_data(youtube_url=detected_url)
            bot.send_message(
                message.chat.id,
                strings[lang].get(
                    "detected_yt_link",
                    "YouTube link detected! Choose format to download:",
                ),  # Use .get for safety
                reply_markup=create_format_selection_markup(lang),
            )
        # If no match (shouldn't happen due to the func filter, but good practice)
        else:
            logger.warning(
                f"YouTube link handler triggered for message without link: {message.text}"
            )

    # Handler to process the received URL
    @bot.message_handler(state=YouTubeDLState.awaiting_url, content_types=["text"])
    def process_url(message: types.Message, data: Dict[str, Any]) -> None:
        """Processes the YouTube URL and asks for the format."""
        user = data["user"]
        state: StateContext = data["state"]
        lang = user.lang if hasattr(user, "lang") else "en"
        url = message.text

        # Basic URL validation (you might want a more robust check)
        if not ("youtube.com" in url or "youtu.be" in url):
            bot.send_message(
                message.chat.id,
                strings[lang].invalid_url,
                reply_markup=create_cancel_button(lang, callback_data="menu"),
            )
            # Keep the state awaiting_url
            return

        state.add_data(youtube_url=url)
        state.set(YouTubeDLState.awaiting_format)
        bot.send_message(
            message.chat.id,
            strings[lang].choose_format,
            reply_markup=create_format_selection_markup(lang),
        )

    # Handler for format selection (callback query)
    @bot.callback_query_handler(
        func=lambda call: call.data.startswith("ydl_format_"),
        state=YouTubeDLState.awaiting_format,
    )
    def process_format_selection(
        call: types.CallbackQuery, data: Dict[str, Any]
    ) -> None:
        """Processes the format selection and starts the download."""
        user = data["user"]
        state: StateContext = data["state"]
        lang = user.lang if hasattr(user, "lang") else "en"
        download_type = call.data.split("_")[-1]  # "video" or "audio"

        if download_type not in ["video", "audio"]:
            bot.answer_callback_query(call.id, strings[lang].invalid_format)
            return

        with data["state"].data() as data_items:
            url = data_items.get("youtube_url")

        if not url:
            logger.error("URL not found in state during format selection.")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=strings[lang].download_error.format(error="Internal state error."),
                reply_markup=create_back_to_menu_button(lang),
            )
            state.delete()
            return

        # Acknowledge selection and show downloading message
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=strings[lang].downloading,
            reply_markup=None,  # Remove buttons
        )

        try:
            # Perform the download (this might block if not run carefully in async)
            # Consider running download_youtube_content in a separate thread/process for bots
            # For simplicity here, calling it directly (may block the bot)
            downloaded_file_path = download_youtube_content(url, download_type)

            # Send the downloaded file
            # Note: Telegram has file size limits (50MB for bots via API, 2GB/4GB for users)
            # Handle potential FileNotFoundError if service fails unexpectedly
            if downloaded_file_path and downloaded_file_path.exists():
                # Send the file as document regardless of type
                with open(downloaded_file_path, "rb") as file:
                    bot.send_document(
                        call.message.chat.id,
                        file,
                        caption=strings[lang].download_success.format(
                            filename=downloaded_file_path.name
                        ),
                    )

                # Clean up the downloaded file after sending
                try:
                    downloaded_file_path.unlink()
                    logger.info(f"Deleted temporary file: {downloaded_file_path}")
                except OSError as e:
                    logger.error(f"Error deleting file {downloaded_file_path}: {e}")

            else:
                raise DownloadError("Downloaded file path not found after download.")

        except DownloadError as e:
            logger.error(f"Download failed for URL {url}: {e}")
            bot.send_message(
                call.message.chat.id,
                strings[lang].download_error.format(error=str(e)),
                reply_markup=create_back_to_menu_button(lang),
            )
        except Exception as e:  # Catch unexpected errors
            logger.exception(
                f"Unexpected error during download/send for URL {url}: {e}"
            )
            bot.send_message(
                call.message.chat.id,
                strings[lang].download_error.format(
                    error="An unexpected error occurred."
                ),
                reply_markup=create_back_to_menu_button(lang),
            )
        finally:
            # Always clear state afterwards
            state.delete()

    # Handler for cancel button during format selection
    @bot.callback_query_handler(
        func=lambda call: call.data == "ydl_cancel",
        state=YouTubeDLState.awaiting_format,
    )
    def cancel_download(call: types.CallbackQuery, data: Dict[str, Any]) -> None:
        """Cancels the download process and returns to the main menu."""
        user = data["user"]
        state: StateContext = data["state"]
        lang = user.lang if hasattr(user, "lang") else "en"

        state.delete()
        # Go back to the main menu - reuse your existing menu logic if possible
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=strings[lang].back_to_menu,  # Or your main menu text
            reply_markup=create_menu_markup(lang),  # Use your main menu markup
        )
