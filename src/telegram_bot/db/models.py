from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base model"""

    pass


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    name = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    lang = Column(String, default="en")
    role = Column(String, default="user")

    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    user_id = Column(BigInteger, ForeignKey("users.id"))
    type = Column(String)
    content = Column(String)

    user = relationship("User", back_populates="events")

    def dict(self) -> dict:
        return {
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": self.user_id,
            "type": self.type,
            "content": self.content,
        }
