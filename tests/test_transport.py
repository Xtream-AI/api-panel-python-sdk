import json
import requests
import pytest
import responses as rsps

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.exceptions import (
    RateLimitException, BadRequestException, AuthenticationException,
    ValidationException, NotFoundException, AuthorizationException,
    InsufficientCreditsException, ConflictException, ServerException,
    ServiceUnavailableException, UnknownApiException, PanelApiException,
)


@pytest.fixture
def slept():
    return []


@pytest.fixture
def transport(slept):
    return HttpTransport(
        base_url="https://p.example.com",
        token="pk_live_x.y",
        max_retries=3,
        sleeper=slept.append,
    )


@rsps.activate
def test_happy_path_returns_response_and_parses_rate_limit(transport):
    rsps.add(
        rsps.GET, "https://p.example.com/panel-api/v1/me",
        json={"type": "admin", "key": {"id": 1, "prefix": "p", "scopes": []}},
        status=200,
        headers={"X-RateLimit-Limit": "300",
                 "X-RateLimit-Remaining": "299",
                 "X-RateLimit-Reset": "1786126673"},
    )
    resp = transport.request("GET", "/panel-api/v1/me")
    assert resp.status == 200
    assert resp.rate_limit.remaining == 299


@rsps.activate
def test_429_is_retried_respecting_retry_after(transport, slept):
    for _ in range(2):
        rsps.add(
            rsps.GET, "https://p.example.com/panel-api/v1/health",
            json={"error": "rate_limited", "message": ".", "request_id": "r"},
            status=429, headers={"Retry-After": "2"},
        )
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/health",
             json={"status": "ok"}, status=200)
    resp = transport.request("GET", "/panel-api/v1/health")
    assert resp.status == 200
    assert len(rsps.calls) == 3

    assert slept == [2.0, 2.0]


@rsps.activate
def test_network_error_is_retried(slept):
    from unittest.mock import patch
    calls = [0]
    real_session = HttpTransport(base_url="https://p.example.com",
                                  token="pk.x", max_retries=3,
                                  sleeper=slept.append)
    def side_effect(*a, **kw):
        calls[0] += 1
        if calls[0] < 3:
            raise requests.ConnectionError("dns failure")

        r = requests.Response()
        r.status_code = 200
        r._content = b'{"status":"ok"}'
        r.headers = {}
        return r
    with patch.object(real_session._session, "request", side_effect=side_effect):
        resp = real_session.request("GET", "/panel-api/v1/health")
    assert resp.status == 200
    assert calls[0] == 3
    assert len(slept) == 2


@rsps.activate
def test_in_flight_idempotency_is_retried(transport):
    for _ in range(2):
        rsps.add(rsps.POST, "https://p.example.com/panel-api/v1/lines",
                 json={"error": "idempotency_in_flight",
                       "message": "still processing", "request_id": "r"},
                 status=409)
    rsps.add(rsps.POST, "https://p.example.com/panel-api/v1/lines",
             json={"id": 1}, status=201)
    resp = transport.request("POST", "/panel-api/v1/lines", body={"package_id": 1})
    assert resp.status == 201
    assert len(rsps.calls) == 3


@rsps.activate
def test_malformed_retry_after_falls_back_to_backoff(transport, slept):
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/health",
             json={"error": "rate_limited", "message": ".", "request_id": "r"},
             status=429, headers={"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"})
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/health",
             json={"status": "ok"}, status=200)
    transport.request("GET", "/panel-api/v1/health")
    assert slept[0] > 1.9


@rsps.activate
def test_rate_limit_headers_parsed_on_4xx(transport):
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/packages",
             json={"error": "insufficient_scope", "message": "nope",
                   "request_id": "r"},
             status=403,
             headers={"X-RateLimit-Limit": "300",
                      "X-RateLimit-Remaining": "42",
                      "X-RateLimit-Reset": "1786126673"})
    with pytest.raises(AuthorizationException):
        transport.request("GET", "/panel-api/v1/packages")
    assert transport.last_rate_limit is not None
    assert transport.last_rate_limit.remaining == 42


@rsps.activate
def test_5xx_is_retried_then_succeeds(transport):
    for _ in range(2):
        rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/health",
                 json={"error": "api_disabled", "message": "."}, status=503)
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/health",
             json={"status": "ok"}, status=200)
    resp = transport.request("GET", "/panel-api/v1/health")
    assert resp.status == 200


@rsps.activate
def test_4xx_non_429_is_never_retried(transport):
    rsps.add(
        rsps.POST, "https://p.example.com/panel-api/v1/lines",
        json={"error": "validation_error", "message": "bad", "request_id": "r",
              "details": {"field": "username"}},
        status=422,
    )
    with pytest.raises(ValidationException) as excinfo:
        transport.request("POST", "/panel-api/v1/lines", body={"x": 1})
    assert excinfo.value.field == "username"
    assert len(rsps.calls) == 1


@rsps.activate
def test_max_retries_exhausted_5xx():
    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                       max_retries=2, sleeper=lambda s: None)
    for _ in range(3):
        rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/me",
                 json={"error": "internal_error", "message": "b",
                       "request_id": "r"}, status=500)
    with pytest.raises(ServerException):
        t.request("GET", "/panel-api/v1/me")
    assert len(rsps.calls) == 3


@rsps.activate
def test_idempotency_key_auto_generated(transport):
    seen = []
    def cb(request):
        seen.append(request.headers.get("Idempotency-Key"))
        return (201, {}, json.dumps({"id": 1}))
    rsps.add_callback(rsps.POST, "https://p.example.com/panel-api/v1/lines",
                      callback=cb, content_type="application/json")
    transport.request("POST", "/panel-api/v1/lines", body={"package_id": 1})
    assert seen == [seen[0]]
    assert len(seen[0]) == 32
    assert all(c in "0123456789abcdef" for c in seen[0])


@rsps.activate
def test_idempotency_key_manual_is_respected(transport):
    seen = []
    def cb(request):
        seen.append(request.headers.get("Idempotency-Key"))
        return (201, {}, json.dumps({"id": 1}))
    rsps.add_callback(rsps.POST, "https://p.example.com/panel-api/v1/lines",
                      callback=cb, content_type="application/json")
    transport.request("POST", "/panel-api/v1/lines",
                      body={"package_id": 1}, idempotency_key="invoice-42")
    assert seen == ["invoice-42"]


@rsps.activate
def test_same_idempotency_key_on_retry(transport):
    seen = []
    call = [0]
    def cb(request):
        call[0] += 1
        seen.append(request.headers.get("Idempotency-Key"))
        if call[0] < 3:
            return (503, {}, json.dumps({"error": "api_disabled",
                                         "message": "x"}))
        return (201, {}, json.dumps({"id": 1}))
    rsps.add_callback(rsps.POST, "https://p.example.com/panel-api/v1/lines",
                      callback=cb, content_type="application/json")
    transport.request("POST", "/panel-api/v1/lines", body={"package_id": 1})
    assert len(seen) == 3
    assert seen[0] == seen[1] == seen[2]


@pytest.mark.parametrize("status,slug,exc_class", [

    (400, "invalid_body",                        BadRequestException),
    (400, "missing_idempotency_key",             BadRequestException),

    (401, "invalid_key",                         AuthenticationException),
    (401, "caller_disabled",                     AuthenticationException),

    (402, "insufficient_credits",                InsufficientCreditsException),
    (402, "billing_expired",                     InsufficientCreditsException),

    (403, "insufficient_scope",                  AuthorizationException),
    (403, "admin_only_endpoint",                 AuthorizationException),
    (403, "admin_only_field",                    AuthorizationException),
    (403, "owner_must_be_self",                  AuthorizationException),
    (403, "delete_not_allowed",                  AuthorizationException),
    (403, "password_change_not_allowed",         AuthorizationException),
    (403, "sub_reseller_creation_not_allowed",   AuthorizationException),

    (404, "not_found",                           NotFoundException),
    (404, "caller_not_found",                    NotFoundException),

    (409, "idempotency_conflict",                ConflictException),

    (422, "validation_error",                    ValidationException),
    (422, "cap_below_active_users",              ValidationException),
    (422, "negative_balance_not_allowed",        ValidationException),
    (422, "negative_cap_not_allowed",            ValidationException),
    (422, "billing_expires_required",            ValidationException),
    (422, "mismatched_mode",                     ValidationException),
    (422, "no_sub_reseller_setup",               ValidationException),
    (422, "owner_id_required",                   ValidationException),
    (422, "line_has_no_expiry",                  ValidationException),
    (422, "trial_flag_requires_trial_package",   ValidationException),
    (422, "renew_with_trial_package_not_allowed", ValidationException),

    (422, "insufficient_slots",                  InsufficientCreditsException),


    (500, "internal_error",                      ServerException),
    (500, "delete_failed",                       ServerException),
    (503, "api_disabled",                        ServiceUnavailableException),
    (503, "service_unavailable",                 ServiceUnavailableException),

    (418, "anything",                            UnknownApiException),
    (501, "not_implemented",                     ServerException),
])
@rsps.activate
def test_error_mapping(status, slug, exc_class):


    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                       max_retries=0, sleeper=lambda s: None)
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/me",
             json={"error": slug, "message": "x", "request_id": "r"},
             status=status, headers={"Retry-After": "2"})
    with pytest.raises(exc_class) as excinfo:
        t.request("GET", "/panel-api/v1/me")
    assert excinfo.value.slug == slug


@rsps.activate
def test_429_extracts_retry_after_from_header():
    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                       max_retries=0, sleeper=lambda s: None)
    rsps.add(rsps.GET, "https://p.example.com/panel-api/v1/me",
             json={"error": "rate_limited", "message": "x", "request_id": "r"},
             status=429, headers={"Retry-After": "42"})
    with pytest.raises(RateLimitException) as excinfo:
        t.request("GET", "/panel-api/v1/me")
    assert excinfo.value.retry_after == 42


from unittest.mock import MagicMock, patch


@pytest.mark.parametrize("bad_key", [
    "k\r\nX-Injected: pwned",
    "k\nX-Injected: pwned",
    "k\rX-Injected: pwned",
])
def test_crlf_in_idempotency_key_raises_before_wire(bad_key, slept):
    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                      max_retries=3, sleeper=slept.append)
    mock_req = MagicMock()
    with patch.object(t._session, "request", mock_req):
        with pytest.raises(ValueError) as excinfo:
            t.request("POST", "/panel-api/v1/lines",
                      body={"package_id": 1}, idempotency_key=bad_key)

    assert not isinstance(excinfo.value, PanelApiException)


    assert "Idempotency-Key" in str(excinfo.value)
    assert "pwned" not in str(excinfo.value)
    assert mock_req.call_count == 0
    assert slept == []


def test_crlf_in_extra_header_value_raises_before_wire(slept):
    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                      max_retries=3, sleeper=slept.append)
    mock_req = MagicMock()
    with patch.object(t._session, "request", mock_req):
        with pytest.raises(ValueError):
            t.request("POST", "/panel-api/v1/lines", body={"package_id": 1},
                      extra_headers={"X-Foo": "v\r\nX-Injected: pwned"})
    assert mock_req.call_count == 0
    assert slept == []


def test_crlf_in_extra_header_name_raises_before_wire(slept):
    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                      max_retries=3, sleeper=slept.append)
    mock_req = MagicMock()
    with patch.object(t._session, "request", mock_req):
        with pytest.raises(ValueError):
            t.request("POST", "/panel-api/v1/lines", body={"package_id": 1},
                      extra_headers={"X-A\r\nX-Evil": "v"})
    assert mock_req.call_count == 0
    assert slept == []


def test_crlf_in_token_raises_before_wire(slept):


    t = HttpTransport(base_url="https://p.example.com",
                      token="pk\r\nX-Injected: pwned",
                      max_retries=3, sleeper=slept.append)
    mock_req = MagicMock()
    with patch.object(t._session, "request", mock_req):
        with pytest.raises(ValueError):
            t.request("GET", "/panel-api/v1/me")
    assert mock_req.call_count == 0
    assert slept == []


@rsps.activate
def test_crlf_guard_does_not_overblock(transport):
    seen = []
    def cb(request):
        seen.append(request.headers)
        return (201, {}, json.dumps({"id": 1}))
    rsps.add_callback(rsps.POST, "https://p.example.com/panel-api/v1/lines",
                      callback=cb, content_type="application/json")
    resp = transport.request(
        "POST", "/panel-api/v1/lines", body={"package_id": 1},
        idempotency_key="invoice 42\twith tab",
        extra_headers={"X-Note": "value with spaces"},
    )
    assert resp.status == 201
    assert len(rsps.calls) == 1
    assert seen[0].get("Idempotency-Key") == "invoice 42\twith tab"
    assert seen[0].get("X-Note") == "value with spaces"
    assert seen[0].get("Authorization") == "Bearer pk_live_x.y"
    assert seen[0].get("Content-Type") == "application/json"


@rsps.activate
def test_in_flight_backoff_schedule_matches_php(slept):
    t = HttpTransport(base_url="https://p.example.com", token="pk.x",
                      max_retries=3, sleeper=slept.append)
    for _ in range(3):
        rsps.add(rsps.POST, "https://p.example.com/panel-api/v1/lines",
                 json={"error": "idempotency_in_flight", "message": "x",
                       "request_id": "r"}, status=409)
    rsps.add(rsps.POST, "https://p.example.com/panel-api/v1/lines",
             json={"id": 1}, status=201)
    resp = t.request("POST", "/panel-api/v1/lines", body={"package_id": 1})
    assert resp.status == 201
    assert len(rsps.calls) == 4
    assert slept == [1, 2, 4]
