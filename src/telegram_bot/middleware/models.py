from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship

from ..auth.models import User
from ..models import Base, TimeStampMixin


class Event(Base, TimeStampMixin):
    """Event model"""

    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id))
    event_type = Column(String)
    state = Column(String, nullable=True)
    content_type = Column(String)
    content = Column(String, nullable=True)

    def dict(self) -> dict:
        """Return a dictionary representation of the event"""
        return {
            "timestamp": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "user_id": self.user_id,
            "event_type": self.event_type,
            "state": self.state,
            "content": self.content,
            "content_type": self.content_type,
        }
