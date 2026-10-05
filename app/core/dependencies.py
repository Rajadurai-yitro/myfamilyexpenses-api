from typing import Generator
import uuid
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_access_token
from app.domain.entities.user import User
from app.infrastructure.database.repositories.sqlalchemy_category_repo import (
    SqlAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_expense_repo import (
    SqlAlchemyExpenseRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_user_repo import (
    SqlAlchemyUserRepository,
)
from app.infrastructure.database.session import get_db

security_scheme = HTTPBearer(auto_error=False)


def get_user_repository(db: Session = Depends(get_db)) -> SqlAlchemyUserRepository:
    return SqlAlchemyUserRepository(db)


def get_category_repository(db: Session = Depends(get_db)) -> SqlAlchemyCategoryRepository:
    return SqlAlchemyCategoryRepository(db)


def get_expense_repository(db: Session = Depends(get_db)) -> SqlAlchemyExpenseRepository:
    return SqlAlchemyExpenseRepository(db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    user_repo: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> User:
    if not credentials or not credentials.credentials:
        raise UnauthorizedException("Authentication token required")

    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise UnauthorizedException("Malformed token subject")
        user_id = uuid.UUID(user_id_str)
    except Exception:
        raise UnauthorizedException("Invalid or expired authentication token")

    user = user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException("User not found")
    if not user.is_active:
        raise UnauthorizedException("User account is inactive")

    return user
