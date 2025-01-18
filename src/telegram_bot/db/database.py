import csv
import logging
import logging.config
import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .models import Base

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load logging configuration with OmegaConf
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv(find_dotenv(usecwd=True))

# Retrieve environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Check if any of the required environment variables are not set
if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
    logger.warning("One or more postgresql database environment variables are not set. Using SQLite instead.")
    DATABASE_URL = "sqlite:///local_database.db"
else:
    # Construct the database URL for PostgreSQL
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"


def get_engine():
    """Get a new engine for the database."""
    return create_engine(
        DATABASE_URL,
        connect_args={"connect_timeout": 5, "application_name": "telegram_bot"} if "postgresql" in DATABASE_URL else {},
        poolclass=NullPool if "postgresql" in DATABASE_URL else None,
    )


def create_tables():
    """Create tables in the database."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    logger.info("Tables created")


def drop_tables():
    """Drop tables in the database."""
    engine = get_engine()
    Base.metadata.drop_all(engine)
    logger.info("Tables dropped")


def get_session():
    """Get a new session from the database engine."""
    engine = get_engine()
    return sessionmaker(bind=engine)()


def export_all_tables(export_dir: str):
    """Export all tables to CSV files."""
    db = get_session()
    inspector = inspect(db.get_bind())

    for table_name in inspector.get_table_names():
        file_path = os.path.join(export_dir, f"{table_name}.csv")
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            writer.writerow(columns)

            records = db.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            for record in records:
                writer.writerow(record)

    db.close()
