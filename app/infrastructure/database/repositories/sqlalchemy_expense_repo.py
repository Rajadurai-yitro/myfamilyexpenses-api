from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import uuid
from sqlalchemy import desc, func, extract
from sqlalchemy.orm import Session

from app.domain.entities.expense import Expense
from app.domain.repositories.expense_repository import ExpenseRepository
from app.infrastructure.database.models.expense_model import ExpenseModel
from app.infrastructure.database.models.category_model import CategoryModel


class SqlAlchemyExpenseRepository(ExpenseRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: ExpenseModel) -> Expense:
        return Expense(
            id=model.id,
            user_id=model.user_id,
            category_id=model.category_id,
            amount=Decimal(str(model.amount)),
            description=model.description,
            expense_date=model.expense_date,
            created_at=model.created_at,
            updated_at=model.updated_at,
            entry_type=model.entry_type or "debit",
            receipt_path=model.receipt_path,
            payment_mode=model.payment_mode or "cash",
            transaction_id=model.transaction_id,
            online_payment_type=model.online_payment_type,
        )

    def create(self, expense: Expense) -> Expense:
        model = ExpenseModel(
            id=expense.id,
            user_id=expense.user_id,
            category_id=expense.category_id,
            amount=expense.amount,
            description=expense.description,
            entry_type=expense.entry_type,
            receipt_path=expense.receipt_path,
            payment_mode=expense.payment_mode,
            transaction_id=expense.transaction_id,
            online_payment_type=expense.online_payment_type,
            expense_date=expense.expense_date,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        model = self.db.query(ExpenseModel).filter(ExpenseModel.id == expense_id).first()
        return self._to_entity(model) if model else None

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
        query = self.db.query(ExpenseModel).filter(ExpenseModel.user_id == user_id)

        if start_date:
            query = query.filter(ExpenseModel.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseModel.expense_date <= end_date)
        if category_id:
            query = query.filter(ExpenseModel.category_id == category_id)
        if search:
            query = query.filter(ExpenseModel.description.ilike(f"%{search.strip()}%"))

        total_count = query.count()
        models = (
            query.order_by(desc(ExpenseModel.expense_date), desc(ExpenseModel.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [self._to_entity(m) for m in models], total_count

    def update(self, expense: Expense) -> Expense:
        model = self.db.query(ExpenseModel).filter(ExpenseModel.id == expense.id).first()
        if not model:
            raise ValueError("Expense not found")
        model.category_id = expense.category_id
        model.amount = expense.amount
        model.description = expense.description
        model.entry_type = expense.entry_type
        model.receipt_path = expense.receipt_path
        model.payment_mode = expense.payment_mode
        model.transaction_id = expense.transaction_id
        model.online_payment_type = expense.online_payment_type
        model.expense_date = expense.expense_date
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, expense_id: uuid.UUID) -> bool:
        model = self.db.query(ExpenseModel).filter(ExpenseModel.id == expense_id).first()
        if not model:
            return False
        from app.infrastructure.storage.receipt_storage import delete_receipt

        delete_receipt(model.receipt_path)
        self.db.delete(model)
        self.db.commit()
        return True

    def get_total_between(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        entry_type: Optional[str] = None,
    ) -> Decimal:
        query = self.db.query(func.coalesce(func.sum(ExpenseModel.amount), 0)).filter(
            ExpenseModel.user_id == user_id
        )
        if entry_type:
            query = query.filter(ExpenseModel.entry_type == entry_type)
        if start_date:
            query = query.filter(ExpenseModel.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseModel.expense_date <= end_date)
        result = query.scalar()
        return Decimal(str(result or 0.00))

    def get_daily_totals(
        self,
        user_id: uuid.UUID,
        year: int,
        month: int,
    ) -> List[Dict[str, any]]:
        rows = (
            self.db.query(
                ExpenseModel.expense_date,
                func.sum(ExpenseModel.amount).label("total_amount"),
                func.count(ExpenseModel.id).label("count"),
            )
            .filter(
                ExpenseModel.user_id == user_id,
                ExpenseModel.entry_type == "debit",
                extract("year", ExpenseModel.expense_date) == year,
                extract("month", ExpenseModel.expense_date) == month,
            )
            .group_by(ExpenseModel.expense_date)
            .order_by(ExpenseModel.expense_date.asc())
            .all()
        )
        return [
            {
                "date": str(r[0]),
                "total_amount": float(r[1] or 0),
                "count": r[2],
            }
            for r in rows
        ]

    def get_monthly_totals(
        self,
        user_id: uuid.UUID,
        year: int,
    ) -> List[Dict[str, any]]:
        rows = (
            self.db.query(
                extract("month", ExpenseModel.expense_date).label("month"),
                func.sum(ExpenseModel.amount).label("total_amount"),
                func.count(ExpenseModel.id).label("count"),
            )
            .filter(
                ExpenseModel.user_id == user_id,
                ExpenseModel.entry_type == "debit",
                extract("year", ExpenseModel.expense_date) == year,
            )
            .group_by(extract("month", ExpenseModel.expense_date))
            .order_by(extract("month", ExpenseModel.expense_date).asc())
            .all()
        )
        return [
            {
                "month": int(r[0]),
                "total_amount": float(r[1] or 0),
                "count": r[2],
            }
            for r in rows
        ]

    def get_yearly_totals(
        self,
        user_id: uuid.UUID,
        start_year: int,
        end_year: int,
    ) -> List[Dict[str, any]]:
        rows = (
            self.db.query(
                extract("year", ExpenseModel.expense_date).label("year"),
                func.sum(ExpenseModel.amount).label("total_amount"),
                func.count(ExpenseModel.id).label("count"),
            )
            .filter(
                ExpenseModel.user_id == user_id,
                ExpenseModel.entry_type == "debit",
                extract("year", ExpenseModel.expense_date) >= start_year,
                extract("year", ExpenseModel.expense_date) <= end_year,
            )
            .group_by(extract("year", ExpenseModel.expense_date))
            .order_by(extract("year", ExpenseModel.expense_date).asc())
            .all()
        )
        return [
            {
                "year": int(r[0]),
                "total_amount": float(r[1] or 0),
                "count": r[2],
            }
            for r in rows
        ]

    def get_category_totals(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, any]]:
        query = (
            self.db.query(
                ExpenseModel.category_id,
                CategoryModel.name_key,
                CategoryModel.icon_key,
                func.sum(ExpenseModel.amount).label("total_amount"),
                func.count(ExpenseModel.id).label("count"),
            )
            .join(CategoryModel, ExpenseModel.category_id == CategoryModel.id)
            .filter(
                ExpenseModel.user_id == user_id,
                ExpenseModel.entry_type == "debit",
            )
        )
        if start_date:
            query = query.filter(ExpenseModel.expense_date >= start_date)
        if end_date:
            query = query.filter(ExpenseModel.expense_date <= end_date)

        rows = (
            query.group_by(
                ExpenseModel.category_id,
                CategoryModel.name_key,
                CategoryModel.icon_key,
            )
            .order_by(desc("total_amount"))
            .all()
        )

        total_sum = sum(Decimal(str(r[3] or 0)) for r in rows)
        return [
            {
                "category_id": str(r[0]),
                "name_key": r[1],
                "icon_key": r[2],
                "total_amount": float(r[3] or 0),
                "count": r[4],
                "percentage": (
                    float(round((Decimal(str(r[3] or 0)) / total_sum) * 100, 2))
                    if total_sum > 0
                    else 0.0
                ),
            }
            for r in rows
        ]
