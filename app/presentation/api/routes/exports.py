from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.application.exports.export_excel_usecase import ExportExpensesExcelUseCase
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

router = APIRouter(prefix="/api/v1/exports", tags=["Exports"])


@router.get("/expenses.xlsx")
def export_expenses_excel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    expense_repo: SqlAlchemyExpenseRepository = Depends(get_expense_repository),
    category_repo: SqlAlchemyCategoryRepository = Depends(get_category_repository),
):
    usecase = ExportExpensesExcelUseCase(expense_repo, category_repo)
    buffer = usecase.execute(
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
    )

    filename = f"expenses_export_{date.today().isoformat()}.xlsx"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers,
    )
