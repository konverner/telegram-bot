import csv
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .database import get_session
from .models import Event, User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_user(username: str) -> User:
    db: Session = get_session()
    result = db.query(User).filter(User.name == username).first()
    db.close()
    return result


def read_users() -> list[User]:
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result


def upsert_user(
    id: int,
    name: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    lang: Optional[str] = "en",
    role: Optional[str] = None,
) -> User:
    """
    Insert or update a user.

    Args:
        id (int): The user's ID.
        name (str): The user's name.
        first_name (str): The user's first name.
        last_name (str): The user's last name.
        lang (str): The user's language.
        role (str): The user's role.

    Returns:
        User: The user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = db.query(User).filter(User.id == id).first()
        if user:
            user.name = name
            user.first_name = first_name
            user.last_name = last_name
        else:
            user = User(id=id, name=name, first_name=first_name, last_name=last_name, lang=lang, role=role)
            db.add(user)
            logger.info(f"User with name {user.name} added successfully.")
        db.commit()
        return user
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user with name {name}: {e}")
    finally:
        db.close()


def create_event(user_id: str, content: str, type: str) -> Event:
    """Create an event for a user."""
    event = Event(user_id=user_id, content=content, type=type, timestamp=datetime.now())
    db: Session = get_session()
    db.expire_on_commit = False
    db.add(event)
    db.commit()
    db.close()
    return event


def read_event(event_id: int) -> Optional[Event]:
    db: Session = get_session()
    try:
        return db.query(Event).filter(Event.id == event_id).first()
    finally:
        db.close()


def read_events_by_user(user_id: str) -> list[Event]:
    db: Session = get_session()
    try:
        return db.query(Event).filter(Event.user_id == user_id).all()
    finally:
        db.close()


def export_all_tables(export_dir: str):
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
