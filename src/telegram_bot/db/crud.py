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


# Users crud


def read_user(id: int) -> User:
    """Read user by id"""
    db: Session = get_session()
    result = db.query(User).filter(User.id == id).first()
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
    lang: Optional[str] = None,
    role: Optional[str] = None,
) -> User:
    """
    Create a new user.

    Args:
        id: The user's ID.
        username: The user's username.
        first_name: The user's first name.
        last_name: The user's last name.
        lang: The user's language.
        role: The user's role.

    Returns:
        The created user object.
    """
    db: Session = get_session()
    db.expire_on_commit = False
    try:
        user = User(id=id, username=username, first_name=first_name, last_name=last_name, lang=lang, role=role)
        db.add(user)
        db.commit()
        logger.info(f"User created: {user.id} {user.username}.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding user {id}: {e}")
        raise
    finally:
        db.close()
    return user


def update_user(
    id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
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
                user.name = username
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if lang is not None:
                user.lang = lang
            if role is not None:
                user.role = role
            logger.info(f"User updated: {user.id} {user.username}.")
        else:
            logger.error(f"User {user.id} {user.username} not found.")
            raise ValueError(f"User with ID {id} not found.")
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user {user.id} {user.username}: {e}")
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


# Events crud


def create_event(user_id: str, content: str, type: str, state: Optional[str] = None) -> Event:
    """Create an event for a user."""
    event = Event(user_id=user_id, content=content, state=state, type=type, timestamp=datetime.now())
    db: Session = get_session()
    db.expire_on_commit = False
    db.add(event)
    db.commit()
    db.close()
    return event


def read_event(event_id: int) -> Optional[Event]:
    """Read an event by ID."""
    db: Session = get_session()
    try:
        return db.query(Event).filter(Event.id == event_id).first()
    finally:
        db.close()


def read_events_by_user(user_id: str) -> list[Event]:
    """Read all events for a user."""
    db: Session = get_session()
    try:
        return db.query(Event).filter(Event.user_id == user_id).all()
    finally:
        db.close()


# Utility functions


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
