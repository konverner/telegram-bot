from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..models import Base, TimeStampMixin


class ItemCategory(Base):
    """Item category model"""

    __tablename__ = "item_categories"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Item(Base, TimeStampMixin):
    """Item model"""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    content = Column(String, nullable=True)
    category = Column(Integer, ForeignKey("item_categories.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")
    item_category = relationship("ItemCategory")
