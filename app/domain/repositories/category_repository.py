from abc import ABC, abstractmethod
from typing import List, Optional
import uuid

from app.domain.entities.category import Category


class CategoryRepository(ABC):
    @abstractmethod
    def get_by_id(self, category_id: uuid.UUID) -> Optional[Category]:
        pass

    @abstractmethod
    def get_by_name_key(self, name_key: str) -> Optional[Category]:
        pass

    @abstractmethod
    def list_all(self, active_only: bool = True) -> List[Category]:
        pass

    @abstractmethod
    def create(self, category: Category) -> Category:
        pass

    @abstractmethod
    def update(self, category: Category) -> Category:
        pass
