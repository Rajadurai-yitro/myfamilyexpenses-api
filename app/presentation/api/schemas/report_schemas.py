from typing import Dict, List, Optional
from pydantic import BaseModel
from app.presentation.api.schemas.expense_schemas import ExpenseResponse


class CategorySummaryItem(BaseModel):
    category_id: str
    name_key: str
    icon_key: str
    total_amount: float
    count: int
    percentage: float


class SummaryReportResponse(BaseModel):
    opening_balance: float
    total_income: float
    total_expense: float
    remaining_balance: float
    today_expense: float
    current_month_expense: float
    currency_code: str
    recent_expenses: List[ExpenseResponse]
    category_summary: List[CategorySummaryItem]


class DailyReportItem(BaseModel):
    date: str
    total_amount: float
    count: int


class MonthlyReportItem(BaseModel):
    month: int
    total_amount: float
    count: int


class YearlyReportItem(BaseModel):
    year: int
    total_amount: float
    count: int
