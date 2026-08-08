
from __future__ import annotations
import json
import random
import time
import uuid
from dataclasses import dataclass
from typing import Any, Callable

import requests

from xtream_ai_panel_api._version import __version__
from xtream_ai_panel_api.models import RateLimitInfo
from xtream_ai_panel_api.exceptions import (
    PanelApiException, AuthenticationException, BadRequestException,
    InsufficientCreditsException, AuthorizationException, NotFoundException,
    ConflictException, ValidationException, RateLimitException,
    ServerException, ServiceUnavailableException, UnknownApiException,
)


USER_AGENT = f"xtreamai-panel-api-python/{__version__}"


@dataclass
class Response:
    status: int
    headers: dict[str, str]
    body: dict[str, Any]
    rate_limit: RateLimitInfo | None


class HttpTransport:
    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout
        self._max_retries = max_retries
        self._session = session or requests.Session()
        self._sleep = sleeper or time.sleep
        self.last_rate_limit: RateLimitInfo | None = None

    def request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> Response:

        if method != "GET" and idempotency_key is None:
            idempotency_key = uuid.uuid4().hex

        url = self._base_url + path
        headers = self._build_headers(idempotency_key, body is not None,
                                       extra_headers or {})
        raw_body = json.dumps(body) if body is not None else None
        attempt = 0

        while True:
            try:
                r = self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    data=raw_body,
                    timeout=(self._timeout, self._timeout * 2),
                )
            except requests.RequestException as e:

                if attempt < self._max_retries:
                    attempt += 1
                    self._sleep(self._backoff(attempt))
                    continue
                raise ServerException(
                    slug="network_error",
                    message=f"Network error: {e.__class__.__name__}: {e}",
                    request_id=None,
                    details={},
                    status_code=0,
                ) from e


            resp_headers = {k.lower(): v for k, v in r.headers.items()}
            try:
                parsed = r.json() if r.text else {}
                if not isinstance(parsed, dict):
                    parsed = {}
            except ValueError:


                parsed = {}


            rl = RateLimitInfo.from_headers(resp_headers)
            self.last_rate_limit = rl
            response = Response(status=r.status_code, headers=resp_headers,
                                 body=parsed, rate_limit=rl)

            slug = str(parsed.get("error", "")) if isinstance(parsed, dict) else ""

            if r.status_code == 429 and attempt < self._max_retries:
                attempt += 1
                wait = self._parse_retry_after_or_backoff(
                    resp_headers.get("retry-after"), self._backoff(attempt))
                self._sleep(wait)
                continue
            if 500 <= r.status_code < 600 and attempt < self._max_retries:
                attempt += 1
                self._sleep(self._backoff(attempt))
                continue
            if (r.status_code == 409 and slug == "idempotency_in_flight"
                    and attempt < self._max_retries):


                self._sleep(min(2 ** attempt, 4))
                attempt += 1
                continue

            if 200 <= r.status_code < 300:
                return response
            raise self._map_exception(r.status_code, parsed, resp_headers)

    @staticmethod
    def _parse_retry_after_or_backoff(header: str | None, backoff: float) -> float:
        if header is None:
            return backoff
        s = header.strip()
        if not s or not s.isdigit():
            return backoff
        n = int(s)
        if n <= 0:
            return backoff
        return float(min(n, 60))

    def _build_headers(self, idem: str | None, has_body: bool,
                        extra: dict[str, str]) -> dict[str, str]:


        self._assert_no_crlf("Authorization", f"Bearer {self._token}")
        h = {
            "Authorization": f"Bearer {self._token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
        if has_body:
            h["Content-Type"] = "application/json"
        if idem is not None:
            self._assert_no_crlf("Idempotency-Key", idem)
            h["Idempotency-Key"] = idem
        for _name, _value in extra.items():
            self._assert_no_crlf(_name, _value)
        h.update(extra)
        return h

    @staticmethod
    def _assert_no_crlf(name: str, value: str) -> None:
        if "\r" in name or "\n" in name or "\r" in value or "\n" in value:
            raise ValueError(f"Illegal CR/LF in HTTP header '{name}'")

    def _backoff(self, attempt: int) -> float:
        base = min(2 ** attempt, 30)
        return base + random.random() * 0.5

    def _map_exception(self, status: int, body: dict[str, Any],
                        headers: dict[str, str]) -> PanelApiException:
        slug = str(body.get("error", "unknown"))
        msg = str(body.get("message", f"HTTP {status}"))
        request_id = body.get("request_id")
        details = body.get("details") or {}
        if not isinstance(details, dict):
            details = {}


        if status == 422 and slug == "insufficient_slots":
            return InsufficientCreditsException(slug, msg, request_id, details, 422)

        if status == 400:
            return BadRequestException(slug, msg, request_id, details, 400)
        if status == 401:
            return AuthenticationException(slug, msg, request_id, details, 401)
        if status == 402:
            return InsufficientCreditsException(slug, msg, request_id, details, 402)
        if status == 403:
            return AuthorizationException(slug, msg, request_id, details, 403)
        if status == 404:
            return NotFoundException(slug, msg, request_id, details, 404)
        if status == 409:
            return ConflictException(slug, msg, request_id, details, 409)
        if status == 422:
            return ValidationException(slug, msg, request_id, details, 422)
        if status == 429:
            retry_after = int(self._parse_retry_after_or_backoff(
                headers.get("retry-after"), 60.0))
            return RateLimitException(slug, msg, request_id, details, 429,
                                       retry_after=retry_after)
        if status == 503:
            return ServiceUnavailableException(slug, msg, request_id, details, 503)
        if status >= 500:
            return ServerException(slug, msg, request_id, details, status)


        return UnknownApiException(slug, msg, request_id, details, status)
