from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP
from typing import Dict, Mapping, Sequence
import uuid


def rupees_to_paise(amount: Decimal) -> int:
    quantized = Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return int((quantized * 100).to_integral_value(rounding=ROUND_HALF_UP))


def paise_to_rupees(paise: int) -> Decimal:
    return (Decimal(paise) / Decimal(100)).quantize(Decimal("0.01"))


def _sorted_ids(ids: Sequence[uuid.UUID]) -> list[uuid.UUID]:
    return sorted(ids, key=lambda value: str(value))


def equal_split(total_paise: int, participant_ids: Sequence[uuid.UUID]) -> Dict[uuid.UUID, int]:
    ids = _sorted_ids(participant_ids)
    if not ids:
        raise ValueError("Select at least one participant")
    if total_paise <= 0:
        raise ValueError("Amount must be greater than zero")
    base, remainder = divmod(total_paise, len(ids))
    return {uid: base + (1 if index < remainder else 0) for index, uid in enumerate(ids)}


def percent_split(
    total_paise: int, percents: Mapping[uuid.UUID, Decimal]
) -> Dict[uuid.UUID, int]:
    if not percents:
        raise ValueError("Select at least one participant")
    if total_paise <= 0:
        raise ValueError("Amount must be greater than zero")
    total_percent = sum((Decimal(str(value)) for value in percents.values()), Decimal("0"))
    if total_percent != Decimal("100"):
        raise ValueError("Percentages must total 100%")
    raw = {
        uid: (Decimal(total_paise) * Decimal(str(pct)) / Decimal("100"))
        for uid, pct in percents.items()
    }
    return _allocate_remainder(total_paise, raw)


def exact_split(total_paise: int, amounts: Mapping[uuid.UUID, int]) -> Dict[uuid.UUID, int]:
    if not amounts:
        raise ValueError("Select at least one participant")
    if total_paise <= 0:
        raise ValueError("Amount must be greater than zero")
    if any(value < 0 for value in amounts.values()):
        raise ValueError("Share amounts cannot be negative")
    if sum(amounts.values()) != total_paise:
        raise ValueError("Exact shares must equal the expense total")
    return dict(amounts)


def shares_split(total_paise: int, shares: Mapping[uuid.UUID, int]) -> Dict[uuid.UUID, int]:
    if not shares:
        raise ValueError("Select at least one participant")
    if total_paise <= 0:
        raise ValueError("Amount must be greater than zero")
    if any(value <= 0 for value in shares.values()):
        raise ValueError("Each participant must have at least one share")
    total_shares = sum(shares.values())
    raw = {
        uid: Decimal(total_paise) * Decimal(value) / Decimal(total_shares)
        for uid, value in shares.items()
    }
    return _allocate_remainder(total_paise, raw)


def _allocate_remainder(total_paise: int, raw: Mapping[uuid.UUID, Decimal]) -> Dict[uuid.UUID, int]:
    floors = {
        uid: int(value.quantize(Decimal("1"), rounding=ROUND_DOWN)) for uid, value in raw.items()
    }
    leftover = {uid: raw[uid] - Decimal(floors[uid]) for uid in raw}
    remaining = total_paise - sum(floors.values())
    order = sorted(raw.keys(), key=lambda uid: (-leftover[uid], str(uid)))
    for index in range(remaining):
        floors[order[index]] += 1
    return floors
