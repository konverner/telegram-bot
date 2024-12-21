import logging
import os

from dotenv import find_dotenv, load_dotenv

from telegram_bot.api.bot import start_bot
from telegram_bot.db import crud
from telegram_bot.db.database import create_tables, drop_tables

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load and get environment variables
load_dotenv(find_dotenv(usecwd=True))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")


def init_db():
    """Initialize the database."""
    # Create tables
    create_tables()

    # Add admin to user table
    if ADMIN_USERNAME:
        user = crud.upsert_user(id=ADMIN_USER_ID, username=ADMIN_USERNAME, role="admin")
        logger.info(f"User '{user.username}' ({user.id}) added to the database with admin role.")

    logger.info("Database initialized")


if __name__ == "__main__":
    drop_tables()
    init_db()
    start_bot()
