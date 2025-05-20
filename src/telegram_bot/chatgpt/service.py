import logging

from sqlalchemy.orm import Session

from .models import Chat, Message

# Load logging configuration with OmegaConf
# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def create_chat(db_session: Session, user_id: int, name: str) -> Chat:
    """
    Create a new chat for a user.

    Args:
        db_session (Session): The database
        user_id (int): The ID of the user who owns the chat.
        name (str): The name of the chat.

    Returns:
        Chat: The created chat object.
    """
    db_chat = Chat(user_id=user_id, name=name)
    db_session.add(db_chat)
    db_session.commit()
    db_session.refresh(db_chat)
    db_session.close()
    return db_chat


def get_user_chats(db_session: Session, user_id: int) -> list[Chat]:
    """
    Retrieve all chats for a specific user.

    Args:
        user_id (int): The ID of the user whose chats to retrieve.

    Returns:
        list[Chat]: A list of chat objects associated with the user.
    """
    result = db_session.query(Chat).filter(Chat.user_id == user_id).all()
    db_session.close()
    return result


def read_chat_history(db_session: Session, chat_id: int) -> list[Message]:
    """
    Retrieve the message history for a specific chat.

    Args:
        db_session (Session): The database session.
        chat_id (int): The ID of the chat whose history to retrieve.

    Returns:
        list[Message]: A list of message objects associated with the chat.
    """
    result = (
        db_session.query(Message)
        .filter(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    db_session.close()
    return result


def delete_chat(db_session: Session, user_id: int, chat_id: int) -> None:
    """
    Delete a chat and all associated messages.

    Args:
        user_id (int): The ID of the user who owns the chat.
        chat_id (int): The ID of the chat to delete.
    """
    # First, delete the messages associated with the chat
    db_messages = db_session.query(Message).filter(Message.chat_id == chat_id).all()
    for message in db_messages:
        db_session.delete(message)

    # Then, delete the chat
    db_chat = (
        db_session.query(Chat)
        .filter(Chat.id == chat_id, Chat.user_id == user_id)
        .first()
    )
    db_session.delete(db_chat)
    db_session.commit()
    db_session.close()


def create_message(
    db_session: Session, chat_id: int, role: str, content: str
) -> Message:
    """
    Create a new message in a chat.

    Args:
        chat_id (int): The ID of the chat to add the message to.
        role (str): The role of the message sender.
        content (str): The content of the message.

    Returns:
        Message: The created message object.
    """
    db_message = Message(chat_id=chat_id, role=role, content=content)
    db_session.add(db_message)
    db_session.commit()
    db_session.refresh(db_message)
    db_session.close()
    return db_message
