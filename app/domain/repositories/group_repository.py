from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Sequence, Tuple
import uuid

from app.domain.entities.group import (
    ExpenseGroup,
    ExpenseSettlement,
    GroupAuditEvent,
    GroupExpense,
    GroupInvitation,
    MemberBalance,
)


class GroupRepository(ABC):
    @abstractmethod
    def create_group(self, group: ExpenseGroup, admin_user_id: uuid.UUID) -> ExpenseGroup:
        pass

    @abstractmethod
    def get_group(self, group_id: uuid.UUID) -> Optional[ExpenseGroup]:
        pass

    @abstractmethod
    def update_group(self, group: ExpenseGroup) -> ExpenseGroup:
        pass

    @abstractmethod
    def list_groups_for_user(self, user_id: uuid.UUID) -> List[ExpenseGroup]:
        pass

    @abstractmethod
    def list_discoverable(self, user_id: uuid.UUID) -> List[ExpenseGroup]:
        pass

    @abstractmethod
    def get_membership(self, group_id: uuid.UUID, user_id: uuid.UUID):
        pass

    @abstractmethod
    def list_active_member_ids(self, group_id: uuid.UUID) -> List[uuid.UUID]:
        pass

    @abstractmethod
    def add_membership(self, group_id: uuid.UUID, user_id: uuid.UUID, role: str) -> None:
        pass

    @abstractmethod
    def reactivate_membership(self, group_id: uuid.UUID, user_id: uuid.UUID, role: str) -> None:
        pass

    @abstractmethod
    def remove_membership(self, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
        pass

    @abstractmethod
    def count_active_admins(self, group_id: uuid.UUID) -> int:
        pass

    @abstractmethod
    def create_invitation(self, invitation: GroupInvitation) -> GroupInvitation:
        pass

    @abstractmethod
    def get_invitation(self, invitation_id: uuid.UUID) -> Optional[GroupInvitation]:
        pass

    @abstractmethod
    def get_pending_invitation(self, group_id: uuid.UUID, email: str) -> Optional[GroupInvitation]:
        pass

    @abstractmethod
    def update_invitation(self, invitation: GroupInvitation) -> GroupInvitation:
        pass

    @abstractmethod
    def list_pending_invitations_for_email(self, email: str) -> List[GroupInvitation]:
        pass

    @abstractmethod
    def expire_stale_invitations(self, now: datetime) -> None:
        pass

    @abstractmethod
    def get_expense_by_request(
        self, group_id: uuid.UUID, created_by: uuid.UUID, client_request_id: str
    ) -> Optional[GroupExpense]:
        pass

    @abstractmethod
    def create_expense(self, expense: GroupExpense) -> GroupExpense:
        pass

    @abstractmethod
    def get_expense(self, expense_id: uuid.UUID) -> Optional[GroupExpense]:
        pass

    @abstractmethod
    def update_expense(self, expense: GroupExpense) -> GroupExpense:
        pass

    @abstractmethod
    def delete_expense(self, expense_id: uuid.UUID) -> None:
        pass

    @abstractmethod
    def list_expenses(self, group_id: uuid.UUID, limit: int = 50) -> List[GroupExpense]:
        pass

    @abstractmethod
    def list_recent_expenses_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> List[GroupExpense]:
        pass

    @abstractmethod
    def group_expense_total(self, group_id: uuid.UUID) -> Decimal:
        pass

    @abstractmethod
    def create_settlement(self, settlement: ExpenseSettlement) -> ExpenseSettlement:
        pass

    @abstractmethod
    def get_settlement_by_request(
        self, group_id: uuid.UUID, created_by: uuid.UUID, client_request_id: str
    ) -> Optional[ExpenseSettlement]:
        pass

    @abstractmethod
    def list_settlements(self, group_id: uuid.UUID) -> List[ExpenseSettlement]:
        pass

    @abstractmethod
    def list_recent_settlements_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> List[ExpenseSettlement]:
        pass

    @abstractmethod
    def list_balances(self, group_id: uuid.UUID) -> List[MemberBalance]:
        pass

    @abstractmethod
    def pair_outstanding_paise(
        self, group_id: uuid.UUID, from_user_id: uuid.UUID, to_user_id: uuid.UUID
    ) -> int:
        pass

    @abstractmethod
    def add_audit(self, event: GroupAuditEvent) -> None:
        pass

    @abstractmethod
    def list_audit(self, group_id: uuid.UUID, limit: int = 50) -> List[GroupAuditEvent]:
        pass

    @abstractmethod
    def lock_group(self, group_id: uuid.UUID) -> None:
        pass
