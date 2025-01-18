import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Event

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
