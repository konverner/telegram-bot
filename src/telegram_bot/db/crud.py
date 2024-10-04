import logging
from typing import Optional

from sqlalchemy.orm import Session

from .database import get_session
from .models import Message, User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_user(user_id: int) -> User:
    db: Session = get_session()
    result = db.query(User).filter(User.id == user_id).first()
    db.close()
    return result

def get_users() -> list[User]:
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result

def upsert_user(
        user_id: str,
        username: str,
        phone_number: str = None,
        language: str = "en"
    ) -> User:
    user = User(
        id=user_id,
        username=username
    )
    if phone_number:
        user.phone_number = phone_number
    if language:
        user.language = language
    db: Session = get_session()
    db.merge(user)
    db.commit()
    db.close()
    return user

def get_message(message_id: int) -> Optional[Message]:
    db: Session = get_session()
    try:
        return db.query(Message).filter(Message.id == message_id).first()
    finally:
        db.close()

def get_messages_by_user(user_id: int) -> list[Message]:
    db: Session = get_session()
    try:
        return db.query(Message).filter(Message.user_id == user_id).all()
    finally:
        db.close()