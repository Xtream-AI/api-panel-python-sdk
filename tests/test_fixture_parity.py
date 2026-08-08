
import json
from pathlib import Path
import pytest

from xtream_ai_panel_api.models import (
    Line, Package, Bouquet, Category, Stream, Vod,
    Reseller, BillingSnapshot, Identity, Connection, PaginatedResponse,
)

FIX = Path(__file__).parent / "fixtures"


def load(rel: str) -> dict:
    return json.loads((FIX / rel).read_text())


def test_health_shape_is_flat():
    h = load("health/health-200.json")
    assert h["status"] == "ok"
    assert "version" in h


def test_me_admin_parses():
    me = Identity.from_dict(load("me/me-admin-200.json"))
    assert me.type == "admin"
    assert me.scopes


def test_line_list_parses():
    page = PaginatedResponse.from_dict(
        load("lines/list-200.json"), Line.from_dict)
    assert page.items
    assert isinstance(page.items[0], Line)


def test_line_get_parses():
    line = Line.from_dict(load("lines/get-200.json"))
    assert line.id > 0


def test_reset_password_shape():


    raw = load("lines/reset-password-200.json")
    assert "id" in raw and "password" in raw


def test_connections_parse():
    raw = load("lines/connections-200.json")
    if not raw.get("items"):
        pytest.skip("no connections in fixture")
    for c in raw["items"]:
        conn = Connection.from_dict(c)
        assert conn.connection_id > 0
        assert conn.content_type in ("live", "movie")


def test_packages_parse_with_float_credits():
    for p in load("catalog/packages-200.json")["items"]:
        pkg = Package.from_dict(p)
        assert pkg.id > 0
        assert isinstance(pkg.official_credits, float)


def test_bouquets_parse():
    for b in load("catalog/bouquets-200.json")["items"]:
        Bouquet.from_dict(b)


def test_streams_parse_with_category_objects():
    for s in load("catalog/streams-200.json")["items"]:
        stream = Stream.from_dict(s)
        for cat in stream.categories:
            assert isinstance(cat, Category)
            assert cat.id > 0


def test_vod_list_parses():
    for v in load("catalog/vods-200.json")["items"]:
        Vod.from_dict(v)


def test_reseller_list_shape_is_flat_billing():
    for r in load("resellers/list-200.json")["items"]:
        reseller = Reseller.from_dict(r)


        assert reseller.owner_id is None
        assert reseller.billing is not None
        assert reseller.billing.mode in ("credits", "users")


def test_reseller_get_has_nested_billing():
    p = FIX / "resellers/get-200.json"
    if not p.is_file():
        pytest.skip("get-200 fixture not captured")
    reseller = Reseller.from_dict(json.loads(p.read_text()))
    assert reseller.billing is not None


def test_reseller_billing_parses():
    p = FIX / "resellers/billing-200.json"
    if not p.is_file():
        pytest.skip("billing-200 fixture not captured")
    b = BillingSnapshot.from_dict(json.loads(p.read_text()))
    assert b.mode in ("credits", "users")


def test_vod_with_categories_parses_category_objects():
    vod = Vod.from_dict(load("catalog/vod-with-categories-200.json"))
    assert vod.categories
    for cat in vod.categories:
        assert isinstance(cat, Category)
        assert cat.id > 0
        assert cat.name != ""
