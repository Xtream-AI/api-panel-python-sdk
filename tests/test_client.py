import responses as rsps
from xtream_ai_panel_api import PanelApiClient


BASE = "https://p.example.com"

def make_client() -> PanelApiClient:
    return PanelApiClient(base_url=BASE, token="pk.x", sleeper=lambda s: None)


def test_exposes_four_resources():
    c = make_client()
    assert c.lines is not None
    assert c.catalog is not None
    assert c.resellers is not None
    assert c.me is not None


@rsps.activate
def test_health_no_auth():
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/health",
             json={"status": "ok", "version": "v1"}, status=200)
    assert make_client().health() == {"status": "ok", "version": "v1"}


def test_last_rate_limit_starts_none():
    assert make_client().last_rate_limit is None


@rsps.activate
def test_last_rate_limit_populated_after_request():
    rsps.add(rsps.GET, f"{BASE}/panel-api/v1/health",
             json={"status": "ok"}, status=200,
             headers={"X-RateLimit-Limit": "300",
                      "X-RateLimit-Remaining": "42",
                      "X-RateLimit-Reset": "1786126673"})
    c = make_client()
    c.health()
    assert c.last_rate_limit is not None
    assert c.last_rate_limit.remaining == 42
