import logging
from datetime import datetime

from sqlalchemy.orm import Session

from .models import Item, ItemCategory

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def read_item_category(db_session: Session, category_id: int):
    """Get an item category by ID"""
    return db_session.query(ItemCategory).filter(ItemCategory.id == category_id).first()


def read_item_categories(db_session: Session, skip: int = 0, limit: int = 10):
    """Get all item categories"""
    return db_session.query(ItemCategory).offset(skip).limit(limit).all()


def create_item(
    db_session: Session, name: str, content: str, category: int, owner_id: int
):
    """Create a new item"""
    item = Item(
        name=name,
        content=content,
        category=category,
        owner_id=owner_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def read_item(db_session: Session, item_id: int):
    """Get an item by ID"""
    return db_session.query(Item).filter(Item.id == item_id).first()


def read_items_by_owner(
    db_session: Session, owner_id: int, skip: int = 0, limit: int = 10
):
    """Get all items by a specific owner"""
    return (
        db_session.query(Item)
        .filter(Item.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def read_items(db_session: Session, skip: int = 0, limit: int = 10):
    """Get all items"""
    return db_session.query(Item).offset(skip).limit(limit).all()


def update_item(
    db_session: Session, item_id: int, name: str, content: str, category: int
):
    """Update an item"""
    item = db_session.query(Item).filter(Item.id == item_id).first()
    if item:
        item.name = name
        item.content = content
        item.category = category
        item.updated_at = datetime.utcnow()
        db_session.commit()
        db_session.refresh(item)
    return item


def delete_item(db_session: Session, item_id: int) -> bool:
    """Delete an item"""
    item = db_session.query(Item).filter(Item.id == item_id).first()
    if item:
        db_session.delete(item)
        db_session.commit()
        return True
    return False
