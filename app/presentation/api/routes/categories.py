from typing import List
from fastapi import APIRouter, Depends

from app.application.categories.category_usecases import (
    ListCategoriesUseCase,
    SeedCategoriesUseCase,
)
from app.core.dependencies import get_category_repository
from app.infrastructure.database.repositories.sqlalchemy_category_repo import (
    SqlAlchemyCategoryRepository,
)
from app.presentation.api.schemas.category_schemas import CategoryResponse

router = APIRouter(prefix="/api/v1/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
def list_categories(
    active_only: bool = True,
    category_repo: SqlAlchemyCategoryRepository = Depends(get_category_repository),
):
    usecase = ListCategoriesUseCase(category_repo)
    cats = usecase.execute(active_only=active_only)
    return [
        CategoryResponse(
            id=c.id,
            name_key=c.name_key,
            icon_key=c.icon_key,
            kind=c.kind,
            sort_order=c.sort_order,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in cats
    ]


@router.post("/seed", response_model=List[CategoryResponse])
def seed_categories(
    category_repo: SqlAlchemyCategoryRepository = Depends(get_category_repository),
):
    usecase = SeedCategoriesUseCase(category_repo)
    cats = usecase.execute()
    return [
        CategoryResponse(
            id=c.id,
            name_key=c.name_key,
            icon_key=c.icon_key,
            kind=c.kind,
            sort_order=c.sort_order,
            is_active=c.is_active,
            created_at=c.created_at,
        )
        for c in cats
    ]
