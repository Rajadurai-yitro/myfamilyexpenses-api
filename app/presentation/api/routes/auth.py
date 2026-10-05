from fastapi import APIRouter, Depends, status

from app.application.auth.auth_usecases import (
    ForgotPasswordUseCase,
    LoginUseCase,
    RefreshTokenUseCase,
    RegisterUseCase,
    ResetPasswordUseCase,
)
from app.core.dependencies import get_current_user, get_user_repository
from app.domain.entities.user import User
from app.infrastructure.database.repositories.sqlalchemy_user_repo import (
    SqlAlchemyUserRepository,
)
from app.presentation.api.schemas.auth_schemas import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    ResetPasswordRequest,
    settings_to_response,
    user_to_response,
)
from app.presentation.api.schemas.common_schemas import MessageResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    req: RegisterRequest,
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    usecase = RegisterUseCase(user_repo)
    result = usecase.execute(
        email=req.email,
        password=req.password,
        display_name=req.display_name,
    )
    user = result["user"]
    settings = result["settings"]
    return AuthResponse(
        user=user_to_response(user),
        settings=settings_to_response(settings),
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.post("/login", response_model=AuthResponse)
def login(
    req: LoginRequest,
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    usecase = LoginUseCase(user_repo)
    result = usecase.execute(email=req.email, password=req.password)
    user = result["user"]
    settings = result["settings"]
    return AuthResponse(
        user=user_to_response(user),
        settings=settings_to_response(settings),
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type=result["token_type"],
    )


@router.post("/refresh")
def refresh_token(
    req: RefreshTokenRequest,
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    usecase = RefreshTokenUseCase(user_repo)
    return usecase.execute(req.refresh_token)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    req: ForgotPasswordRequest,
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    usecase = ForgotPasswordUseCase(user_repo)
    res = usecase.execute(req.email)
    return MessageResponse(message=res["message"])


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    req: ResetPasswordRequest,
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    usecase = ResetPasswordUseCase(user_repo)
    res = usecase.execute(email=req.email, new_password=req.new_password)
    return MessageResponse(message=res["message"])


@router.post("/logout", response_model=MessageResponse)
def logout(
    current_user: User = Depends(get_current_user),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
):
    user_repo.revoke_refresh_tokens(current_user.id)
    return MessageResponse(message="Successfully logged out")
