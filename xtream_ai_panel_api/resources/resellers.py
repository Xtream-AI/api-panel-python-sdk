from __future__ import annotations
from typing import Any
from urllib.parse import urlencode

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.models import (
    Reseller, BillingSnapshot, PaginatedResponse,
)


class ResellersResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def list(self, limit: int | None = None,
              cursor: str | None = None,
              member_group_id: int | None = None,
              status: bool | None = None,
              username: str | None = None) -> PaginatedResponse[Reseller]:
        q: dict[str, str] = {}
        if limit is not None:            q["limit"] = str(limit)
        if cursor is not None:           q["cursor"] = cursor
        if member_group_id is not None:  q["member_group_id"] = str(member_group_id)
        if status is not None:           q["status"] = "1" if status else "0"
        if username is not None:         q["username"] = username
        path = "/panel-api/v1/resellers" + ("?" + urlencode(q) if q else "")
        r = self._transport.request("GET", path)
        return PaginatedResponse.from_dict(r.body, Reseller.from_dict)

    def create(
        self,
        username: str,
        password: str,
        email: str,
        member_group_id: int | None = None,
        credits: float | None = None,
        billing_mode: str | None = None,
        max_users: int | None = None,
        billing_expires: int | None = None,
        owner_id: int | None = None,
        notes: str | None = None,
        idempotency_key: str | None = None,
    ) -> Reseller:
        body: dict[str, Any] = {"username": username, "password": password,
                                 "email": email}
        if member_group_id is not None:  body["member_group_id"] = member_group_id
        if credits is not None:          body["credits"] = credits
        if billing_mode is not None:     body["billing_mode"] = billing_mode
        if max_users is not None:        body["max_users"] = max_users
        if billing_expires is not None:  body["billing_expires"] = billing_expires
        if owner_id is not None:         body["owner_id"] = owner_id
        if notes is not None:            body["notes"] = notes
        r = self._transport.request("POST", "/panel-api/v1/resellers",
                                     body=body, idempotency_key=idempotency_key)
        return Reseller.from_dict(r.body)

    def get(self, id: int) -> Reseller:
        r = self._transport.request("GET", f"/panel-api/v1/resellers/{id}")
        return Reseller.from_dict(r.body)

    def update(self, id: int, fields: dict[str, Any],
                idempotency_key: str | None = None) -> Reseller:
        r = self._transport.request("POST",
                                     f"/panel-api/v1/resellers/{id}/update",
                                     body=fields, idempotency_key=idempotency_key)
        return Reseller.from_dict(r.body)

    def billing(self, id: int) -> BillingSnapshot:
        r = self._transport.request("GET",
                                     f"/panel-api/v1/resellers/{id}/billing")
        return BillingSnapshot.from_dict(r.body)

    def adjust_billing(self, id: int, delta: float,
                        reason: str | None = None,
                        idempotency_key: str | None = None) -> BillingSnapshot:
        body: dict[str, Any] = {"delta": delta}
        if reason is not None:
            body["reason"] = reason
        r = self._transport.request(
            "POST", f"/panel-api/v1/resellers/{id}/billing/adjust",
            body=body, idempotency_key=idempotency_key)
        return BillingSnapshot.from_dict(r.body)
