import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..database import get_session
from ..models import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_user(id: int) -> User:
    """Read user by id"""
    db: Session = get_session()
    result = db.query(User).filter(User.id == id).first()
    db.close()
    return result


def read_user_by_username(username: str) -> User:
    """Read user by username"""
    db: Session = get_session()
    result = db.query(User).filter(User.username == username).first()
    db.close()
    return result


def read_users() -> list[User]:
    """Read all users"""
    db: Session = get_session()
    result = db.query(User).all()
    db.close()
    return result


def create_user(
    id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    lang: Optional[str] = None,
    role: Optional[str] = "user",
) -> User:
    """
    Create a new user.

    Args:
        id: The user's ID.
        username: The user's name.
        first_name: The user's first name.
        last_name: The user's last name.
        phone_number: The user's phone number.
        lang: The user's language.
        role: The user's role.

    Returns:
        The created user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = User(
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            first_message_timestamp=datetime.now(),
            last_message_timestamp=datetime.now(),
            phone_number=phone_number,
            lang=lang,
            role=role,
        )
        db.add(user)
        db.commit()
        logger.info(f"User with name {user.username} added successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user with name {username}: {e}")
        raise
    finally:
        db.close()
    return user


def update_user(
    id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    lang: Optional[str] = None,
    role: Optional[str] = None,
) -> User:
    """
    Update an existing user.

    Args:
        id: The user's ID.
        username: The user's name.
        first_name: The user's first name.
        last_name: The user's last name.
        phone_number: The user's phone number.
        lang: The user's language.
        role: The user's role.

    Returns:
        The updated user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = db.query(User).filter(User.id == id).first()
        if user:
            if username is not None:
                user.username = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if phone_number is not None:
                user.phone_number = phone_number
            if lang is not None:
                user.lang = lang
            if role is not None:
                user.role = role
            user.last_message_timestamp = datetime.now()
            db.commit()
            logger.info(f"User with ID {user.id} updated successfully.")
        else:
            logger.error(f"User with ID {id} not found.")
            raise ValueError(f"User with ID {id} not found.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user with ID {id}: {e}")
        raise
    finally:
        db.close()
    return user


def upsert_user(
    id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    lang: Optional[str] = None,
    role: Optional[str] = None,
) -> User:
    """
    Insert or update a user.

    Args:
        id: The user's ID.
        username: The user's name.
        first_name: The user's first name.
        last_name: The user's last name.
        lang: The user's language.
        role: The user's role.
        active_session_id: The user's active session ID.

    Returns:
        The user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = db.query(User).filter(User.id == id).first()
        if user:
            user = update_user(
                id=id, username=username, first_name=first_name, last_name=last_name, lang=lang, role=role
            )
        else:
            user = create_user(
                id=id, username=username, first_name=first_name, last_name=last_name, lang=lang, role=role
            )
    except Exception as e:
        db.rollback()
        logger.error(f"Error upserting user with ID {id}: {e}")
        raise
    finally:
        db.close()
    return user
