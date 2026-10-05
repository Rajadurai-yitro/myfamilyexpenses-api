from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.domain.entities.settings import UserSettings
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.database.models.user_model import UserModel
from app.infrastructure.database.models.settings_model import UserSettingsModel
from app.infrastructure.database.models.token_model import RefreshTokenModel


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, db: Session):
        self.db = db

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            email=model.email,
            password_hash=model.password_hash,
            display_name=model.display_name,
            is_active=model.is_active,
            email_verified=model.email_verified,
            created_at=model.created_at,
            updated_at=model.updated_at,
            avatar_path=model.avatar_path,
        )

    def _to_settings_entity(self, model: UserSettingsModel) -> UserSettings:
        return UserSettings(
            user_id=model.user_id,
            language_code=model.language_code,
            theme_mode=model.theme_mode,
            theme_color=model.theme_color,
            currency_code=model.currency_code,
            time_zone=model.time_zone,
            opening_balance=Decimal(str(model.opening_balance)),
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        return self._to_entity(model) if model else None

    def get_by_email(self, email: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.email == email.strip().lower()).first()
        return self._to_entity(model) if model else None

    def create(self, user: User) -> User:
        model = UserModel(
            id=user.id,
            email=user.email,
            password_hash=user.password_hash,
            display_name=user.display_name,
            is_active=user.is_active,
            email_verified=user.email_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def update(self, user: User) -> User:
        model = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if not model:
            raise ValueError("User does not exist")
        model.display_name = user.display_name
        model.password_hash = user.password_hash
        model.is_active = user.is_active
        model.email_verified = user.email_verified
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def set_avatar_path(self, user_id: uuid.UUID, avatar_path: Optional[str]) -> User:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            raise ValueError("User does not exist")
        model.avatar_path = avatar_path
        model.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(model)
        return self._to_entity(model)

    def delete(self, user_id: uuid.UUID) -> bool:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if not model:
            return False
        self.db.delete(model)
        self.db.commit()
        return True

    def get_settings(self, user_id: uuid.UUID) -> Optional[UserSettings]:
        model = self.db.query(UserSettingsModel).filter(UserSettingsModel.user_id == user_id).first()
        return self._to_settings_entity(model) if model else None

    def save_settings(self, settings: UserSettings) -> UserSettings:
        model = self.db.query(UserSettingsModel).filter(UserSettingsModel.user_id == settings.user_id).first()
        if not model:
            model = UserSettingsModel(
                user_id=settings.user_id,
                language_code=settings.language_code,
                theme_mode=settings.theme_mode,
                theme_color=settings.theme_color,
                currency_code=settings.currency_code,
                time_zone=settings.time_zone,
                opening_balance=settings.opening_balance,
                created_at=settings.created_at,
                updated_at=settings.updated_at,
            )
            self.db.add(model)
        else:
            model.language_code = settings.language_code
            model.theme_mode = settings.theme_mode
            model.theme_color = settings.theme_color
            model.currency_code = settings.currency_code
            model.time_zone = settings.time_zone
            model.opening_balance = settings.opening_balance
            model.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(model)
        return self._to_settings_entity(model)

    def store_refresh_token(self, user_id: uuid.UUID, token_hash: str, expires_at: datetime) -> None:
        token = RefreshTokenModel(
            id=uuid.uuid4(),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=datetime.utcnow(),
        )
        self.db.add(token)
        self.db.commit()

    def revoke_refresh_tokens(self, user_id: uuid.UUID) -> None:
        self.db.query(RefreshTokenModel).filter(
            RefreshTokenModel.user_id == user_id,
            RefreshTokenModel.revoked_at.is_(None),
        ).update({"revoked_at": datetime.utcnow()})
        self.db.commit()
