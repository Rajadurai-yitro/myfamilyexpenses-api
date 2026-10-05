from datetime import datetime
from typing import List, Optional
import uuid
from sqlalchemy.orm import Session

from app.domain.entities.category import Category
from app.domain.repositories.category_repository import CategoryRepository
from app.infrastructure.database.models.category_model import CategoryModel


class SqlAlchemyCategoryRepository(CategoryRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: CategoryModel) -> Category:
        return Category(
            id=model.id,
            name_key=model.name_key,
            icon_key=model.icon_key,
            sort_order=model.sort_order,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
            kind=model.kind or "debit",
        )

    def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        model = self.db.query(CategoryModel).filter(CategoryModel.id == category_id).first()
        return self._to_entity(model) if model else None

    def get_by_name_key(self, name_key: str) -> Optional[Category]:
        model = self.db.query(CategoryModel).filter(
            CategoryModel.name_key == name_key.strip().lower()
        ).first()
        return self._to_entity(model) if model else None

    def list_all(self, active_only: bool = True) -> List[Category]:
        query = self.db.query(CategoryModel)
        if active_only:
            query = query.filter(CategoryModel.is_active.is_(True))
        models = query.order_by(CategoryModel.sort_order.asc(), CategoryModel.name_key.asc()).all()
        return [self._to_entity(m) for m in models]

    def create(self, category: Category) -> Category:
        model = CategoryModel(
            id=category.id,
            name_key=category.name_key,
            icon_key=category.icon_key,
            sort_order=category.sort_order,
            is_active=category.is_active,
            kind=category.kind,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, category: Category) -> Category:
        model = self.db.query(CategoryModel).filter(CategoryModel.id == category.id).first()
        if not model:
            raise ValueError("Category not found")
        model.name_key = category.name_key
        model.icon_key = category.icon_key
        model.kind = category.kind
        model.sort_order = category.sort_order
        model.is_active = category.is_active
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)
