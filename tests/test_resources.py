import json
import urllib.parse
import pytest
import responses as rsps

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.resources.lines import LinesResource
from xtream_ai_panel_api.resources.catalog import CatalogResource
from xtream_ai_panel_api.resources.resellers import ResellersResource
from xtream_ai_panel_api.resources.me import MeResource
from xtream_ai_panel_api.models import (
    Line, Connection, Package, Bouquet, Stream, Vod,
    Reseller, BillingSnapshot, Identity, PaginatedResponse,
)


BASE = "https://p.example.com"

@pytest.fixture
def transport():
    return HttpTransport(base_url=BASE, token="pk.x", sleeper=lambda s: None)


LINE_JSON = {
    "id": 100, "username": "u", "password": "p", "member_id": 42,
    "exp_date": 1900000000, "max_connections": 1,
    "is_trial": False, "is_restreamer": False,
    "enabled": True, "admin_enabled": True,
    "bouquets": [1, 2], "created_at": 1700000000,
}


@rsps.activate
def test_lines_create(transport):
    rsps.add(rsps.POST, f"{BASE}/panel-api/v1/lines",
             json=LINE_JSON, status=201)
    line = LinesResource(transport).create(package_id=42, member_id=2432,
                                            username="john")
    assert isinstance(line, Line)
    assert line.id == 100

@rsps.activate
def test_lines_create_sends_email(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (201, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines",
                      callback=cb, content_type="application/json")
    LinesResource(transport).create(package_id=1, member_id=1, email="a@b.com")
    assert seen["body"]["email"] == "a@b.com"

@rsps.activate
def test_lines_list_pagination(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/lines",
             json={"items": [LINE_JSON], "next_cursor": "abc"}, status=200)
    page = LinesResource(transport).list(limit=50)
    assert isinstance(page, PaginatedResponse)
    assert page.next_cursor == "abc"
    assert isinstance(page.items[0], Line)

@rsps.activate
def test_lines_get(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/lines/100",
             json=LINE_JSON, status=200)
    assert LinesResource(transport).get(100).id == 100

@rsps.activate
def test_lines_enable(transport):
    rsps.add(rsps.POST, f"{BASE}/panel-api/v1/lines/100/enable",
             json=LINE_JSON, status=200)
    LinesResource(transport).enable(100)

@rsps.activate
def test_lines_disable(transport):
    rsps.add(rsps.POST, f"{BASE}/panel-api/v1/lines/100/disable",
             json=LINE_JSON, status=200)
    LinesResource(transport).disable(100)

@rsps.activate
def test_lines_renew_with_package(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/renew",
                      callback=cb, content_type="application/json")
    LinesResource(transport).renew(100, package_id=7)
    assert seen["body"]["package_id"] == 7

@rsps.activate
def test_lines_reset_password(transport):
    rsps.add(rsps.POST, f"{BASE}/panel-api/v1/lines/100/reset-password",
             json={"id": 100, "password": "new_secret"}, status=200)
    assert LinesResource(transport).reset_password(100) == "new_secret"


@rsps.activate
def test_lines_delete(transport):
    rsps.add(rsps.POST, f"{BASE}/panel-api/v1/lines/100/delete",
             json={"deleted": True}, status=200)

    assert LinesResource(transport).delete(100) is True


@rsps.activate
def test_lines_delete_returns_false_on_missing_field(transport):
    rsps.add(rsps.POST, f"{BASE}/panel-api/v1/lines/100/delete",
             json={}, status=200)
    assert LinesResource(transport).delete(100) is False

@rsps.activate
def test_lines_connections(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/lines/100/connections",
             json={"items": [{"connection_id": 1, "content_type": "live",
                              "content_id": None, "content_name": "",
                              "started_at": 1900000000, "elapsed_sec": 0,
                              "client_ip": "203.0.113.4", "client_country": "US"}]}, status=200)
    conns = LinesResource(transport).connections(100)
    assert len(conns) == 1
    assert isinstance(conns[0], Connection)
    assert conns[0].client_ip == "203.0.113.4"

@rsps.activate
def test_lines_update_only_provided_fields(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, password="new")
    assert seen["body"] == {"password": "new"}


@rsps.activate
def test_lines_reset_password_with_chosen_password(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps({"id": 100, "password": "Chosen123!"}))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/reset-password",
                      callback=cb, content_type="application/json")
    pw = LinesResource(transport).reset_password(100, password="Chosen123!")
    assert seen["body"]["password"] == "Chosen123!"
    assert pw == "Chosen123!"


@rsps.activate
def test_lines_reset_password_without_password_no_key(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps({"id": 100, "password": "random00"}))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/reset-password",
                      callback=cb, content_type="application/json")
    pw = LinesResource(transport).reset_password(100)
    assert "password" not in seen["body"]
    assert pw == "random00"


@rsps.activate
def test_lines_create_admin_only_fields(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (201, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines",
                      callback=cb, content_type="application/json")
    LinesResource(transport).create(
        package_id=1, member_id=1,
        exp_date=1900000000,
        allowed_ips=["203.0.113.9", "198.51.100.7"],
        allowed_ua=["VLC/3.0", "Kodi"],
        is_isplock=True,
    )
    assert seen["body"]["exp_date"] == 1900000000
    assert seen["body"]["allowed_ips"] == ["203.0.113.9", "198.51.100.7"]
    assert seen["body"]["allowed_ua"] == ["VLC/3.0", "Kodi"]
    assert seen["body"]["is_isplock"] is True


@rsps.activate
def test_lines_update_exp_date_int(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, exp_date=1900000000)
    assert seen["body"] == {"exp_date": 1900000000}


@rsps.activate
def test_lines_update_exp_date_perpetual_null(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, exp_date=None)
    assert "exp_date" in seen["body"]
    assert seen["body"]["exp_date"] is None


@rsps.activate
def test_lines_update_exp_date_omitted_no_key(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, max_connections=4)
    assert "exp_date" not in seen["body"]
    assert seen["body"] == {"max_connections": 4}


@rsps.activate
def test_lines_update_new_fields(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(
        100, admin_enabled=False,
        allowed_ips=["203.0.113.9"], allowed_ua=["VLC/3.0"])
    assert seen["body"]["admin_enabled"] is False
    assert seen["body"]["allowed_ips"] == ["203.0.113.9"]
    assert seen["body"]["allowed_ua"] == ["VLC/3.0"]
    assert "exp_date" not in seen["body"]


@rsps.activate
def test_lines_update_bouquets_and_notes(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, bouquets=[4, "9"],
                                    notes="renewed by billing")
    assert seen["body"]["bouquets"] == [4, 9]
    assert seen["body"]["notes"] == "renewed by billing"


@rsps.activate
def test_lines_update_empty_notes_clears_them(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, notes="")
    assert seen["body"] == {"notes": ""}


@rsps.activate
def test_lines_update_omits_bouquets_and_notes_when_none(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, password="new")
    assert "bouquets" not in seen["body"]
    assert "notes" not in seen["body"]
    assert seen["body"] == {"password": "new"}


@rsps.activate
def test_lines_renew_with_bouquets(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/renew",
                      callback=cb, content_type="application/json")
    LinesResource(transport).renew(100, package_id=7, bouquets=[1, 2])
    assert seen["body"]["package_id"] == 7
    assert seen["body"]["bouquets"] == [1, 2]


@rsps.activate
def test_lines_renew_omits_bouquets_when_none(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/renew",
                      callback=cb, content_type="application/json")
    LinesResource(transport).renew(100, package_id=7)
    assert seen["body"] == {"package_id": 7}


@rsps.activate
def test_lines_update_keeps_idempotency_key_after_new_params(transport):
    seen = {}
    def cb(request):
        seen["key"] = request.headers.get("Idempotency-Key")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, notes="n", idempotency_key="inv-77")
    assert seen["key"] == "inv-77"


@rsps.activate
def test_lines_positional_idempotency_key_still_binds(transport):
    seen = {}
    def cb(request):
        seen["key"] = request.headers.get("Idempotency-Key")
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(LINE_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/renew",
                      callback=cb, content_type="application/json")
    LinesResource(transport).renew(100, 7, "idem-positional")
    assert seen["key"] == "idem-positional"
    assert seen["body"] == {"package_id": 7}

    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/lines/100/update",
                      callback=cb, content_type="application/json")
    LinesResource(transport).update(100, "pw", True, False, 2, 1700000000,
                                    True, ["1.2.3.4"], ["ua"], "idem-positional-2")
    assert seen["key"] == "idem-positional-2"
    assert "bouquets" not in seen["body"]
    assert "notes" not in seen["body"]


def test_lines_bouquets_and_notes_are_keyword_only():
    import inspect
    for name in ("update", "renew"):
        sig = inspect.signature(getattr(LinesResource, name))
        for param in ("bouquets", "notes"):
            if param in sig.parameters:
                assert sig.parameters[param].kind is inspect.Parameter.KEYWORD_ONLY, \
                    f"{name}({param}=...) must stay keyword-only"


@rsps.activate
def test_catalog_packages(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/packages", json={"items": [{
        "id": 66, "package_name": "Basic",
        "is_trial": False, "is_official": True,
        "official_credits": 1, "official_duration": 1,
        "official_duration_in": "months",
        "trial_credits": 0, "trial_duration": 0, "trial_duration_in": "hours",
        "max_connections": 1, "is_restreamer": False, "forced_country": "",
    }]}, status=200)
    p = CatalogResource(transport).packages()
    assert isinstance(p[0], Package)

@rsps.activate
def test_catalog_bouquets(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/bouquets",
             json={"items": [{"id": 1, "name": "S", "order": 0}]}, status=200)
    assert isinstance(CatalogResource(transport).bouquets()[0], Bouquet)

@rsps.activate
def test_catalog_streams(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/streams",
             json={"items": [{"id": 1, "name": "Ch", "icon": None,
                              "categories": [{"id": 7, "name": "Sports"}]}],
                   "next_cursor": "x"}, status=200)
    page = CatalogResource(transport).streams(limit=10)
    assert isinstance(page.items[0], Stream)
    assert page.next_cursor == "x"

@rsps.activate
def test_catalog_stream(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/streams/99",
             json={"id": 99, "name": "HBO", "icon": None, "categories": [{"id": 1, "name": "A"}]},
             status=200)
    assert CatalogResource(transport).stream(99).id == 99

@rsps.activate
def test_catalog_vods(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/vods",
             json={"items": [{"id": 1, "name": "X", "icon": None,
                              "year": 2020, "rating": 7.7,
                              "is_serie": False, "categories": []}],
                   "next_cursor": None}, status=200)
    page = CatalogResource(transport).vods(q="X")
    assert isinstance(page.items[0], Vod)

@rsps.activate
def test_catalog_vod(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/vods/1",
             json={"id": 1, "name": "X", "icon": None,
                   "year": None, "rating": None,
                   "is_serie": True, "categories": []}, status=200)
    v = CatalogResource(transport).vod(1)
    assert v.is_serie is True


RESELLER_JSON = {
    "id": 260595, "username": "joshuee", "email": "x@y",
    "member_group_id": 4, "member_group_name": "RESELLER",
    "owner_id": 2432,
    "billing": {"mode": "credits", "credits": 0.25,
                "max_users": None, "active_users": None,
                "billing_expires": None},
    "notes": None, "status": True, "date_registered": 1700000000,
}

@rsps.activate
def test_resellers_list(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/resellers",
             json={"items": [RESELLER_JSON], "next_cursor": None}, status=200)
    page = ResellersResource(transport).list(limit=25)
    assert isinstance(page.items[0], Reseller)

@rsps.activate
def test_resellers_list_server_side_filters(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/resellers",
             json={"items": [RESELLER_JSON], "next_cursor": None}, status=200)
    page = ResellersResource(transport).list(member_group_id=4, status=True,
                                             username="joshuee")
    qs = urllib.parse.parse_qs(
        urllib.parse.urlparse(rsps.calls[0].request.url).query)
    assert qs["member_group_id"] == ["4"]
    assert qs["status"] == ["1"]
    assert qs["username"] == ["joshuee"]
    assert isinstance(page.items[0], Reseller)

@rsps.activate
def test_resellers_list_status_false(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/resellers",
             json={"items": [], "next_cursor": None}, status=200)
    ResellersResource(transport).list(status=False)
    qs = urllib.parse.parse_qs(
        urllib.parse.urlparse(rsps.calls[0].request.url).query)
    assert qs["status"] == ["0"]

@rsps.activate
def test_resellers_create(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (201, {}, json.dumps(dict(RESELLER_JSON, id=500)))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/resellers",
                      callback=cb, content_type="application/json")
    reseller = ResellersResource(transport).create(
        username="new", password="p", email="x@y",
        billing_mode="users", max_users=50, billing_expires=1900000000)
    assert reseller.id == 500
    assert seen["body"]["billing_mode"] == "users"

@rsps.activate
def test_resellers_get(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/resellers/2432",
             json=dict(RESELLER_JSON, id=2432), status=200)
    assert ResellersResource(transport).get(2432).id == 2432

@rsps.activate
def test_resellers_update(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps(RESELLER_JSON))
    rsps.add_callback(rsps.POST, f"{BASE}/panel-api/v1/resellers/260595/update",
                      callback=cb, content_type="application/json")
    ResellersResource(transport).update(260595, {"email": "new@x"})
    assert seen["body"] == {"email": "new@x"}

@rsps.activate
def test_resellers_billing(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/resellers/1/billing",
             json={"mode": "credits", "credits": 10.5,
                   "max_users": None, "active_users": None,
                   "billing_expires": None}, status=200)
    s = ResellersResource(transport).billing(1)
    assert isinstance(s, BillingSnapshot)
    assert s.credits == 10.5

@rsps.activate
def test_resellers_adjust_billing(transport):
    seen = {}
    def cb(request):
        seen["body"] = json.loads(request.body or "{}")
        return (200, {}, json.dumps({"mode": "credits", "credits": 5.5,
                                       "max_users": None, "active_users": None,
                                       "billing_expires": None}))
    rsps.add_callback(rsps.POST,
                      f"{BASE}/panel-api/v1/resellers/1/billing/adjust",
                      callback=cb, content_type="application/json")
    s = ResellersResource(transport).adjust_billing(1, delta=-5.0,
                                                     reason="invoice #42")
    assert seen["body"] == {"delta": -5.0, "reason": "invoice #42"}
    assert s.credits == 5.5


@rsps.activate
def test_me_get(transport):
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/me",
             json={"type": "admin", "reg_user_id": None,
                   "member_group_id": None, "member_group_name": None,
                   "billing": None, "permissions": None,
                   "key": {"id": 42, "prefix": "pk_live_abc",
                            "scopes": ["lines:read"]}},
             status=200)
    me = MeResource(transport).get()
    assert isinstance(me, Identity)
    assert me.type == "admin"
    assert me.key_id == 42
