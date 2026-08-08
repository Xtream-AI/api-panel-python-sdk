from datetime import datetime, timezone
from xtream_ai_panel_api.models import (
    Line, Package, Bouquet, Stream, Vod, BillingSnapshot, Reseller,
    Identity, Connection, RateLimitInfo, PaginatedResponse,
)


def test_line_from_dict_populates_all_fields():
    j = {
        "id": 1512227, "username": "GregorioS", "password": "Santos52",
        "member_id": 2432, "exp_date": 1813449600, "max_connections": 4,
        "is_trial": False, "is_restreamer": False,
        "enabled": True, "admin_enabled": True,
        "bouquets": [2, 4, 14, 15], "created_at": 1574874852,
    }
    line = Line.from_dict(j)
    assert line.id == 1512227
    assert line.member_id == 2432
    assert isinstance(line.exp_date, datetime)
    assert line.exp_date.timestamp() == 1813449600
    assert line.exp_date.tzinfo is timezone.utc
    assert line.bouquets == [2, 4, 14, 15]
    assert line.enabled is True


def test_line_accepts_null_exp_date():
    j = {
        "id": 1, "username": "x", "password": "y", "member_id": 1,
        "exp_date": None, "max_connections": 1,
        "is_trial": False, "is_restreamer": False,
        "enabled": True, "admin_enabled": True,
        "bouquets": [], "created_at": None,
    }
    line = Line.from_dict(j)
    assert line.exp_date is None
    assert line.created_at is None


def test_paginated_from_dict_maps_items():
    def factory(d):
        return Bouquet.from_dict(d)
    p = PaginatedResponse.from_dict(
        {"items": [{"id": 1, "name": "A", "order": 0}], "next_cursor": "z"},
        factory,
    )
    assert p.items[0].id == 1
    assert p.next_cursor == "z"


def test_rate_limit_info_from_headers():
    r = RateLimitInfo.from_headers({
        "x-ratelimit-limit": "300",
        "x-ratelimit-remaining": "42",
        "x-ratelimit-reset": "1786126673",
    })
    assert r.limit == 300
    assert r.remaining == 42
    assert isinstance(r.reset_at, datetime)


def test_rate_limit_info_returns_none_when_headers_missing():
    assert RateLimitInfo.from_headers({}) is None


def test_billing_snapshot_from_none():
    assert BillingSnapshot.from_dict(None) is None
