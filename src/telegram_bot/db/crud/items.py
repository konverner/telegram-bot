import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ..database import get_session
from ..models import Item, ItemCategory

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# CRUD operations for ItemCategory
def create_item_category(name: str):
    """ Create a new item category """
    db: Session = get_session()
    item_category = ItemCategory(name=name)
    db.add(item_category)
    db.commit()
    db.refresh(item_category)
    return item_category

def read_item_category(category_id: int):
    """ Get an item category by ID """
    db: Session = get_session()
    return db.query(ItemCategory).filter(ItemCategory.id == category_id).first()

def read_item_categories(skip: int = 0, limit: int = 10):
    """ Get all item categories """
    db: Session = get_session()
    return db.query(ItemCategory).offset(skip).limit(limit).all()

def update_item_category(category_id: int, name: str):
    """ Update an item category """
    db: Session = get_session()
    item_category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if item_category:
        item_category.name = name
        db.commit()
        db.refresh(item_category)
    return item_category

def delete_item_category(category_id: int):
    """ Delete an item category """
    db: Session = get_session()
    item_category = db.query(ItemCategory).filter(ItemCategory.id == category_id).first()
    if item_category:
        db.delete(item_category)
        db.commit()
    return item_category

# CRUD operations for Item
def create_item(name: str, content: str, category: int, owner_id: int):
    """ Create a new item """
    db: Session = get_session()
    item = Item(
        name=name,
        content=content,
        category=category,
        owner_id=owner_id,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

def read_item(item_id: int):
    """ Get an item by ID """
    db: Session = get_session()
    return db.query(Item).filter(Item.id == item_id).first()

def read_items(skip: int = 0, limit: int = 10):
    """ Get all items """
    db: Session = get_session()
    return db.query(Item).offset(skip).limit(limit).all()

def update_item(item_id: int, name: str, content: str, category: int):
    """ Update an item """
    db: Session = get_session()
    item = db.query(Item).filter(Item.id == item_id).first()
    if item:
        item.name = name
        item.content = content
        item.category = category
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
    return item

def delete_item(item_id: int):
    """ Delete an item """
    db: Session = get_session()
    item = db.query(Item).filter(Item.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return item
