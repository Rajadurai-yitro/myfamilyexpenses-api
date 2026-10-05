from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import uuid

from app.domain.entities.expense import Expense


class ExpenseRepository(ABC):
    @abstractmethod
    def create(self, expense: Expense) -> Expense:
        pass

    @abstractmethod
    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        pass

    @abstractmethod
    def list(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Expense], int]:
        pass

    @abstractmethod
    def update(self, expense: Expense) -> Expense:
        pass

    @abstractmethod
    def delete(self, expense_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    def get_total_between(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        entry_type: Optional[str] = None,
    ) -> Decimal:
        pass

    @abstractmethod
    def get_daily_totals(
        self,
        user_id: uuid.UUID,
        year: int,
        month: int,
    ) -> List[Dict[str, any]]:
        pass

    @abstractmethod
    def get_monthly_totals(
        self,
        user_id: uuid.UUID,
        year: int,
    ) -> List[Dict[str, any]]:
        pass

    @abstractmethod
    def get_yearly_totals(
        self,
        user_id: uuid.UUID,
        start_year: int,
        end_year: int,
    ) -> List[Dict[str, any]]:
        pass

    @abstractmethod
    def get_category_totals(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, any]]:
        pass
