from sqlalchemy.orm import Session

from .models import Role
from .service import upsert_user


def init_roles_table(db_session: Session):
    # Insert data into the system roles table
    system_roles_data = [
        {"id": 0, "name": "superuser", "description": "Super User"},
        {"id": 1, "name": "admin", "description": "Admin"},
        {"id": 2, "name": "user", "description": "User"},
    ]

    # Add and commit data
    for system_role_data in system_roles_data:
        system_role = Role(**system_role_data)
        db_session.add(system_role)

    db_session.commit()


def init_superuser(db_session: Session, user_id: int, username: str):
    # Insert data into the system roles table
    user = upsert_user(db_session, id=user_id, username=username, role_id=0)
    db_session.commit()
