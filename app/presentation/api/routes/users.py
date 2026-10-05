from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from app.application.auth.auth_usecases import GetCurrentUserUseCase
from app.application.profile.profile_usecases import ProfileUseCases
from app.core.dependencies import get_current_user, get_user_repository
from app.core.exceptions import EntityNotFoundException
from app.domain.entities.user import User
from app.infrastructure.database.repositories.sqlalchemy_user_repo import (
    SqlAlchemyUserRepository,
)
from app.infrastructure.storage.avatar_storage import avatar_file
from app.presentation.api.schemas.auth_schemas import (
    settings_to_response,
    user_to_response,
)
from app.presentation.api.schemas.common_schemas import MessageResponse
from app.presentation.api.schemas.user_schemas import (
    UpdateProfileRequest,
    UpdateSettingsRequest,
)

router = APIRouter(prefix="/api/v1/users", tags=["Users"])


@router.get("/me")
def get_me(
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    result = GetCurrentUserUseCase(user_repo).execute(current_user.id)
    return {
        "user": user_to_response(result["user"]),
        "settings": settings_to_response(result["settings"]),
    }


@router.patch("/me")
def update_profile(
    req: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    updated = ProfileUseCases(user_repo).update_profile(current_user.id, req.display_name)
    return user_to_response(updated["user"])


@router.patch("/me/settings")
def update_settings(
    req: UpdateSettingsRequest,
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    settings = ProfileUseCases(user_repo).update_settings(
        user_id=current_user.id,
        language_code=req.language_code,
        theme_mode=req.theme_mode,
        theme_color=req.theme_color,
        currency_code=req.currency_code,
        time_zone=req.time_zone,
        opening_balance=req.opening_balance,
    )
    return settings_to_response(settings)


@router.post("/me/avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    updated = ProfileUseCases(user_repo).set_avatar(
        current_user.id,
        file.file.read(),
        file.content_type,
    )
    return user_to_response(updated)


@router.get("/me/avatar")
def download_avatar(
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    user = user_repo.get_by_id(current_user.id)
    path = avatar_file(user.avatar_path if user else None)
    if path is None:
        raise EntityNotFoundException("Avatar", current_user.id)
    return FileResponse(path)


@router.delete("/me/avatar")
def remove_avatar(
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    updated = ProfileUseCases(user_repo).clear_avatar(current_user.id)
    return user_to_response(updated)


@router.delete("/me", response_model=MessageResponse)
def delete_account(
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    ProfileUseCases(user_repo).delete_account(current_user.id)
    return MessageResponse(message="User account and all associated data permanently deleted")
