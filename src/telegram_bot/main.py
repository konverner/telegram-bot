from telegram_bot.api.bot import start_bot
from telegram_bot.db.database import create_tables

if __name__ == "__main__":
    create_tables()
    start_bot()
