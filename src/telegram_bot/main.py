import os

from dotenv import find_dotenv, load_dotenv

from telegram_bot.api.bot import start_bot
from telegram_bot.db import crud
from telegram_bot.db.database import create_tables, drop_tables

# Load and get environment variables
load_dotenv(find_dotenv(usecwd=True))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")


if __name__ == "__main__":
    drop_tables()
    create_tables()
    # add admin user
    if ADMIN_USERNAME:
        crud.upsert_user(name=ADMIN_USERNAME, role="admin")
    start_bot()
