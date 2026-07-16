"""Persistence layer — SQLAlchemy-инфраструктура.

Живёт только здесь и в конкретных провайдерах. Доменный слой
(app/core/, app/models/) НИКОГДА не импортирует SQLAlchemy.
"""

from app.persistence.database import Base, create_engine, init_database
from app.persistence.models import MemoryRecord

__all__ = [
    "Base",
    "MemoryRecord",
    "create_engine",
    "init_database",
]
