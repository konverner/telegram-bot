import logging.config
import os

from dotenv import find_dotenv, load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from .models import Base

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
    logger.error("One or more database environment variables are not set.")
    exit(1)

# Construct the database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?sslmode=require"

def get_enginge():
    return create_engine(
        DATABASE_URL,
        connect_args={'connect_timeout': 5, "application_name": "telegram_bot"},
        poolclass=NullPool
    )
def create_tables():
    engine = get_enginge()
    Base.metadata.create_all(engine)
    logger.info("Tables created")

def get_session():
    engine = get_enginge()
    return sessionmaker(bind=engine)()
