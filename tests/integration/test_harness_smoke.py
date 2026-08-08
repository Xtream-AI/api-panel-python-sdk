
import os
import pytest
import requests

from xtream_ai_panel_api import PanelApiClient
from xtream_ai_panel_api.exceptions import ValidationException


@pytest.fixture(scope="module")
def client():
    url = os.environ.get("HARNESS_URL", "http://127.0.0.1:9955")
    token = os.environ.get("HARNESS_TOKEN", "")
    if not token:
        pytest.skip("HARNESS_TOKEN env var not set.")
    try:
        r = requests.get(f"{url}/panel-api/v1/health", timeout=2)
        if r.status_code != 200:
            pytest.skip(f"Harness not reachable at {url} ({r.status_code}).")
    except requests.RequestException as e:
        pytest.skip(f"Harness not reachable at {url}: {e}")
    return PanelApiClient(base_url=url, token=token)


def test_health(client):
    h = client.health()
    assert h["status"] == "ok"


def test_me(client):
    me = client.me.get()
    assert me.type == "admin"
    assert len(me.scopes) > 0


def test_list_lines(client):
    page = client.lines.list(limit=3)
    assert isinstance(page.items, list)


def test_list_packages(client):
    p = client.catalog.packages()
    assert isinstance(p, list)


def test_validation_error_surface(client):
    with pytest.raises(ValidationException):
        client.lines.create(package_id=999999, member_id=260595)
