from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, field_serializer, field_validator


def _money(value: Decimal) -> str:
    return str(Decimal(str(value)).quantize(Decimal("0.01")))


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    group_type: str = "other"
    visibility: str = "private"
    member_emails: List[str] = Field(default_factory=list)


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=60)
    description: Optional[str] = Field(None, max_length=500)
    group_type: Optional[str] = None
    visibility: Optional[str] = None


class InviteRequest(BaseModel):
    email: str


class ShareInput(BaseModel):
    user_id: uuid.UUID
    percent: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    shares: Optional[int] = None


class GroupExpenseCreateRequest(BaseModel):
    category_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    expense_date: date
    paid_by: uuid.UUID
    participant_ids: List[uuid.UUID]
    split_method: str = "equal"
    description: Optional[str] = Field(None, max_length=500)
    payment_mode: str = "cash"
    online_payment_type: Optional[str] = None
    shares: List[ShareInput] = Field(default_factory=list)
    client_request_id: Optional[str] = Field(None, max_length=64)

    @field_validator("client_request_id", "online_payment_type", "description", mode="before")
    @classmethod
    def _blank(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value


class SettlementCreateRequest(BaseModel):
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    method: str
    note: Optional[str] = Field(None, max_length=500)
    client_request_id: Optional[str] = Field(None, max_length=64)


class MemberResponse(BaseModel):
    user_id: uuid.UUID
    role: str
    status: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    has_avatar: bool = False
    avatar_url: Optional[str] = None


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: Optional[str]
    group_type: str
    visibility: str
    image_url: Optional[str] = None
    created_by: uuid.UUID
    total_expenses: str
    member_count: int
    members: List[MemberResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at", when_used="json")
    def _utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")


class DiscoverableGroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    group_type: str
    member_count: int
    image_url: Optional[str] = None


class InvitationResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    email: str
    status: str
    group_name: Optional[str] = None
    expires_at: datetime


class ShareResponse(BaseModel):
    user_id: uuid.UUID
    amount: str
    percent: Optional[str] = None
    shares: Optional[int] = None


class GroupExpenseResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    group_name: Optional[str] = None
    paid_by: uuid.UUID
    payer_name: Optional[str] = None
    created_by: uuid.UUID
    category_id: uuid.UUID
    category_name_key: Optional[str] = None
    category_icon_key: Optional[str] = None
    amount: str
    description: Optional[str]
    expense_date: date
    payment_mode: str
    online_payment_type: Optional[str] = None
    split_method: str
    receipt_url: Optional[str] = None
    shares: List[ShareResponse] = Field(default_factory=list)
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def _utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")


class BalanceResponse(BaseModel):
    user_id: uuid.UUID
    display_name: Optional[str]
    email: str
    net_amount: str
    has_avatar: bool = False


class SettlementResponse(BaseModel):
    id: uuid.UUID
    group_id: uuid.UUID
    from_user_id: uuid.UUID
    to_user_id: uuid.UUID
    from_name: Optional[str] = None
    to_name: Optional[str] = None
    amount: str
    method: str
    recording_kind: str
    note: Optional[str] = None
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def _utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")


class AuditResponse(BaseModel):
    id: uuid.UUID
    action: str
    payload: dict
    created_at: datetime

    @field_serializer("created_at", when_used="json")
    def _utc(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat().replace("+00:00", "Z")


class UpdateResponse(BaseModel):
    kind: str
    group_id: Optional[uuid.UUID] = None
    title: str
    subtitle: str
    amount: Optional[str] = None
    invitation_id: Optional[uuid.UUID] = None
    settlement_id: Optional[uuid.UUID] = None


class GroupDashboardResponse(BaseModel):
    groups: List[GroupResponse]
    recent_expenses: List[GroupExpenseResponse]
    updates: List[UpdateResponse]


def money(value: Decimal) -> str:
    return _money(value)
