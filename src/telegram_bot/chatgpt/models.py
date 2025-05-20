from sqlalchemy import BigInteger, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..models import Base, TimeStampMixin


class Chat(Base, TimeStampMixin):
    """Chat model"""

    __tablename__ = "chatgpt_chats"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=True)

    # Establish relationship with Message and enable cascade deletion
    messages = relationship(
        "Message", back_populates="chat", cascade="all, delete-orphan"
    )


class Message(Base, TimeStampMixin):
    """Message model"""

    __tablename__ = "chatgpt_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    chat_id = Column(Integer, ForeignKey("chatgpt_chats.id"))
    role = Column(String)
    content = Column(String)

    # Define the relationship with Chat
    chat = relationship("Chat", back_populates="messages")
