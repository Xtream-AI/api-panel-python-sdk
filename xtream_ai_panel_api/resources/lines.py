from __future__ import annotations
from typing import Any
from urllib.parse import urlencode

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.models import Line, Connection, PaginatedResponse


_UNSET: Any = object()


class LinesResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def create(
        self,
        package_id: int,
        member_id: int | None = None,
        username: str | None = None,
        password: str | None = None,
        bouquets: list[int] | None = None,
        max_connections: int | None = None,
        is_trial: bool | None = None,
        is_restreamer: bool | None = None,
        email: str | None = None,
        notes: str | None = None,
        exp_date: int | None = None,
        allowed_ips: list[str] | None = None,
        allowed_ua: list[str] | None = None,
        is_isplock: bool | None = None,
        idempotency_key: str | None = None,
    ) -> Line:


        body: dict[str, Any] = {"package_id": package_id}
        if member_id is not None:       body["member_id"] = member_id
        if username is not None:        body["username"] = username
        if password is not None:        body["password"] = password
        if bouquets is not None:        body["bouquets"] = [int(b) for b in bouquets]
        if max_connections is not None: body["max_connections"] = max_connections
        if is_trial is not None:        body["is_trial"] = is_trial
        if is_restreamer is not None:   body["is_restreamer"] = is_restreamer
        if email is not None:           body["email"] = email
        if notes is not None:           body["notes"] = notes
        if exp_date is not None:        body["exp_date"] = exp_date
        if allowed_ips is not None:     body["allowed_ips"] = [str(x) for x in allowed_ips]
        if allowed_ua is not None:      body["allowed_ua"] = [str(x) for x in allowed_ua]
        if is_isplock is not None:      body["is_isplock"] = is_isplock

        r = self._transport.request("POST", "/panel-api/v1/lines",
                                     body=body, idempotency_key=idempotency_key)
        return Line.from_dict(r.body)

    def list(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        username: str | None = None,
        password: str | None = None,
        enabled: bool | None = None,
        is_trial: bool | None = None,
    ) -> PaginatedResponse[Line]:
        q: dict[str, str] = {}
        if limit is not None:    q["limit"]    = str(limit)
        if cursor is not None:   q["cursor"]   = cursor
        if username is not None: q["username"] = username
        if password is not None: q["password"] = password
        if enabled is not None:  q["enabled"]  = "true" if enabled else "false"
        if is_trial is not None: q["is_trial"] = "true" if is_trial else "false"
        path = "/panel-api/v1/lines" + ("?" + urlencode(q) if q else "")
        r = self._transport.request("GET", path)
        return PaginatedResponse.from_dict(r.body, Line.from_dict)

    def get(self, id: int) -> Line:
        r = self._transport.request("GET", f"/panel-api/v1/lines/{id}")
        return Line.from_dict(r.body)

    def update(
        self,
        id: int,
        password: str | None = None,
        enabled: bool | None = None,
        is_restreamer: bool | None = None,
        max_connections: int | None = None,
        exp_date: Any = _UNSET,
        admin_enabled: bool | None = None,
        allowed_ips: list[str] | None = None,
        allowed_ua: list[str] | None = None,
        idempotency_key: str | None = None,
        *,
        bouquets: list[int] | None = None,
        notes: str | None = None,
        package_id: int | None = None,
    ) -> Line:


        body: dict[str, Any] = {}
        if password is not None:        body["password"] = password
        if enabled is not None:         body["enabled"] = enabled
        if is_restreamer is not None:   body["is_restreamer"] = is_restreamer
        if max_connections is not None: body["max_connections"] = max_connections
        if exp_date is not _UNSET:      body["exp_date"] = exp_date if exp_date is None else int(exp_date)
        if admin_enabled is not None:   body["admin_enabled"] = admin_enabled
        if allowed_ips is not None:     body["allowed_ips"] = [str(x) for x in allowed_ips]
        if allowed_ua is not None:      body["allowed_ua"] = [str(x) for x in allowed_ua]
        if bouquets is not None:        body["bouquets"] = [int(b) for b in bouquets]
        if notes is not None:           body["notes"] = notes
        if package_id is not None:      body["package_id"] = int(package_id)
        r = self._transport.request("POST", f"/panel-api/v1/lines/{id}/update",
                                     body=body, idempotency_key=idempotency_key)
        return Line.from_dict(r.body)

    def enable(self, id: int, idempotency_key: str | None = None) -> Line:
        r = self._transport.request("POST", f"/panel-api/v1/lines/{id}/enable",
                                     body={}, idempotency_key=idempotency_key)
        return Line.from_dict(r.body)

    def disable(self, id: int, idempotency_key: str | None = None) -> Line:
        r = self._transport.request("POST", f"/panel-api/v1/lines/{id}/disable",
                                     body={}, idempotency_key=idempotency_key)
        return Line.from_dict(r.body)

    def renew(self, id: int, package_id: int | None = None,
              idempotency_key: str | None = None,
              *,
              bouquets: list[int] | None = None) -> Line:
        body: dict[str, Any] = {}
        if package_id is not None:
            body["package_id"] = package_id
        if bouquets is not None:
            body["bouquets"] = [int(b) for b in bouquets]
        r = self._transport.request("POST", f"/panel-api/v1/lines/{id}/renew",
                                     body=body, idempotency_key=idempotency_key)
        return Line.from_dict(r.body)

    def reset_password(self, id: int, password: str | None = None,
                       idempotency_key: str | None = None) -> str:


        body: dict[str, Any] = {}
        if password is not None:
            body["password"] = password
        r = self._transport.request("POST",
                                     f"/panel-api/v1/lines/{id}/reset-password",
                                     body=body, idempotency_key=idempotency_key)
        return str(r.body.get("password", ""))

    def delete(self, id: int, idempotency_key: str | None = None) -> bool:
        r = self._transport.request("POST", f"/panel-api/v1/lines/{id}/delete",
                                     body={}, idempotency_key=idempotency_key)
        return bool(r.body.get("deleted", False))

    def connections(self, id: int) -> list[Connection]:
        r = self._transport.request("GET",
                                     f"/panel-api/v1/lines/{id}/connections")
        return [Connection.from_dict(x) for x in r.body.get("items", [])]
