import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from .models import User

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def read_user(db_session: Session, user_id: Optional[int] = None, username: Optional[str] = None) -> User:
    """Read user by user_id or username"""
    if user_id is not None:
        result = db_session.query(User).filter(User.id == user_id).first()
    elif username is not None:
        result = db_session.query(User).filter(User.username == username).first()
    else:
        raise ValueError("Either user_id or username must be provided")
    return result


def read_users(db_session: Session, user_ids: Optional[list[int]] = None) -> list[User]:
    """Read users by user_ids"""
    if user_ids:
        result = db_session.query(User).filter(User.id.in_(user_ids)).all()
    else:
        result = db_session.query(User).all()
    return result


def create_user(
    db_session: Session,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    lang: Optional[str] = None,
    role_id: Optional[int] = 1,
    is_blocked: Optional[bool] = False,
) -> User:
    """
    Create a new user.

    Args:
        user_id: The user's ID.
        username: The user's name.
        first_name: The user's first name.
        last_name: The user's last name.
        phone_number: The user's phone number.
        lang: The user's language.
        role_id: The user's role id.

    Returns:
        The created user object.
    """

    db_session.expire_on_commit = False

    try:
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            first_message_timestamp=datetime.now(),
            last_message_timestamp=datetime.now(),
            phone_number=phone_number,
            lang=lang,
            role_id=role_id,
            is_blocked=is_blocked,
        )
        db_session.add(user)
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error adding user with name {username}: {e}")
        raise
    finally:
        db_session.close()
    return user


def update_user(
    db_session: Session,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    phone_number: Optional[str] = None,
    lang: Optional[str] = None,
    role_id: Optional[int] = None,
    is_blocked: Optional[bool] = None,
) -> User:
    """
    Update an existing user.

    Args:
        user_id: The user's ID.
        username: The user's name.
        first_name: The user's first name.
        last_name: The user's last name.
        phone_number: The user's phone number.
        lang: The user's language.
        role_id: The user's role id.
        is_blocked: The user's blocked status.

    Returns:
        The updated user object.
    """
    db_session.expire_on_commit = False
    try:
        user = db_session.query(User).filter(User.id == user_id).first()
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
            if role_id is not None:
                user.role_id = role_id
            if is_blocked is not None:
                user.is_blocked = is_blocked
            user.last_message_timestamp = datetime.now()
            db_session.commit()
        else:
            logger.error(f"User with ID {user_id} not found.")
            raise ValueError(f"User with ID {user_id} not found.")
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error updating user with ID {user_id}: {e}")
        raise
    finally:
        db_session.close()
    return user


def upsert_user(
    db_session: Session,
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    lang: Optional[str] = None,
    role_id: Optional[str] = None,
    is_blocked: Optional[bool] = None,
) -> User:
    """
    Insert or update a user.

    Args:
        user_id: The user's ID.
        username: The user's name.
        first_name: The user's first name.
        last_name: The user's last name.
        lang: The user's language.
        role_id: The user's role.
        is_blocked: The user's blocked status.

    Returns:
        The user object.
    """

    db_session.expire_on_commit = False
    try:
        user = db_session.query(User).filter(User.id == user_id).first()
        if user:
            user = update_user(
                db_session,
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                lang=lang,
                role_id=role_id,
                is_blocked=is_blocked,
            )
        else:
            user = create_user(
                db_session,
                user_id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                lang=lang,
                role_id=role_id,
                is_blocked=is_blocked,
            )
    except Exception as e:
        db_session.rollback()
        logger.error(f"Error upserting user with ID {user_id}: {e}")
        raise
    finally:
        db_session.close()
    return user
