import csv
import logging
import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from ..auth.models import Base
from ..config import settings

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

load_dotenv(find_dotenv(usecwd=True))

# Use settings to determine database URL
if settings.SQLALCHEMY_DATABASE_URI:
    DATABASE_URL = str(settings.SQLALCHEMY_DATABASE_URI)
    logger.info(f"Using PostgreSQL database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")
else:
    DATABASE_URL = "sqlite:///local_database.db"
    logger.warning("Database environment variables not set. Using SQLite instead.")

# Replace with a unified approach:
engine = create_engine(
    DATABASE_URL,
    connect_args={"connect_timeout": 5, "application_name": "telegram_bot"}
    if "postgresql" in DATABASE_URL
    else {},
    poolclass=NullPool if "postgresql" in DATABASE_URL else None,
    pool_size=32,
    echo=False,
)

# a factory that produces new Session objects (database sessions).
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency
def get_db():
    """Get a database session and ensure it's closed when done."""
    db = SessionLocal()  #  a new database session object
    try:
        yield db  # yield keyword allows the session to be used within a with statement
    finally:
        db.close()


def create_tables():
    """Create tables in the database."""
    Base.metadata.create_all(engine)
    logger.info("Tables created")


def drop_tables():
    """Drop tables in the database."""
    Base.metadata.drop_all(engine)
    logger.info("Tables dropped")


def export_all_tables(db_session, export_dir: str) -> list[str]:
    """Export all tables to CSV files."""
    inspector = inspect(db_session.get_bind())
    table_names = inspector.get_table_names()
    for table_name in table_names:
        file_path = os.path.join(export_dir, f"{table_name}.csv")
        with open(file_path, mode="w", newline="") as file:
            writer = csv.writer(file)
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            writer.writerow(columns)

            records = db_session.execute(text(f"SELECT * FROM {table_name}")).fetchall()
            for record in records:
                writer.writerow(record)

    db_session.close()
    return table_names
