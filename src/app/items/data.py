from sqlalchemy.orm import Session

from .models import ItemCategory


def init_item_categories_table(db_session: Session):
    # Insert data into the item categories table
    item_categories_data = [
        {"id": 1, "name": "Category A"},
        {"id": 2, "name": "Category B"},
    ]

    # Add and commit data
    for item_category_data in item_categories_data:
        item_category = ItemCategory(**item_category_data)
        db_session.add(item_category)

    db_session.commit()
