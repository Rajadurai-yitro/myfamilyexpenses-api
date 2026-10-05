from abc import ABC, abstractmethod
from typing import Optional
import uuid

from app.domain.entities.user import User
from app.domain.entities.settings import UserSettings


class UserRepository(ABC):
    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional[User]:
        pass

    @abstractmethod
    def create(self, user: User) -> User:
        pass

    @abstractmethod
    def update(self, user: User) -> User:
        pass

    @abstractmethod
    def set_avatar_path(self, user_id: uuid.UUID, avatar_path: Optional[str]) -> User:
        pass

    @abstractmethod
    def delete(self, user_id: uuid.UUID) -> bool:
        pass

    @abstractmethod
    def get_settings(self, user_id: uuid.UUID) -> Optional[UserSettings]:
        pass

    @abstractmethod
    def save_settings(self, settings: UserSettings) -> UserSettings:
        pass

    @abstractmethod
    def store_refresh_token(self, user_id: uuid.UUID, token_hash: str, expires_at) -> None:
        pass

    @abstractmethod
    def revoke_refresh_tokens(self, user_id: uuid.UUID) -> None:
        pass
