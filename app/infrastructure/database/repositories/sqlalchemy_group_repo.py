from datetime import datetime
from decimal import Decimal
from typing import List, Optional
import json
import uuid
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.domain.entities.group import (
    ExpenseGroup,
    ExpenseSettlement,
    ExpenseShare,
    GroupAuditEvent,
    GroupExpense,
    GroupInvitation,
    GroupMember,
    MemberBalance,
)
from app.domain.repositories.group_repository import GroupRepository
from app.domain.services.split_calculator import rupees_to_paise
from app.infrastructure.database.models.group_models import (
    ExpenseGroupModel,
    ExpenseSettlementModel,
    ExpenseShareModel,
    GroupAuditEventModel,
    GroupExpenseModel,
    GroupInvitationModel,
    GroupMembershipModel,
)
from app.infrastructure.database.models.user_model import UserModel


class SqlAlchemyGroupRepository(GroupRepository):
    def __init__(self, db: Session):
        self.db = db

    def create_group(self, group: ExpenseGroup, admin_user_id: uuid.UUID) -> ExpenseGroup:
        model = ExpenseGroupModel(
            id=group.id,
            name=group.name,
            description=group.description,
            group_type=group.group_type,
            visibility=group.visibility,
            image_path=group.image_path,
            created_by=group.created_by,
            created_at=group.created_at,
            updated_at=group.updated_at,
        )
        self.db.add(model)
        self.db.add(
            GroupMembershipModel(
                group_id=group.id,
                user_id=admin_user_id,
                role="admin",
                status="active",
                joined_at=group.created_at,
            )
        )
        self.db.commit()
        return self.get_group(group.id)

    def get_group(self, group_id: uuid.UUID) -> Optional[ExpenseGroup]:
        model = self.db.query(ExpenseGroupModel).filter(ExpenseGroupModel.id == group_id).first()
        if not model:
            return None
        return self._group_entity(model, include_members=True)

    def update_group(self, group: ExpenseGroup) -> ExpenseGroup:
        model = self.db.query(ExpenseGroupModel).filter(ExpenseGroupModel.id == group.id).first()
        model.name = group.name
        model.description = group.description
        model.group_type = group.group_type
        model.visibility = group.visibility
        model.image_path = group.image_path
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return self.get_group(group.id)

    def list_groups_for_user(self, user_id: uuid.UUID) -> List[ExpenseGroup]:
        rows = (
            self.db.query(ExpenseGroupModel)
            .join(GroupMembershipModel)
            .filter(
                GroupMembershipModel.user_id == user_id,
                GroupMembershipModel.status == "active",
            )
            .order_by(desc(ExpenseGroupModel.updated_at))
            .all()
        )
        return [self._group_entity(row, include_members=True) for row in rows]

    def list_discoverable(self, user_id: uuid.UUID) -> List[ExpenseGroup]:
        rows = (
            self.db.query(ExpenseGroupModel)
            .filter(ExpenseGroupModel.visibility == "discoverable")
            .order_by(ExpenseGroupModel.name)
            .all()
        )
        return [self._group_entity(row, include_members=False) for row in rows]

    def get_membership(self, group_id: uuid.UUID, user_id: uuid.UUID):
        return (
            self.db.query(GroupMembershipModel)
            .filter(
                GroupMembershipModel.group_id == group_id,
                GroupMembershipModel.user_id == user_id,
            )
            .first()
        )

    def list_active_member_ids(self, group_id: uuid.UUID) -> List[uuid.UUID]:
        rows = (
            self.db.query(GroupMembershipModel.user_id)
            .filter(
                GroupMembershipModel.group_id == group_id,
                GroupMembershipModel.status == "active",
            )
            .all()
        )
        return [row[0] for row in rows]

    def add_membership(self, group_id: uuid.UUID, user_id: uuid.UUID, role: str) -> None:
        self.db.add(
            GroupMembershipModel(
                group_id=group_id,
                user_id=user_id,
                role=role,
                status="active",
                joined_at=datetime.utcnow(),
            )
        )
        self.db.commit()

    def reactivate_membership(self, group_id: uuid.UUID, user_id: uuid.UUID, role: str) -> None:
        membership = self.get_membership(group_id, user_id)
        membership.role = role
        membership.status = "active"
        membership.joined_at = datetime.utcnow()
        self.db.commit()

    def remove_membership(self, group_id: uuid.UUID, user_id: uuid.UUID) -> None:
        membership = self.get_membership(group_id, user_id)
        if membership:
            membership.status = "removed"
            self.db.commit()

    def count_active_admins(self, group_id: uuid.UUID) -> int:
        return (
            self.db.query(func.count(GroupMembershipModel.id))
            .filter(
                GroupMembershipModel.group_id == group_id,
                GroupMembershipModel.status == "active",
                GroupMembershipModel.role == "admin",
            )
            .scalar()
            or 0
        )

    def create_invitation(self, invitation: GroupInvitation) -> GroupInvitation:
        model = GroupInvitationModel(
            id=invitation.id,
            group_id=invitation.group_id,
            email=invitation.email,
            invited_by=invitation.invited_by,
            invitee_user_id=invitation.invitee_user_id,
            status=invitation.status,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._invite_entity(model)

    def get_invitation(self, invitation_id: uuid.UUID) -> Optional[GroupInvitation]:
        model = (
            self.db.query(GroupInvitationModel)
            .filter(GroupInvitationModel.id == invitation_id)
            .first()
        )
        return self._invite_entity(model) if model else None

    def get_pending_invitation(self, group_id: uuid.UUID, email: str) -> Optional[GroupInvitation]:
        model = (
            self.db.query(GroupInvitationModel)
            .filter(
                GroupInvitationModel.group_id == group_id,
                GroupInvitationModel.email == email,
                GroupInvitationModel.status == "pending",
            )
            .first()
        )
        return self._invite_entity(model) if model else None

    def update_invitation(self, invitation: GroupInvitation) -> GroupInvitation:
        model = (
            self.db.query(GroupInvitationModel)
            .filter(GroupInvitationModel.id == invitation.id)
            .first()
        )
        model.status = invitation.status
        model.invitee_user_id = invitation.invitee_user_id
        model.responded_at = invitation.responded_at
        self.db.commit()
        return self._invite_entity(model)

    def list_pending_invitations_for_email(self, email: str) -> List[GroupInvitation]:
        rows = (
            self.db.query(GroupInvitationModel)
            .filter(
                GroupInvitationModel.email == email,
                GroupInvitationModel.status == "pending",
            )
            .order_by(desc(GroupInvitationModel.created_at))
            .all()
        )
        return [self._invite_entity(row) for row in rows]

    def expire_stale_invitations(self, now: datetime) -> None:
        (
            self.db.query(GroupInvitationModel)
            .filter(
                GroupInvitationModel.status == "pending",
                GroupInvitationModel.expires_at < now,
            )
            .update({"status": "expired"}, synchronize_session=False)
        )
        self.db.commit()

    def get_expense_by_request(
        self, group_id: uuid.UUID, created_by: uuid.UUID, client_request_id: str
    ) -> Optional[GroupExpense]:
        model = (
            self.db.query(GroupExpenseModel)
            .options(joinedload(GroupExpenseModel.shares))
            .filter(
                GroupExpenseModel.group_id == group_id,
                GroupExpenseModel.created_by == created_by,
                GroupExpenseModel.client_request_id == client_request_id,
            )
            .first()
        )
        return self._expense_entity(model) if model else None

    def create_expense(self, expense: GroupExpense) -> GroupExpense:
        model = GroupExpenseModel(
            id=expense.id,
            group_id=expense.group_id,
            paid_by=expense.paid_by,
            created_by=expense.created_by,
            category_id=expense.category_id,
            amount=expense.amount,
            description=expense.description,
            expense_date=expense.expense_date,
            payment_mode=expense.payment_mode,
            online_payment_type=expense.online_payment_type,
            split_method=expense.split_method,
            client_request_id=expense.client_request_id,
            receipt_path=expense.receipt_path,
            created_at=expense.created_at,
            updated_at=expense.updated_at,
        )
        for share in expense.shares:
            model.shares.append(
                ExpenseShareModel(
                    expense_id=expense.id,
                    user_id=share.user_id,
                    amount=share.amount,
                    percent=share.percent,
                    shares=share.shares,
                )
            )
        self.db.add(model)
        self.db.commit()
        return self.get_expense(expense.id)

    def get_expense(self, expense_id: uuid.UUID) -> Optional[GroupExpense]:
        model = (
            self.db.query(GroupExpenseModel)
            .options(joinedload(GroupExpenseModel.shares), joinedload(GroupExpenseModel.category))
            .filter(GroupExpenseModel.id == expense_id)
            .first()
        )
        return self._expense_entity(model) if model else None

    def update_expense(self, expense: GroupExpense) -> GroupExpense:
        model = (
            self.db.query(GroupExpenseModel).filter(GroupExpenseModel.id == expense.id).first()
        )
        model.receipt_path = expense.receipt_path
        model.updated_at = datetime.utcnow()
        self.db.commit()
        return self.get_expense(expense.id)

    def delete_expense(self, expense_id: uuid.UUID) -> None:
        model = (
            self.db.query(GroupExpenseModel).filter(GroupExpenseModel.id == expense_id).first()
        )
        if model:
            self.db.delete(model)
            self.db.commit()

    def list_expenses(self, group_id: uuid.UUID, limit: int = 50) -> List[GroupExpense]:
        rows = (
            self.db.query(GroupExpenseModel)
            .options(joinedload(GroupExpenseModel.shares), joinedload(GroupExpenseModel.category))
            .filter(GroupExpenseModel.group_id == group_id)
            .order_by(desc(GroupExpenseModel.expense_date), desc(GroupExpenseModel.created_at))
            .limit(limit)
            .all()
        )
        return [self._expense_entity(row) for row in rows]

    def list_recent_expenses_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> List[GroupExpense]:
        rows = (
            self.db.query(GroupExpenseModel)
            .options(joinedload(GroupExpenseModel.shares), joinedload(GroupExpenseModel.category))
            .join(GroupMembershipModel, GroupMembershipModel.group_id == GroupExpenseModel.group_id)
            .filter(
                GroupMembershipModel.user_id == user_id,
                GroupMembershipModel.status == "active",
            )
            .order_by(desc(GroupExpenseModel.created_at))
            .limit(limit)
            .all()
        )
        return [self._expense_entity(row) for row in rows]

    def group_expense_total(self, group_id: uuid.UUID) -> Decimal:
        total = (
            self.db.query(func.coalesce(func.sum(GroupExpenseModel.amount), 0))
            .filter(GroupExpenseModel.group_id == group_id)
            .scalar()
        )
        return Decimal(str(total)).quantize(Decimal("0.01"))

    def create_settlement(self, settlement: ExpenseSettlement) -> ExpenseSettlement:
        model = ExpenseSettlementModel(
            id=settlement.id,
            group_id=settlement.group_id,
            from_user_id=settlement.from_user_id,
            to_user_id=settlement.to_user_id,
            amount=settlement.amount,
            method=settlement.method,
            recording_kind=settlement.recording_kind,
            client_request_id=settlement.client_request_id,
            created_by=settlement.created_by,
            note=settlement.note,
            created_at=settlement.created_at,
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._settlement_entity(model)

    def get_settlement_by_request(
        self, group_id: uuid.UUID, created_by: uuid.UUID, client_request_id: str
    ) -> Optional[ExpenseSettlement]:
        model = (
            self.db.query(ExpenseSettlementModel)
            .filter(
                ExpenseSettlementModel.group_id == group_id,
                ExpenseSettlementModel.created_by == created_by,
                ExpenseSettlementModel.client_request_id == client_request_id,
            )
            .first()
        )
        return self._settlement_entity(model) if model else None

    def list_settlements(self, group_id: uuid.UUID) -> List[ExpenseSettlement]:
        rows = (
            self.db.query(ExpenseSettlementModel)
            .filter(ExpenseSettlementModel.group_id == group_id)
            .order_by(desc(ExpenseSettlementModel.created_at))
            .all()
        )
        return [self._settlement_entity(row) for row in rows]

    def list_recent_settlements_for_user(
        self, user_id: uuid.UUID, limit: int = 20
    ) -> List[ExpenseSettlement]:
        rows = (
            self.db.query(ExpenseSettlementModel)
            .join(
                GroupMembershipModel,
                GroupMembershipModel.group_id == ExpenseSettlementModel.group_id,
            )
            .filter(
                GroupMembershipModel.user_id == user_id,
                GroupMembershipModel.status == "active",
                (ExpenseSettlementModel.from_user_id == user_id)
                | (ExpenseSettlementModel.to_user_id == user_id),
            )
            .order_by(desc(ExpenseSettlementModel.created_at))
            .limit(limit)
            .all()
        )
        return [self._settlement_entity(row) for row in rows]

    def list_balances(self, group_id: uuid.UUID) -> List[MemberBalance]:
        members = (
            self.db.query(GroupMembershipModel, UserModel)
            .join(UserModel, UserModel.id == GroupMembershipModel.user_id)
            .filter(
                GroupMembershipModel.group_id == group_id,
                GroupMembershipModel.status == "active",
            )
            .all()
        )
        paid = dict(
            self.db.query(GroupExpenseModel.paid_by, func.coalesce(func.sum(GroupExpenseModel.amount), 0))
            .filter(GroupExpenseModel.group_id == group_id)
            .group_by(GroupExpenseModel.paid_by)
            .all()
        )
        owed = dict(
            self.db.query(ExpenseShareModel.user_id, func.coalesce(func.sum(ExpenseShareModel.amount), 0))
            .join(GroupExpenseModel, GroupExpenseModel.id == ExpenseShareModel.expense_id)
            .filter(GroupExpenseModel.group_id == group_id)
            .group_by(ExpenseShareModel.user_id)
            .all()
        )
        settled_out = dict(
            self.db.query(
                ExpenseSettlementModel.from_user_id,
                func.coalesce(func.sum(ExpenseSettlementModel.amount), 0),
            )
            .filter(ExpenseSettlementModel.group_id == group_id)
            .group_by(ExpenseSettlementModel.from_user_id)
            .all()
        )
        settled_in = dict(
            self.db.query(
                ExpenseSettlementModel.to_user_id,
                func.coalesce(func.sum(ExpenseSettlementModel.amount), 0),
            )
            .filter(ExpenseSettlementModel.group_id == group_id)
            .group_by(ExpenseSettlementModel.to_user_id)
            .all()
        )
        balances = []
        for membership, user in members:
            uid = user.id
            net = (
                rupees_to_paise(Decimal(str(paid.get(uid, 0))))
                - rupees_to_paise(Decimal(str(owed.get(uid, 0))))
                + rupees_to_paise(Decimal(str(settled_out.get(uid, 0))))
                - rupees_to_paise(Decimal(str(settled_in.get(uid, 0))))
            )
            balances.append(
                MemberBalance(
                    user_id=uid,
                    display_name=user.display_name,
                    email=user.email,
                    net_paise=net,
                    has_avatar=bool(user.avatar_path),
                )
            )
        return balances

    def pair_outstanding_paise(
        self, group_id: uuid.UUID, from_user_id: uuid.UUID, to_user_id: uuid.UUID
    ) -> int:
        balances = {item.user_id: item.net_paise for item in self.list_balances(group_id)}
        debtor = balances.get(from_user_id, 0)
        creditor = balances.get(to_user_id, 0)
        if debtor >= 0 or creditor <= 0:
            return 0
        return min(-debtor, creditor)

    def add_audit(self, event: GroupAuditEvent) -> None:
        self.db.add(
            GroupAuditEventModel(
                id=event.id,
                group_id=event.group_id,
                actor_id=event.actor_id,
                action=event.action,
                payload=json.dumps(event.payload),
                created_at=event.created_at,
            )
        )
        self.db.commit()

    def list_audit(self, group_id: uuid.UUID, limit: int = 50) -> List[GroupAuditEvent]:
        rows = (
            self.db.query(GroupAuditEventModel)
            .filter(GroupAuditEventModel.group_id == group_id)
            .order_by(desc(GroupAuditEventModel.created_at))
            .limit(limit)
            .all()
        )
        return [
            GroupAuditEvent(
                id=row.id,
                group_id=row.group_id,
                actor_id=row.actor_id,
                action=row.action,
                payload=json.loads(row.payload) if row.payload else {},
                created_at=row.created_at,
            )
            for row in rows
        ]

    def lock_group(self, group_id: uuid.UUID) -> None:
        (
            self.db.query(ExpenseGroupModel)
            .filter(ExpenseGroupModel.id == group_id)
            .with_for_update()
            .first()
        )

    def _group_entity(self, model: ExpenseGroupModel, include_members: bool) -> ExpenseGroup:
        members: List[GroupMember] = []
        if include_members:
            rows = (
                self.db.query(GroupMembershipModel, UserModel)
                .join(UserModel, UserModel.id == GroupMembershipModel.user_id)
                .filter(
                    GroupMembershipModel.group_id == model.id,
                    GroupMembershipModel.status == "active",
                )
                .all()
            )
            members = [
                GroupMember(
                    user_id=user.id,
                    role=membership.role,
                    status=membership.status,
                    email=user.email,
                    display_name=user.display_name,
                    has_avatar=bool(user.avatar_path),
                    joined_at=membership.joined_at,
                )
                for membership, user in rows
            ]
        count = (
            self.db.query(func.count(GroupMembershipModel.id))
            .filter(
                GroupMembershipModel.group_id == model.id,
                GroupMembershipModel.status == "active",
            )
            .scalar()
            or 0
        )
        return ExpenseGroup(
            id=model.id,
            name=model.name,
            description=model.description,
            group_type=model.group_type,
            visibility=model.visibility,
            image_path=model.image_path,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
            members=members,
            total_expenses=self.group_expense_total(model.id),
            member_count=count,
        )

    def _invite_entity(self, model: GroupInvitationModel) -> GroupInvitation:
        group = (
            self.db.query(ExpenseGroupModel)
            .filter(ExpenseGroupModel.id == model.group_id)
            .first()
        )
        return GroupInvitation(
            id=model.id,
            group_id=model.group_id,
            email=model.email,
            invited_by=model.invited_by,
            invitee_user_id=model.invitee_user_id,
            status=model.status,
            expires_at=model.expires_at,
            created_at=model.created_at,
            responded_at=model.responded_at,
            group_name=group.name if group else None,
        )

    def _expense_entity(self, model: GroupExpenseModel) -> GroupExpense:
        payer = self.db.query(UserModel).filter(UserModel.id == model.paid_by).first()
        group = (
            self.db.query(ExpenseGroupModel)
            .filter(ExpenseGroupModel.id == model.group_id)
            .first()
        )
        category = model.category
        return GroupExpense(
            id=model.id,
            group_id=model.group_id,
            paid_by=model.paid_by,
            created_by=model.created_by,
            category_id=model.category_id,
            amount=Decimal(str(model.amount)),
            description=model.description,
            expense_date=model.expense_date,
            payment_mode=model.payment_mode,
            online_payment_type=model.online_payment_type,
            split_method=model.split_method,
            client_request_id=model.client_request_id,
            receipt_path=model.receipt_path,
            created_at=model.created_at,
            updated_at=model.updated_at,
            shares=[
                ExpenseShare(
                    user_id=share.user_id,
                    amount=Decimal(str(share.amount)),
                    percent=Decimal(str(share.percent)) if share.percent is not None else None,
                    shares=share.shares,
                )
                for share in model.shares
            ],
            payer_name=(payer.display_name or payer.email) if payer else None,
            category_name_key=category.name_key if category else None,
            category_icon_key=category.icon_key if category else None,
            group_name=group.name if group else None,
        )

    def _settlement_entity(self, model: ExpenseSettlementModel) -> ExpenseSettlement:
        from_user = self.db.query(UserModel).filter(UserModel.id == model.from_user_id).first()
        to_user = self.db.query(UserModel).filter(UserModel.id == model.to_user_id).first()
        return ExpenseSettlement(
            id=model.id,
            group_id=model.group_id,
            from_user_id=model.from_user_id,
            to_user_id=model.to_user_id,
            amount=Decimal(str(model.amount)),
            method=model.method,
            recording_kind=model.recording_kind,
            client_request_id=model.client_request_id,
            created_by=model.created_by,
            note=model.note,
            created_at=model.created_at,
            from_name=(from_user.display_name or from_user.email) if from_user else None,
            to_name=(to_user.display_name or to_user.email) if to_user else None,
        )
