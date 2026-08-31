"""
TalentFlow AI — Base Generic Repository
Provides clean CRUD operations for SQLAlchemy models.
"""
from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from ..models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType], db: Session):
        self.model = model
        self.db = db

    def get_by_id(self, id: Any) -> Optional[ModelType]:
        return self.db.query(self.model).filter(self.model.id == str(id)).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return self.db.query(self.model).offset(skip).limit(limit).all()

    def create(self, **kwargs) -> ModelType:
        instance = self.model(**kwargs)
        self.db.add(instance)
        self.db.flush()
        return instance

    def update(self, instance: ModelType, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            if hasattr(instance, key) and value is not None:
                setattr(instance, key, value)
        self.db.flush()
        return instance

    def delete(self, instance: ModelType) -> bool:
        self.db.delete(instance)
        self.db.flush()
        return True

    def count(self) -> int:
        return self.db.query(self.model).count()
