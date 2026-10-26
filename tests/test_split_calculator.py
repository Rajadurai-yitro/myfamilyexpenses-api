from decimal import Decimal
import uuid

from app.domain.services.split_calculator import (
    equal_split,
    exact_split,
    percent_split,
    rupees_to_paise,
    shares_split,
)


def test_equal_split_remainder_goes_to_sorted_ids():
    a, b, c = uuid.UUID("00000000-0000-0000-0000-00000000000a"), uuid.UUID(
        "00000000-0000-0000-0000-00000000000b"
    ), uuid.UUID("00000000-0000-0000-0000-00000000000c")
    result = equal_split(1001, [c, a, b])
    assert sum(result.values()) == 1001
    assert result[a] == 334
    assert result[b] == 334
    assert result[c] == 333


def test_percent_must_total_100():
    a, b = uuid.uuid4(), uuid.uuid4()
    try:
        percent_split(1000, {a: Decimal("60"), b: Decimal("30")})
        assert False
    except ValueError as exc:
        assert "100%" in str(exc)


def test_percent_remainder():
    a = uuid.UUID("00000000-0000-0000-0000-00000000000a")
    b = uuid.UUID("00000000-0000-0000-0000-00000000000b")
    result = percent_split(1000, {a: Decimal("33.33"), b: Decimal("66.67")})
    assert sum(result.values()) == 1000


def test_exact_must_match_total():
    a, b = uuid.uuid4(), uuid.uuid4()
    try:
        exact_split(1200, {a: 300, b: 300})
        assert False
    except ValueError:
        pass
    assert exact_split(1200, {a: 900, b: 300}) == {a: 900, b: 300}


def test_shares_split():
    a = uuid.UUID("00000000-0000-0000-0000-00000000000a")
    b = uuid.UUID("00000000-0000-0000-0000-00000000000b")
    result = shares_split(1000, {a: 1, b: 3})
    assert result[a] == 250
    assert result[b] == 750


def test_rupees_to_paise_rounds_half_up():
    assert rupees_to_paise(Decimal("10.005")) == 1001
    assert rupees_to_paise(Decimal("10.004")) == 1000
