from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import uuid

from app.core.exceptions import (
    EntityNotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.domain.entities.expense import Expense
from app.domain.repositories.category_repository import CategoryRepository
from app.domain.repositories.expense_repository import ExpenseRepository
from app.infrastructure.storage.receipt_storage import save_receipt


class CreateExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository, category_repo: CategoryRepository):
        self.expense_repo = expense_repo
        self.category_repo = category_repo

    def execute(
        self,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        amount: Decimal,
        expense_date: date,
        description: Optional[str] = None,
        entry_type: str = "debit",
        payment_mode: str = "cash",
        transaction_id: Optional[str] = None,
        online_payment_type: Optional[str] = None,
    ) -> Expense:
        if amount <= Decimal("0.00"):
            raise ValidationException("Expense amount must be greater than zero")

        kind = _normalize_entry_type(entry_type)
        mode, txn, online_type = _normalize_payment(
            payment_mode, transaction_id, online_payment_type
        )
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise EntityNotFoundException("Category", category_id)
        if category.kind != kind:
            raise ValidationException(
                "Choose a debit category for spending, or a credit category for income"
            )

        expense = Expense.create(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            expense_date=expense_date,
            description=description,
            entry_type=kind,
            payment_mode=mode,
            transaction_id=txn,
            online_payment_type=online_type,
        )
        return self.expense_repo.create(expense)


class GetExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> Expense:
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise EntityNotFoundException("Expense", expense_id)

        # Strict user ownership check
        if expense.user_id != user_id:
            raise ForbiddenException("You do not have permission to view this expense")

        return expense


class ListExpensesUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        category_id: Optional[uuid.UUID] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Expense], int]:
        return self.expense_repo.list(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            search=search,
            skip=skip,
            limit=limit,
        )


class UpdateExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository, category_repo: CategoryRepository):
        self.expense_repo = expense_repo
        self.category_repo = category_repo

    def execute(
        self,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
        category_id: Optional[uuid.UUID] = None,
        amount: Optional[Decimal] = None,
        expense_date: Optional[date] = None,
        description: Optional[str] = None,
        payment_mode: Optional[str] = None,
        transaction_id: Optional[str] = None,
        online_payment_type: Optional[str] = None,
    ) -> Expense:
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise EntityNotFoundException("Expense", expense_id)

        # Strict ownership check
        if expense.user_id != user_id:
            raise ForbiddenException("You do not have permission to edit this expense")

        if category_id:
            category = self.category_repo.get_by_id(category_id)
            if not category:
                raise EntityNotFoundException("Category", category_id)
            expense.category_id = category_id
            expense.entry_type = category.kind

        if amount is not None:
            if amount <= Decimal("0.00"):
                raise ValidationException("Amount must be greater than zero")
            expense.amount = round(Decimal(str(amount)), 2)

        if expense_date is not None:
            expense.expense_date = expense_date

        if description is not None:
            expense.description = description.strip() if description.strip() else None

        if payment_mode is not None:
            mode, txn, online_type = _normalize_payment(
                payment_mode, transaction_id, online_payment_type
            )
            expense.payment_mode = mode
            expense.transaction_id = txn
            expense.online_payment_type = online_type

        return self.expense_repo.update(expense)


class DeleteExpenseUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(self, expense_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise EntityNotFoundException("Expense", expense_id)

        # Strict ownership check
        if expense.user_id != user_id:
            raise ForbiddenException("You do not have permission to delete this expense")

        return self.expense_repo.delete(expense_id)


_PAYMENT_MODES = {"cash", "online"}
_ONLINE_TYPES = {"upi", "neft", "card", "net_banking", "other"}


def _normalize_payment(
    payment_mode: Optional[str],
    transaction_id: Optional[str],
    online_payment_type: Optional[str],
):
    mode = (payment_mode or "cash").strip().lower()
    if mode not in _PAYMENT_MODES:
        raise ValidationException("payment_mode must be cash or online")
    if mode == "cash":
        return "cash", None, None
    txn = (transaction_id or "").strip()
    online_type = (online_payment_type or "").strip().lower()
    if not txn:
        raise ValidationException("Transaction ID is required for online payments")
    if len(txn) > 100:
        raise ValidationException("Transaction ID must be 100 characters or fewer")
    if online_type not in _ONLINE_TYPES:
        raise ValidationException("Choose an online payment type")
    return mode, txn, online_type


def _normalize_entry_type(entry_type: str) -> str:
    kind = (entry_type or "debit").strip().lower()
    if kind not in ("debit", "credit"):
        raise ValidationException("entry_type must be credit or debit")
    return kind


class AttachReceiptUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(
        self,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
        data: bytes,
        content_type: Optional[str],
    ) -> Expense:
        expense = self.expense_repo.get_by_id(expense_id)
        if not expense:
            raise EntityNotFoundException("Expense", expense_id)
        if expense.user_id != user_id:
            raise ForbiddenException("You do not have permission to edit this expense")
        try:
            expense.receipt_path = save_receipt(user_id, expense_id, data, content_type)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        return self.expense_repo.update(expense)
