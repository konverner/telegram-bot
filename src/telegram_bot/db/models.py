from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base model"""

    pass


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    username = Column(String, ForeignKey("users.name"))
    text = Column(String)

    user = relationship("User", back_populates="messages")


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger)
    name = Column(String, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    lang = Column(String, default="en")
    role = Column(String, default="user")

    messages = relationship("Message", back_populates="user")
