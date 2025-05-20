from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    event,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base model"""

    pass


class TimeStampMixin(object):
    """Timestamping mixin"""

    created_at = Column(DateTime, default=datetime.now)
    created_at._creation_order = 9998
    updated_at = Column(DateTime, default=datetime.now)
    updated_at._creation_order = 9998

    @staticmethod
    def _updated_at(mapper, connection, target):
        target.updated_at = datetime.now()

    @classmethod
    def __declare_last__(cls):
        """Add event listeners"""
        event.listen(cls, "before_update", cls._updated_at)
