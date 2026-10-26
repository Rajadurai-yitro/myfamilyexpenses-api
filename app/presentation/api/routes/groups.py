from decimal import Decimal
from typing import List, Optional
import uuid
from fastapi import APIRouter, Depends, File, Header, UploadFile, status
from fastapi.responses import FileResponse

from app.application.groups.group_expense_usecases import GroupExpenseUseCases
from app.application.groups.group_usecases import GroupUseCases
from app.core.dependencies import (
    get_category_repository,
    get_current_user,
    get_group_repository,
    get_user_repository,
)
from app.core.exceptions import EntityNotFoundException
from app.domain.entities.group import (
    ExpenseGroup,
    ExpenseSettlement,
    GroupExpense,
    GroupInvitation,
    GroupUpdate,
    MemberBalance,
)
from app.domain.entities.user import User
from app.domain.services.split_calculator import paise_to_rupees
from app.infrastructure.storage.group_attachment_storage import group_file
from app.presentation.api.schemas.common_schemas import MessageResponse
from app.infrastructure.database.repositories.sqlalchemy_category_repo import (
    SqlAlchemyCategoryRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_group_repo import (
    SqlAlchemyGroupRepository,
)
from app.infrastructure.database.repositories.sqlalchemy_user_repo import (
    SqlAlchemyUserRepository,
)
from app.presentation.api.schemas.group_schemas import (
    AuditResponse,
    BalanceResponse,
    DiscoverableGroupResponse,
    GroupCreateRequest,
    GroupDashboardResponse,
    GroupExpenseCreateRequest,
    GroupExpenseResponse,
    GroupResponse,
    GroupUpdateRequest,
    InvitationResponse,
    InviteRequest,
    MemberResponse,
    SettlementCreateRequest,
    SettlementResponse,
    ShareResponse,
    UpdateResponse,
    money,
)

router = APIRouter(prefix="/api/v1/groups", tags=["Groups"])


def _group_usecases(
    groups: SqlAlchemyGroupRepository = Depends(get_group_repository),
    users: SqlAlchemyUserRepository = Depends(get_user_repository),
) -> GroupUseCases:
    return GroupUseCases(groups, users)


def _expense_usecases(
    groups: SqlAlchemyGroupRepository = Depends(get_group_repository),
    categories: SqlAlchemyCategoryRepository = Depends(get_category_repository),
) -> GroupExpenseUseCases:
    return GroupExpenseUseCases(groups, categories)


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
def create_group(
    req: GroupCreateRequest,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    group = usecases.create_group(
        user_id=current_user.id,
        name=req.name,
        description=req.description,
        group_type=req.group_type,
        visibility=req.visibility,
        member_emails=req.member_emails,
    )
    return _group_response(group)


@router.get("", response_model=List[GroupResponse])
def list_groups(
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return [_group_response(item) for item in usecases.list_my_groups(current_user.id)]


@router.get("/dashboard", response_model=GroupDashboardResponse)
def dashboard(
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    groups, expenses, updates = usecases.dashboard(current_user.id)
    return GroupDashboardResponse(
        groups=[_group_response(item) for item in groups],
        recent_expenses=[_expense_response(item) for item in expenses],
        updates=[_update_response(item) for item in updates],
    )


@router.get("/discoverable", response_model=List[DiscoverableGroupResponse])
def discoverable(
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return [
        DiscoverableGroupResponse(
            id=item.id,
            name=item.name,
            group_type=item.group_type,
            member_count=item.member_count,
            image_url=_group_image_url(item),
        )
        for item in usecases.list_discoverable(current_user.id)
    ]


@router.post("/invitations/{invitation_id}/accept", response_model=InvitationResponse)
def accept_invite(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return _invite_response(usecases.respond_invitation(invitation_id, current_user.id, True))


@router.post("/invitations/{invitation_id}/reject", response_model=InvitationResponse)
def reject_invite(
    invitation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return _invite_response(usecases.respond_invitation(invitation_id, current_user.id, False))


@router.get("/{group_id}", response_model=GroupResponse)
def get_group(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return _group_response(usecases.get_group(group_id, current_user.id))


@router.patch("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: uuid.UUID,
    req: GroupUpdateRequest,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return _group_response(
        usecases.update_group(
            group_id,
            current_user.id,
            name=req.name,
            description=req.description,
            group_type=req.group_type,
            visibility=req.visibility,
        )
    )


@router.post("/{group_id}/image", response_model=GroupResponse)
def upload_group_image(
    group_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return _group_response(
        usecases.attach_image(group_id, current_user.id, file.file.read(), file.content_type)
    )


@router.get("/{group_id}/image")
def download_group_image(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    group = usecases.public_cover(group_id, current_user.id)
    path = group_file(group.image_path)
    if path is None:
        raise EntityNotFoundException("GroupImage", group_id)
    return FileResponse(path)


@router.post("/{group_id}/invitations", response_model=InvitationResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    group_id: uuid.UUID,
    req: InviteRequest,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return _invite_response(usecases.invite_member(group_id, current_user.id, req.email))


@router.delete("/{group_id}/members/{member_id}", response_model=MessageResponse)
def remove_member(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    usecases.remove_member(group_id, current_user.id, member_id)
    return MessageResponse(message="Member removed")


@router.get("/{group_id}/activity", response_model=List[AuditResponse])
def activity(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupUseCases = Depends(_group_usecases),
):
    return [
        AuditResponse(id=item.id, action=item.action, payload=item.payload, created_at=item.created_at)
        for item in usecases.activity(group_id, current_user.id)
    ]


@router.get("/{group_id}/expenses", response_model=List[GroupExpenseResponse])
def list_expenses(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    return [_expense_response(item) for item in usecases.list_expenses(group_id, current_user.id)]


@router.post("/{group_id}/expenses", response_model=GroupExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    group_id: uuid.UUID,
    req: GroupExpenseCreateRequest,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    percents = {item.user_id: item.percent for item in req.shares if item.percent is not None}
    exact = {item.user_id: item.amount for item in req.shares if item.amount is not None}
    share_counts = {item.user_id: item.shares for item in req.shares if item.shares is not None}
    expense = usecases.create_expense(
        group_id=group_id,
        user_id=current_user.id,
        category_id=req.category_id,
        amount=req.amount,
        expense_date=req.expense_date,
        paid_by=req.paid_by,
        participant_ids=req.participant_ids,
        split_method=req.split_method,
        description=req.description,
        payment_mode=req.payment_mode,
        online_payment_type=req.online_payment_type,
        percents=percents or None,
        exact_amounts=exact or None,
        shares=share_counts or None,
        client_request_id=req.client_request_id or idempotency_key,
    )
    return _expense_response(expense)


@router.get("/{group_id}/expenses/{expense_id}", response_model=GroupExpenseResponse)
def get_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    return _expense_response(usecases.get_expense(group_id, expense_id, current_user.id))


@router.delete("/{group_id}/expenses/{expense_id}", response_model=MessageResponse)
def delete_expense(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    usecases.delete_expense(group_id, expense_id, current_user.id)
    return MessageResponse(message="Expense deleted")


@router.post("/{group_id}/expenses/{expense_id}/receipt", response_model=GroupExpenseResponse)
def upload_receipt(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    return _expense_response(
        usecases.attach_receipt(
            group_id, expense_id, current_user.id, file.file.read(), file.content_type
        )
    )


@router.get("/{group_id}/expenses/{expense_id}/receipt")
def download_receipt(
    group_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    expense = usecases.get_expense(group_id, expense_id, current_user.id)
    path = group_file(expense.receipt_path)
    if path is None:
        raise EntityNotFoundException("Receipt", expense_id)
    return FileResponse(path)


@router.get("/{group_id}/balances", response_model=List[BalanceResponse])
def balances(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    return [_balance_response(item) for item in usecases.list_balances(group_id, current_user.id)]


@router.get("/{group_id}/settlements", response_model=List[SettlementResponse])
def list_settlements(
    group_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
):
    return [_settlement_response(item) for item in usecases.list_settlements(group_id, current_user.id)]


@router.post(
    "/{group_id}/settlements",
    response_model=SettlementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_settlement(
    group_id: uuid.UUID,
    req: SettlementCreateRequest,
    current_user: User = Depends(get_current_user),
    usecases: GroupExpenseUseCases = Depends(_expense_usecases),
    idempotency_key: Optional[str] = Header(default=None, alias="Idempotency-Key"),
):
    return _settlement_response(
        usecases.create_settlement(
            group_id=group_id,
            user_id=current_user.id,
            from_user_id=req.from_user_id,
            to_user_id=req.to_user_id,
            amount=req.amount,
            method=req.method,
            note=req.note,
            client_request_id=req.client_request_id or idempotency_key,
        )
    )


def _group_image_url(group: ExpenseGroup) -> Optional[str]:
    if not group.image_path:
        return None
    return f"/api/v1/groups/{group.id}/image"


def _group_response(group: ExpenseGroup) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        group_type=group.group_type,
        visibility=group.visibility,
        image_url=_group_image_url(group),
        created_by=group.created_by,
        total_expenses=money(group.total_expenses),
        member_count=group.member_count,
        members=[
            MemberResponse(
                user_id=item.user_id,
                role=item.role,
                status=item.status,
                email=item.email,
                display_name=item.display_name,
                has_avatar=item.has_avatar,
                avatar_url=f"/api/v1/users/{item.user_id}/avatar" if item.has_avatar else None,
            )
            for item in group.members
        ],
        created_at=group.created_at,
        updated_at=group.updated_at,
    )


def _invite_response(item: GroupInvitation) -> InvitationResponse:
    return InvitationResponse(
        id=item.id,
        group_id=item.group_id,
        email=item.email,
        status=item.status,
        group_name=item.group_name,
        expires_at=item.expires_at,
    )


def _expense_response(item: GroupExpense) -> GroupExpenseResponse:
    return GroupExpenseResponse(
        id=item.id,
        group_id=item.group_id,
        group_name=item.group_name,
        paid_by=item.paid_by,
        payer_name=item.payer_name,
        created_by=item.created_by,
        category_id=item.category_id,
        category_name_key=item.category_name_key,
        category_icon_key=item.category_icon_key,
        amount=money(item.amount),
        description=item.description,
        expense_date=item.expense_date,
        payment_mode=item.payment_mode,
        online_payment_type=item.online_payment_type,
        split_method=item.split_method,
        receipt_url=(
            f"/api/v1/groups/{item.group_id}/expenses/{item.id}/receipt"
            if item.receipt_path
            else None
        ),
        shares=[
            ShareResponse(
                user_id=share.user_id,
                amount=money(share.amount),
                percent=str(share.percent) if share.percent is not None else None,
                shares=share.shares,
            )
            for share in item.shares
        ],
        created_at=item.created_at,
    )


def _balance_response(item: MemberBalance) -> BalanceResponse:
    return BalanceResponse(
        user_id=item.user_id,
        display_name=item.display_name,
        email=item.email,
        net_amount=money(paise_to_rupees(item.net_paise)),
        has_avatar=item.has_avatar,
    )


def _settlement_response(item: ExpenseSettlement) -> SettlementResponse:
    return SettlementResponse(
        id=item.id,
        group_id=item.group_id,
        from_user_id=item.from_user_id,
        to_user_id=item.to_user_id,
        from_name=item.from_name,
        to_name=item.to_name,
        amount=money(item.amount),
        method=item.method,
        recording_kind=item.recording_kind,
        note=item.note,
        created_at=item.created_at,
    )


def _update_response(item: GroupUpdate) -> UpdateResponse:
    return UpdateResponse(
        kind=item.kind,
        group_id=item.group_id,
        title=item.title,
        subtitle=item.subtitle,
        amount=money(item.amount) if item.amount is not None else None,
        invitation_id=item.invitation_id,
        settlement_id=item.settlement_id,
    )
