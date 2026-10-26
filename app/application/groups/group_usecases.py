from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import uuid

from app.core.exceptions import (
    ConflictException,
    EntityNotFoundException,
    ForbiddenException,
    ValidationException,
)
from app.domain.entities.group import (
    GROUP_TYPES,
    INVITE_STATUSES,
    VISIBILITIES,
    ExpenseGroup,
    GroupAuditEvent,
    GroupInvitation,
    GroupUpdate,
)
from app.domain.repositories.group_repository import GroupRepository
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.storage.group_attachment_storage import save_group_image


INVITE_DAYS = 14


class GroupUseCases:
    def __init__(self, groups: GroupRepository, users: UserRepository):
        self.groups = groups
        self.users = users

    def create_group(
        self,
        user_id: uuid.UUID,
        name: str,
        description: Optional[str],
        group_type: str,
        visibility: str,
        member_emails: List[str],
    ) -> ExpenseGroup:
        clean_name = _clean_name(name)
        kind = _one_of(group_type, GROUP_TYPES, "group type")
        vis = _one_of(visibility, VISIBILITIES, "visibility")
        group = ExpenseGroup.create(
            name=clean_name,
            created_by=user_id,
            description=_optional_text(description, 500),
            group_type=kind,
            visibility=vis,
        )
        saved = self.groups.create_group(group, user_id)
        self._audit(saved.id, user_id, "group_created", {"name": saved.name})
        creator = self.users.get_by_id(user_id)
        creator_email = creator.email if creator else ""
        for raw in member_emails or []:
            email = raw.strip().lower()
            if not email or email == creator_email:
                continue
            try:
                self.invite_member(saved.id, user_id, email)
            except ConflictException:
                continue
        return self.groups.get_group(saved.id)

    def list_my_groups(self, user_id: uuid.UUID) -> List[ExpenseGroup]:
        return self.groups.list_groups_for_user(user_id)

    def list_discoverable(self, user_id: uuid.UUID) -> List[ExpenseGroup]:
        return self.groups.list_discoverable(user_id)

    def get_group(self, group_id: uuid.UUID, user_id: uuid.UUID) -> ExpenseGroup:
        return self._require_member_group(group_id, user_id)

    def public_cover(self, group_id: uuid.UUID, user_id: uuid.UUID) -> ExpenseGroup:
        group = self.groups.get_group(group_id)
        if not group:
            raise EntityNotFoundException("Group", group_id)
        if group.visibility == "discoverable" or self._is_active_member(group_id, user_id):
            return group
        raise ForbiddenException("You are not a member of this group")

    def update_group(
        self,
        group_id: uuid.UUID,
        user_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        group_type: Optional[str] = None,
        visibility: Optional[str] = None,
    ) -> ExpenseGroup:
        group = self._require_admin_group(group_id, user_id)
        if name is not None:
            group.name = _clean_name(name)
        if description is not None:
            group.description = _optional_text(description, 500)
        if group_type is not None:
            group.group_type = _one_of(group_type, GROUP_TYPES, "group type")
        if visibility is not None:
            group.visibility = _one_of(visibility, VISIBILITIES, "visibility")
        updated = self.groups.update_group(group)
        self._audit(group_id, user_id, "group_updated", {"name": updated.name})
        return updated

    def attach_image(
        self, group_id: uuid.UUID, user_id: uuid.UUID, data: bytes, content_type: Optional[str]
    ) -> ExpenseGroup:
        group = self._require_admin_group(group_id, user_id)
        try:
            group.image_path = save_group_image(group_id, data, content_type)
        except ValueError as exc:
            raise ValidationException(str(exc)) from exc
        return self.groups.update_group(group)

    def invite_member(self, group_id: uuid.UUID, user_id: uuid.UUID, email: str) -> GroupInvitation:
        self._require_admin_group(group_id, user_id)
        clean = email.strip().lower()
        if "@" not in clean or len(clean) < 5:
            raise ValidationException("Enter a valid email address")
        invitee = self.users.get_by_email(clean)
        if invitee and self._is_active_member(group_id, invitee.id):
            raise ConflictException("That person is already in this group")
        pending = self.groups.get_pending_invitation(group_id, clean)
        if pending:
            raise ConflictException("An invitation is already waiting for that email")
        now = datetime.utcnow()
        invitation = GroupInvitation(
            id=uuid.uuid4(),
            group_id=group_id,
            email=clean,
            invited_by=user_id,
            invitee_user_id=invitee.id if invitee else None,
            status="pending",
            expires_at=now + timedelta(days=INVITE_DAYS),
            created_at=now,
        )
        saved = self.groups.create_invitation(invitation)
        self._audit(group_id, user_id, "member_invited", {"email": clean})
        return saved

    def respond_invitation(self, invitation_id: uuid.UUID, user_id: uuid.UUID, accept: bool) -> GroupInvitation:
        self.groups.expire_stale_invitations(datetime.utcnow())
        invitation = self.groups.get_invitation(invitation_id)
        if not invitation:
            raise EntityNotFoundException("Invitation", invitation_id)
        user = self.users.get_by_id(user_id)
        if not user or user.email != invitation.email:
            raise ForbiddenException("This invitation is for a different account")
        if invitation.status != "pending":
            raise ConflictException("This invitation is no longer pending")
        if invitation.expires_at < datetime.utcnow():
            invitation.status = "expired"
            invitation.responded_at = datetime.utcnow()
            return self.groups.update_invitation(invitation)
        invitation.invitee_user_id = user_id
        invitation.responded_at = datetime.utcnow()
        invitation.status = "accepted" if accept else "rejected"
        saved = self.groups.update_invitation(invitation)
        if accept:
            existing = self.groups.get_membership(invitation.group_id, user_id)
            if existing:
                self.groups.reactivate_membership(invitation.group_id, user_id, "member")
            else:
                self.groups.add_membership(invitation.group_id, user_id, "member")
            self._audit(invitation.group_id, user_id, "invite_accepted", {})
        return saved

    def remove_member(self, group_id: uuid.UUID, admin_id: uuid.UUID, member_id: uuid.UUID) -> None:
        self._require_admin_group(group_id, admin_id)
        membership = self.groups.get_membership(group_id, member_id)
        if not membership or membership.status != "active":
            raise EntityNotFoundException("Member", member_id)
        if membership.role == "admin" and self.groups.count_active_admins(group_id) <= 1:
            raise ValidationException("Keep at least one group administrator")
        self.groups.remove_membership(group_id, member_id)
        self._audit(group_id, admin_id, "member_removed", {"user_id": str(member_id)})

    def dashboard(self, user_id: uuid.UUID):
        user = self.users.get_by_id(user_id)
        self.groups.expire_stale_invitations(datetime.utcnow())
        groups = self.groups.list_groups_for_user(user_id)
        expenses = self.groups.list_recent_expenses_for_user(user_id, limit=20)
        updates: List[GroupUpdate] = []
        if user:
            for invite in self.groups.list_pending_invitations_for_email(user.email):
                updates.append(
                    GroupUpdate(
                        kind="invitation",
                        group_id=invite.group_id,
                        title=f"Invite to {invite.group_name or 'a group'}",
                        subtitle="Accept to join this group",
                        amount=None,
                        invitation_id=invite.id,
                        created_at=invite.created_at,
                    )
                )
        for settlement in self.groups.list_recent_settlements_for_user(user_id, limit=10):
            other = settlement.from_name if settlement.to_user_id == user_id else settlement.to_name
            updates.append(
                GroupUpdate(
                    kind="payment_recorded",
                    group_id=settlement.group_id,
                    title=f"{other or 'A member'} recorded a payment",
                    subtitle="Review and settle",
                    amount=settlement.amount,
                    settlement_id=settlement.id,
                    created_at=settlement.created_at,
                )
            )
        for group in groups:
            balances = self.groups.list_balances(group.id)
            mine = next((item for item in balances if item.user_id == user_id), None)
            if mine and mine.net_paise < 0:
                amount = (-mine.net_paise) / 100
                from decimal import Decimal

                updates.append(
                    GroupUpdate(
                        kind="settle_reminder",
                        group_id=group.id,
                        title=f"Settle up in {group.name}",
                        subtitle="Outstanding balance",
                        amount=Decimal(str(amount)).quantize(Decimal("0.01")),
                        created_at=group.updated_at,
                    )
                )
        updates.sort(key=lambda item: item.created_at or datetime.min, reverse=True)
        return groups, expenses, updates[:20]

    def activity(self, group_id: uuid.UUID, user_id: uuid.UUID):
        self._require_member(group_id, user_id)
        return self.groups.list_audit(group_id)

    def _require_member(self, group_id: uuid.UUID, user_id: uuid.UUID):
        group = self.groups.get_group(group_id)
        if not group:
            raise EntityNotFoundException("Group", group_id)
        if not self._is_active_member(group_id, user_id):
            raise ForbiddenException("You are not a member of this group")
        return group

    def _require_member_group(self, group_id: uuid.UUID, user_id: uuid.UUID) -> ExpenseGroup:
        return self._require_member(group_id, user_id)

    def _require_admin_group(self, group_id: uuid.UUID, user_id: uuid.UUID) -> ExpenseGroup:
        group = self._require_member(group_id, user_id)
        membership = self.groups.get_membership(group_id, user_id)
        if membership.role != "admin":
            raise ForbiddenException("Only a group administrator can do that")
        return group

    def _is_active_member(self, group_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        membership = self.groups.get_membership(group_id, user_id)
        return bool(membership and membership.status == "active")

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


def _clean_name(name: str) -> str:
    value = (name or "").strip()
    if len(value) < 2 or len(value) > 60:
        raise ValidationException("Group name must be between 2 and 60 characters")
    return value


def _optional_text(value: Optional[str], limit: int) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    if len(text) > limit:
        raise ValidationException(f"Text must be {limit} characters or fewer")
    return text


def _one_of(value: str, allowed: Tuple[str, ...], label: str) -> str:
    clean = (value or "").strip().lower()
    if clean not in allowed:
        raise ValidationException(f"Choose a valid {label}")
    return clean
