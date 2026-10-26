from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import uuid


GROUP_TYPES = ("family", "friends", "trip", "roommates", "other")
VISIBILITIES = ("private", "discoverable")
MEMBER_ROLES = ("admin", "member")
MEMBER_STATUSES = ("active", "removed")
INVITE_STATUSES = ("pending", "accepted", "rejected", "expired")
SPLIT_METHODS = ("equal", "percent", "exact", "shares")
SETTLEMENT_METHODS = ("cash", "upi", "bank_transfer", "card", "other")
PAYMENT_MODES = ("cash", "online")
ONLINE_TYPES = ("upi", "neft", "card", "net_banking", "other")


@dataclass
class GroupMember:
    user_id: uuid.UUID
    role: str
    status: str
    email: str
    display_name: Optional[str]
    has_avatar: bool
    joined_at: datetime


@dataclass
class ExpenseGroup:
    id: uuid.UUID
    name: str
    description: Optional[str]
    group_type: str
    visibility: str
    image_path: Optional[str]
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    members: List[GroupMember] = field(default_factory=list)
    total_expenses: Decimal = Decimal("0.00")
    member_count: int = 0

    @classmethod
    def create(
        cls,
        name: str,
        created_by: uuid.UUID,
        description: Optional[str] = None,
        group_type: str = "other",
        visibility: str = "private",
    ) -> "ExpenseGroup":
        now = datetime.utcnow()
        return cls(
            id=uuid.uuid4(),
            name=name,
            description=description,
            group_type=group_type,
            visibility=visibility,
            image_path=None,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )


@dataclass
class GroupInvitation:
    id: uuid.UUID
    group_id: uuid.UUID
    email: str
    invited_by: uuid.UUID
    invitee_user_id: Optional[uuid.UUID]
    status: str
    expires_at: datetime
    created_at: datetime
    responded_at: Optional[datetime] = None
    group_name: Optional[str] = None


@dataclass
class ExpenseShare:
    user_id: uuid.UUID
    amount: Decimal
    percent: Optional[Decimal] = None
    shares: Optional[int] = None


@dataclass
class GroupExpense:
    id: uuid.UUID
    group_id: uuid.UUID
    paid_by: uuid.UUID
    created_by: uuid.UUID
    category_id: uuid.UUID
    amount: Decimal
    description: Optional[str]
    expense_date: date
    payment_mode: str
    online_payment_type: Optional[str]
    split_method: str
    client_request_id: Optional[str]
    receipt_path: Optional[str]
    created_at: datetime
    updated_at: datetime
    shares: List[ExpenseShare] = field(default_factory=list)
    payer_name: Optional[str] = None
    category_name_key: Optional[str] = None
    category_icon_key: Optional[str] = None
    group_name: Optional[str] = None


@dataclass
class ExpenseSettlement:
    id: uuid.UUID
    group_id: uuid.UUID
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    amount: Decimal
    method: str
    recording_kind: str
    client_request_id: Optional[str]
    created_by: uuid.UUID
    note: Optional[str]
    created_at: datetime
    from_name: Optional[str] = None
    to_name: Optional[str] = None


@dataclass
class MemberBalance:
    user_id: uuid.UUID
    display_name: Optional[str]
    email: str
    net_paise: int
    has_avatar: bool = False


@dataclass
class GroupAuditEvent:
    id: uuid.UUID
    group_id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    payload: dict
    created_at: datetime
    actor_name: Optional[str] = None


@dataclass
class GroupUpdate:
    kind: str
    group_id: Optional[uuid.UUID]
    title: str
    subtitle: str
    amount: Optional[Decimal]
    invitation_id: Optional[uuid.UUID] = None
    settlement_id: Optional[uuid.UUID] = None
    created_at: Optional[datetime] = None
