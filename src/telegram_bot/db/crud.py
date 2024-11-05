import csv
import logging
import os
from datetime import datetime
from typing import Optional

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .database import get_session
from .models import Message, User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user(username: str) -> User:
    db: Session = get_session()
    result = db.query(User).filter(User.name == username).first()
    db.close()
    return result


def get_users() -> list[User]:
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result


def upsert_user(
    name: str,
    id: Optional[int] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    lang: str = "en",
    role: Optional[str] = None,
) -> User:
    user = User(name=name)
    if id is not None:
        user.id = id
    if lang:
        user.lang = lang
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if role:
        user.role = role
    db: Session = get_session()
    db.merge(user)
    db.commit()

    user = db.query(User).filter(User.name == name).first()

    db.close()
    return user


def add_message(username: str, text: str) -> Message:
    message = Message(username=username, text=text, timestamp=datetime.now())
    db: Session = get_session()
    db.add(message)
    db.commit()
    db.close()
    return message


def get_message(message_id: int) -> Optional[Message]:
    db: Session = get_session()
    try:
        return db.query(Message).filter(Message.id == message_id).first()
    finally:
        db.close()


def get_messages_by_user(username: str) -> list[Message]:
    db: Session = get_session()
    try:
        return db.query(Message).filter(Message.username == username).all()
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
