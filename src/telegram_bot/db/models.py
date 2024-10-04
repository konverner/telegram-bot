from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Message(Base):
    __tablename__ = 'messages'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    message_text = Column(String)

    user = relationship("User", back_populates="messages")


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    first_message_timestamp = Column(DateTime)
    username = Column(String)
    phone_number = Column(String)
    language = Column(String, default='en')

    messages = relationship("Message", back_populates="user")
