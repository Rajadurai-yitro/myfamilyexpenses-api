from datetime import date
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.application.expenses.expense_usecases import (
    AttachReceiptUseCase,
    CreateExpenseUseCase,
    DeleteExpenseUseCase,
    GetExpenseUseCase,
    ListExpensesUseCase,
    UpdateExpenseUseCase,
)
from app.core.exceptions import EntityNotFoundException
from app.domain.entities.expense import Expense
from app.infrastructure.storage.receipt_storage import receipt_file
from app.core.dependencies import (
    get_category_repository,
    get_current_user,
    get_expense_repository,
)
from app.domain.entities.user import User
from app.infrastructure.database.repositories.sqlalchemy_category_repo import (
    SqlAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_expense_repo import (
    SqlAlchemyExpenseRepository,
)
from app.presentation.api.schemas.common_schemas import (
    MessageResponse,
    PaginatedResponse,
)
from app.presentation.api.schemas.expense_schemas import (
    ExpenseCreateRequest,
    ExpenseResponse,
    ExpenseUpdateRequest,
)

router = APIRouter(prefix="/api/v1/expenses", tags=["Expenses"])


def _expense_response(expense: Expense) -> ExpenseResponse:
    receipt_url = None
    if expense.receipt_path:
        receipt_url = f"/api/v1/expenses/{expense.id}/receipt"
    return ExpenseResponse(
        id=expense.id,
        user_id=expense.user_id,
        category_id=expense.category_id,
        amount=float(expense.amount),
        description=expense.description,
        expense_date=expense.expense_date,
        entry_type=expense.entry_type,
        payment_mode=expense.payment_mode,
        transaction_id=expense.transaction_id,
        online_payment_type=expense.online_payment_type,
        receipt_url=receipt_url,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    req: ExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
    category_repo: SqlAlchemyCategoryRepository = Depends(get_category_repository),
):
    usecase = CreateExpenseUseCase(expense_repo, category_repo)
    expense = usecase.execute(
        user_id=current_user.id,
        category_id=req.category_id,
        amount=req.amount,
        expense_date=req.expense_date,
        description=req.description,
        entry_type=req.entry_type,
        payment_mode=req.payment_mode,
        transaction_id=req.transaction_id,
        online_payment_type=req.online_payment_type,
    )
    return _expense_response(expense)


@router.get("", response_model=PaginatedResponse[ExpenseResponse])
def list_expenses(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[uuid.UUID] = None,
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = ListExpensesUseCase(expense_repo)
    expenses, total = usecase.execute(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        search=search,
        skip=skip,
        limit=limit,
    )
    items = [_expense_response(e) for e in expenses]
    return PaginatedResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = GetExpenseUseCase(expense_repo)
    expense = usecase.execute(expense_id, current_user.id)
    return _expense_response(expense)


@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: uuid.UUID,
    req: ExpenseUpdateRequest,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
    category_repo: SqlAlchemyCategoryRepository = Depends(get_category_repository),
):
    usecase = UpdateExpenseUseCase(expense_repo, category_repo)
    expense = usecase.execute(
        expense_id=expense_id,
        user_id=current_user.id,
        category_id=req.category_id,
        amount=req.amount,
        expense_date=req.expense_date,
        description=req.description,
        payment_mode=req.payment_mode,
        transaction_id=req.transaction_id,
        online_payment_type=req.online_payment_type,
    )
    return _expense_response(expense)


@router.post("/{expense_id}/receipt", response_model=ExpenseResponse)
def upload_receipt(
    expense_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    data = file.file.read()
    expense = AttachReceiptUseCase(expense_repo).execute(
        expense_id=expense_id,
        user_id=current_user.id,
        data=data,
        content_type=file.content_type,
    )
    return _expense_response(expense)


@router.get("/{expense_id}/receipt")
def download_receipt(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    expense = GetExpenseUseCase(expense_repo).execute(expense_id, current_user.id)
    if not expense.receipt_path:
        raise EntityNotFoundException("Receipt", expense_id)
    path = receipt_file(expense.receipt_path)
    if path is None:
        raise EntityNotFoundException("Receipt", expense_id)
    return FileResponse(path)


@router.delete("/{expense_id}", response_model=MessageResponse)
def delete_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
):
    usecase = DeleteExpenseUseCase(expense_repo)
    usecase.execute(expense_id, current_user.id)
    return MessageResponse(message="Expense deleted successfully")
