import logging
import os

from sqlalchemy.exc import SQLAlchemyError
from telebot import TeleBot
from telebot.handler_backends import BaseMiddleware

from ..database.core import SessionLocal

# Set logging
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, None))
logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, bot: TeleBot) -> None:
        """Middleware to manage database sessions

        This middleware creates a database session for each update,
        adds it to the data dictionary, and ensures it's properly closed afterward.

        Args:
            bot (TeleBot): TeleBot instance
        """
        self.bot = bot
        # Set update types to handle various types of updates
        self.update_types = [
            "message",
            "callback_query",
            "inline_query",
            "edited_message",
        ]
        logger.info("Database middleware initialized")

    def pre_process(self, message, data):
        """Create a database session and add it to the data dictionary"""
        try:
            # Create a new database session directly using SessionLocal
            session = SessionLocal()
            data["db_session"] = session
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error creating database session: {str(e)}")
            return False

    def post_process(self, message, data, exception):
        """Close the database session"""
        # Get the session from the data dictionary
        session = data.get("db_session")
        if session:
            try:
                # If there was an exception, rollback the session
                if exception:
                    logger.warning(
                        f"Rolling back database session due to exception: {str(exception)}"
                    )
                    session.rollback()
                # Otherwise commit any pending changes
                else:
                    session.commit()
            except SQLAlchemyError as e:
                logger.error(f"Error during session commit/rollback: {str(e)}")
                session.rollback()
            finally:
                # Always close the session, matching the finally block in get_db()
                session.close()
        else:
            logger.warning("No database session found in post_process")
