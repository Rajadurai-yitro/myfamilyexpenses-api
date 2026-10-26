from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional
import uuid

from app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.domain.entities.group import (
    ONLINE_TYPES,
    PAYMENT_MODES,
    SETTLEMENT_METHODS,
    SPLIT_METHODS,
    ExpenseSettlement,
    ExpenseShare,
    GroupAuditEvent,
    GroupExpense,
    MemberBalance,
)
from app.domain.repositories.category_repository import CategoryRepository
from app.domain.repositories.group_repository import GroupRepository
from app.domain.services.split_calculator import (
    equal_split,
    exact_split,
    paise_to_rupees,
    percent_split,
    rupees_to_paise,
    shares_split,
)
from app.infrastructure.storage.group_attachment_storage import save_group_attachment


class GroupExpenseUseCases:
    def __init__(self, groups: GroupRepository, categories: CategoryRepository):
        self.groups = groups
        self.categories = categories

    def list_expenses(self, group_id: uuid.UUID, user_id: uuid.UUID) -> List[GroupExpense]:
        self._require_member(group_id, user_id)
        return self.groups.list_expenses(group_id)

    def get_expense(self, group_id: uuid.UUID, expense_id: uuid.UUID, user_id: uuid.UUID) -> GroupExpense:
        self._require_member(group_id, user_id)
        expense = self.groups.get_expense(expense_id)
        if not expense or expense.group_id != group_id:
            raise EntityNotFoundException("GroupExpense", expense_id)
        return expense

    def create_expense(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        category_id: uuid.UUID,
        amount: Decimal,
        expense_date: date,
        paid_by: uuid.UUID,
        participant_ids: List[uuid.UUID],
        split_method: str,
        description: Optional[str],
        payment_mode: str,
        online_payment_type: Optional[str],
        percents: Optional[Dict[uuid.UUID, Decimal]],
        exact_amounts: Optional[Dict[uuid.UUID, Decimal]],
        shares: Optional[Dict[uuid.UUID, int]],
        client_request_id: Optional[str],
    ) -> GroupExpense:
        self._require_member(group_id, user_id)
        request_id = (client_request_id or "").strip() or None
        if request_id:
            existing = self.groups.get_expense_by_request(group_id, user_id, request_id)
            if existing:
                return existing
        self.groups.lock_group(group_id)
        members = set(self.groups.list_active_member_ids(group_id))
        if paid_by not in members:
            raise ValidationException("The payer must be an active group member")
        participants = list(dict.fromkeys(participant_ids))
        if not participants:
            raise ValidationException("Select at least one participant")
        missing = [item for item in participants if item not in members]
        if missing:
            raise ValidationException("Every participant must be an active group member")
        category = self.categories.get_by_id(category_id)
        if not category:
            raise EntityNotFoundException("Category", category_id)
        if category.kind != "debit":
            raise ValidationException("Shared expenses must use a spending category")
        method = (split_method or "equal").strip().lower()
        if method not in SPLIT_METHODS:
            raise ValidationException("Choose a valid split method")
        total_paise = rupees_to_paise(amount)
        if total_paise <= 0:
            raise ValidationException("Expense amount must be greater than zero")
        share_map = _compute_shares(method, total_paise, participants, percents, exact_amounts, shares)
        mode, online_type = _normalize_payment(payment_mode, online_payment_type)
        now = datetime.utcnow()
        expense = GroupExpense(
            id=uuid.uuid4(),
            group_id=group_id,
            paid_by=paid_by,
            created_by=user_id,
            category_id=category_id,
            amount=paise_to_rupees(total_paise),
            description=(description or "").strip() or None,
            expense_date=expense_date,
            payment_mode=mode,
            online_payment_type=online_type,
            split_method=method,
            client_request_id=request_id,
            receipt_path=None,
            created_at=now,
            updated_at=now,
            shares=[
                ExpenseShare(
                    user_id=uid,
                    amount=paise_to_rupees(share_map[uid]),
                    percent=(percents or {}).get(uid),
                    shares=(shares or {}).get(uid),
                )
                for uid in participants
            ],
        )
        saved = self.groups.create_expense(expense)
        self._audit(
            group_id,
            user_id,
            "expense_added",
            {"expense_id": str(saved.id), "amount": str(saved.amount)},
        )
        return saved

    def attach_receipt(
        self,
        group_id: uuid.UUID,
        expense_id: uuid.UUID,
        user_id: uuid.UUID,
        data: bytes,
        content_type: Optional[str],
    ) -> GroupExpense:
        expense = self.get_expense(group_id, expense_id, user_id)
        try:
            expense.receipt_path = save_group_attachment(group_id, expense_id, data, content_type)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        return self.groups.update_expense(expense)

    def delete_expense(self, group_id: uuid.UUID, expense_id: uuid.UUID, user_id: uuid.UUID) -> None:
        expense = self.get_expense(group_id, expense_id, user_id)
        membership = self.groups.get_membership(group_id, user_id)
        if expense.created_by != user_id and membership.role != "admin":
            raise ForbiddenException("Only the creator or an administrator can delete this expense")
        self.groups.delete_expense(expense_id)
        self._audit(group_id, user_id, "expense_deleted", {"expense_id": str(expense_id)})

    def list_balances(self, group_id: uuid.UUID, user_id: uuid.UUID) -> List[MemberBalance]:
        self._require_member(group_id, user_id)
        return self.groups.list_balances(group_id)

    def list_settlements(self, group_id: uuid.UUID, user_id: uuid.UUID) -> List[ExpenseSettlement]:
        self._require_member(group_id, user_id)
        return self.groups.list_settlements(group_id)

    def create_settlement(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        from_user_id: uuid.UUID,
        to_user_id: uuid.UUID,
        amount: Decimal,
        method: str,
        note: Optional[str],
        client_request_id: Optional[str],
    ) -> ExpenseSettlement:
        self._require_member(group_id, user_id)
        request_id = (client_request_id or "").strip() or None
        if request_id:
            existing = self.groups.get_settlement_by_request(group_id, user_id, request_id)
            if existing:
                return existing
        if from_user_id == to_user_id:
            raise ValidationException("A settlement needs two different people")
        members = set(self.groups.list_active_member_ids(group_id))
        if from_user_id not in members or to_user_id not in members:
            raise ValidationException("Both people must be active group members")
        if user_id not in {from_user_id, to_user_id}:
            raise ForbiddenException("You can only record a payment you are part of")
        pay_method = (method or "").strip().lower()
        if pay_method not in SETTLEMENT_METHODS:
            raise ValidationException("Choose a valid settlement method")
        paise = rupees_to_paise(amount)
        if paise <= 0:
            raise ValidationException("Settlement amount must be greater than zero")
        self.groups.lock_group(group_id)
        outstanding = self.groups.pair_outstanding_paise(group_id, from_user_id, to_user_id)
        if paise > outstanding:
            raise ValidationException("That amount is more than the outstanding balance")
        settlement = ExpenseSettlement(
            id=uuid.uuid4(),
            group_id=group_id,
            from_user_id=from_user_id,
            to_user_id=to_user_id,
            amount=paise_to_rupees(paise),
            method=pay_method,
            recording_kind="manual",
            client_request_id=request_id,
            created_by=user_id,
            note=(note or "").strip() or None,
            created_at=datetime.utcnow(),
        )
        saved = self.groups.create_settlement(settlement)
        self._audit(
            group_id,
            user_id,
            "payment_recorded",
            {
                "settlement_id": str(saved.id),
                "amount": str(saved.amount),
                "recording_kind": "manual",
            },
        )
        return saved

    def _require_member(self, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
        group = self.groups.get_group(group_id)
        if not group:
            raise EntityNotFoundException("Group", group_id)
        membership = self.groups.get_membership(group_id, user_id)
        if not membership or membership.status != "active":
            raise ForbiddenException("You are not a member of this group")

    def _audit(self, group_id: uuid.UUID, actor_id: uuid.UUID, action: str, payload: dict) -> None:
        self.groups.add_audit(
            GroupAuditEvent(
                id=uuid.uuid4(),
                group_id=group_id,
                actor_id=actor_id,
                action=action,
                payload=payload,
                created_at=datetime.utcnow(),
            )
        )


def _compute_shares(
    method: str,
    total_paise: int,
    participants: List[uuid.UUID],
    percents: Optional[Dict[uuid.UUID, Decimal]],
    exact_amounts: Optional[Dict[uuid.UUID, Decimal]],
    shares: Optional[Dict[uuid.UUID, int]],
) -> Dict[uuid.UUID, int]:
    try:
        if method == "equal":
            return equal_split(total_paise, participants)
        if method == "percent":
            if not percents or set(percents) != set(participants):
                raise ValueError("Enter a percentage for every selected participant")
            return percent_split(total_paise, percents)
        if method == "exact":
            if not exact_amounts or set(exact_amounts) != set(participants):
                raise ValueError("Enter an amount for every selected participant")
            mapped = {uid: rupees_to_paise(value) for uid, value in exact_amounts.items()}
            return exact_split(total_paise, mapped)
        if not shares or set(shares) != set(participants):
            raise ValueError("Enter shares for every selected participant")
        return shares_split(total_paise, shares)
    except ValueError as exc:
        raise ValidationException(str(exc)) from exc


def _normalize_payment(payment_mode: str, online_payment_type: Optional[str]):
    mode = (payment_mode or "cash").strip().lower()
    if mode not in PAYMENT_MODES:
        raise ValidationException("payment_mode must be cash or online")
    if mode == "cash":
        return "cash", None
    online_type = (online_payment_type or "").strip().lower() or None
    if online_type and online_type not in ONLINE_TYPES:
        raise ValidationException("Choose a valid original payment method")
    return mode, online_type
