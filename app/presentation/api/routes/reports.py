from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.application.reports.report_usecases import (
    GetCategoryReportUseCase,
    GetDailyReportUseCase,
    GetMonthlyReportUseCase,
    GetSummaryReportUseCase,
    GetYearlyReportUseCase,
)
from app.core.dependencies import (
    get_current_user,
    get_expense_repository,
    get_user_repository,
)
from app.domain.entities.user import User
from app.infrastructure.database.repositories.sqlalchemy_expense_repo import (
    SqlAlchemyExpenseRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_user_repo import (
    SqlAlchemyUserRepository,
)
from app.presentation.api.schemas.expense_schemas import ExpenseResponse
from app.presentation.api.schemas.report_schemas import (
    CategorySummaryItem,
    DailyReportItem,
    MonthlyReportItem,
    SummaryReportResponse,
    YearlyReportItem,
)

router = APIRouter(prefix="/api/v1/reports", tags=["Reports"])


@router.get("/summary", response_model=SummaryReportResponse)
def get_summary_report(
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    usecase = GetSummaryReportUseCase(expense_repo, user_repo)
    data = usecase.execute(current_user.id)
    return SummaryReportResponse(
        opening_balance=data["opening_balance"],
        total_income=data["total_income"],
        total_expense=data["total_expense"],
        remaining_balance=data["remaining_balance"],
        today_expense=data["today_expense"],
        current_month_expense=data["current_month_expense"],
        currency_code=data["currency_code"],
        recent_expenses=[
            ExpenseResponse(
                id=e.id,
                user_id=e.user_id,
                category_id=e.category_id,
                amount=float(e.amount),
                description=e.description,
                expense_date=e.expense_date,
                entry_type=e.entry_type,
                payment_mode=e.payment_mode,
                transaction_id=e.transaction_id,
                online_payment_type=e.online_payment_type,
                receipt_url=(
                    f"/api/v1/expenses/{e.id}/receipt" if e.receipt_path else None
                ),
                created_at=e.created_at,
                updated_at=e.updated_at,
            )
            for e in data["recent_expenses"]
        ],
        category_summary=[CategorySummaryItem(**item) for item in data["category_summary"]],
    )


@router.get("/daily", response_model=List[DailyReportItem])
def get_daily_report(
    year: int = Query(..., ge=2000, le=2100),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = GetDailyReportUseCase(expense_repo)
    data = usecase.execute(current_user.id, year, month)
    return [DailyReportItem(**item) for item in data]


@router.get("/monthly", response_model=List[MonthlyReportItem])
def get_monthly_report(
    year: int = Query(..., ge=2000, le=2100),
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = GetMonthlyReportUseCase(expense_repo)
    data = usecase.execute(current_user.id, year)
    return [MonthlyReportItem(**item) for item in data]


@router.get("/yearly", response_model=List[YearlyReportItem])
def get_yearly_report(
    start_year: int = Query(2020, ge=2000),
    end_year: int = Query(2030, le=2100),
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = GetYearlyReportUseCase(expense_repo)
    data = usecase.execute(current_user.id, start_year, end_year)
    return [YearlyReportItem(**item) for item in data]


@router.get("/categories", response_model=List[CategorySummaryItem])
def get_category_report(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = GetCategoryReportUseCase(expense_repo)
    data = usecase.execute(current_user.id, start_date, end_date)
    return [CategorySummaryItem(**item) for item in data]
