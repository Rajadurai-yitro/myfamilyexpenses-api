from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from app.core.config import settings as app_settings
from app.domain.repositories.expense_repository import ExpenseRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.balance_calculator import BalanceCalculator


class GetSummaryReportUseCase:
    def __init__(self, expense_repo: ExpenseRepository, user_repo: UserRepository):
        self.expense_repo = expense_repo
        self.user_repo = user_repo

    def execute(self, user_id: uuid.UUID) -> Dict[str, any]:
        today = date.today()
        first_day_of_month = today.replace(day=1)

        # Get settings for opening balance
        settings = self.user_repo.get_settings(user_id)
        opening_balance = settings.opening_balance if settings else Decimal("0.00")

        # Debit is spending. Credit is income.
        today_expense = self.expense_repo.get_total_between(
            user_id, today, today, entry_type="debit"
        )
        month_expense = self.expense_repo.get_total_between(
            user_id, first_day_of_month, today, entry_type="debit"
        )
        all_time_expense = self.expense_repo.get_total_between(
            user_id, None, None, entry_type="debit"
        )
        total_income = self.expense_repo.get_total_between(
            user_id, None, None, entry_type="credit"
        )

        balance_metrics = BalanceCalculator.calculate_remaining(
            opening_balance=opening_balance,
            total_income=total_income,
            total_expense=all_time_expense,
        )

        # Top recent expenses (last 5)
        recent_expenses, _ = self.expense_repo.list(user_id=user_id, skip=0, limit=5)

        # Top category totals for current month
        categories_breakdown = self.expense_repo.get_category_totals(
            user_id=user_id,
            start_date=first_day_of_month,
            end_date=today,
        )

        return {
            "opening_balance": float(balance_metrics["opening_balance"]),
            "total_income": float(balance_metrics["total_income"]),
            "total_expense": float(balance_metrics["total_expense"]),
            "remaining_balance": float(balance_metrics["remaining_balance"]),
            "today_expense": float(today_expense),
            "current_month_expense": float(month_expense),
            "currency_code": settings.currency_code if settings else app_settings.DEFAULT_CURRENCY,
            "recent_expenses": recent_expenses,
            "category_summary": categories_breakdown,
        }


class GetDailyReportUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(self, user_id: uuid.UUID, year: int, month: int) -> List[Dict[str, any]]:
        return self.expense_repo.get_daily_totals(user_id, year, month)


class GetMonthlyReportUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(self, user_id: uuid.UUID, year: int) -> List[Dict[str, any]]:
        return self.expense_repo.get_monthly_totals(user_id, year)


class GetYearlyReportUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(self, user_id: uuid.UUID, start_year: int, end_year: int) -> List[Dict[str, any]]:
        return self.expense_repo.get_yearly_totals(user_id, start_year, end_year)


class GetCategoryReportUseCase:
    def __init__(self, expense_repo: ExpenseRepository):
        self.expense_repo = expense_repo

    def execute(
        self,
        user_id: uuid.UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, any]]:
        return self.expense_repo.get_category_totals(user_id, start_date, end_date)
