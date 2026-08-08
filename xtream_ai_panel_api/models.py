
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Generic, TypeVar


def _ts_to_dt(v: Any) -> datetime | None:
    if v is None or v == 0 or v == "":
        return None
    return datetime.fromtimestamp(int(v), tz=timezone.utc)


T = TypeVar("T")


@dataclass(frozen=True)
class Line:
    id: int
    username: str
    password: str
    member_id: int
    exp_date: datetime | None
    max_connections: int
    is_trial: bool
    is_restreamer: bool
    enabled: bool
    admin_enabled: bool
    bouquets: list[int]
    created_at: datetime | None

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Line":
        return cls(
            id=int(j["id"]),
            username=str(j["username"]),
            password=str(j["password"]),
            member_id=int(j["member_id"]),
            exp_date=_ts_to_dt(j.get("exp_date")),
            max_connections=int(j["max_connections"]),
            is_trial=bool(j.get("is_trial", False)),
            is_restreamer=bool(j.get("is_restreamer", False)),
            enabled=bool(j.get("enabled", False)),
            admin_enabled=bool(j.get("admin_enabled", False)),
            bouquets=[int(x) for x in j.get("bouquets", [])],
            created_at=_ts_to_dt(j.get("created_at")),
        )


@dataclass(frozen=True)
class Package:
    id: int
    package_name: str
    is_trial: bool
    is_official: bool
    official_credits: float
    official_duration: int
    official_duration_in: str
    trial_credits: float
    trial_duration: int
    trial_duration_in: str
    max_connections: int
    is_restreamer: bool
    forced_country: str

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Package":
        return cls(
            id=int(j["id"]),
            package_name=str(j["package_name"]),
            is_trial=bool(j["is_trial"]),
            is_official=bool(j["is_official"]),
            official_credits=float(j["official_credits"]),
            official_duration=int(j["official_duration"]),
            official_duration_in=str(j["official_duration_in"]),
            trial_credits=float(j["trial_credits"]),
            trial_duration=int(j["trial_duration"]),
            trial_duration_in=str(j["trial_duration_in"]),
            max_connections=int(j["max_connections"]),
            is_restreamer=bool(j["is_restreamer"]),
            forced_country=str(j.get("forced_country", "")),
        )


@dataclass(frozen=True)
class Bouquet:
    id: int
    name: str
    order: int

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Bouquet":
        return cls(id=int(j["id"]), name=str(j["name"]),
                   order=int(j.get("order", 0)))


@dataclass(frozen=True)
class Category:
    id: int
    name: str

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Category":
        return cls(id=int(j["id"]), name=str(j.get("name", "")))


@dataclass(frozen=True)
class Stream:
    id: int
    name: str
    icon: str
    categories: list[Category]

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Stream":
        return cls(
            id=int(j["id"]),
            name=str(j["name"]),
            icon=str(j.get("icon") or ""),
            categories=[Category.from_dict(c) for c in j.get("categories", [])],
        )


@dataclass(frozen=True)
class Vod:
    id: int
    name: str
    icon: str
    year: int | None
    rating: float | None
    is_serie: bool
    categories: list[Category]

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Vod":
        return cls(
            id=int(j["id"]),
            name=str(j["name"]),
            icon=str(j.get("icon") or ""),
            year=int(j["year"]) if j.get("year") is not None else None,
            rating=float(j["rating"]) if j.get("rating") is not None else None,
            is_serie=bool(j.get("is_serie", False)),
            categories=[Category.from_dict(c) for c in j.get("categories", [])],
        )


@dataclass(frozen=True)
class BillingSnapshot:
    mode: str
    credits: float | None
    max_users: int | None
    active_users: int | None
    billing_expires: datetime | None

    @classmethod
    def from_dict(cls, j: dict[str, Any] | None) -> "BillingSnapshot | None":
        if j is None:
            return None
        return cls(
            mode=str(j["mode"]),
            credits=float(j["credits"]) if j.get("credits") is not None else None,
            max_users=int(j["max_users"]) if j.get("max_users") is not None else None,
            active_users=int(j["active_users"]) if j.get("active_users") is not None else None,
            billing_expires=_ts_to_dt(j.get("billing_expires")),
        )


@dataclass(frozen=True)
class Reseller:
    id: int
    username: str
    email: str
    member_group_id: int
    member_group_name: str | None
    owner_id: int | None
    billing: BillingSnapshot | None
    notes: str | None
    status: bool
    date_registered: datetime | None
    credits_charged: float | None

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Reseller":

        billing: BillingSnapshot | None = None
        nested = j.get("billing")
        if isinstance(nested, dict):
            billing = BillingSnapshot.from_dict(nested)
        elif "billing_mode" in j:
            billing = BillingSnapshot.from_dict({
                "mode":            j["billing_mode"],
                "credits":         j.get("credits"),
                "max_users":       j.get("max_users"),
                "active_users":    j.get("active_users"),
                "billing_expires": j.get("billing_expires"),
            })


        ts = j.get("date_registered")
        if ts is None:
            ts = j.get("created_at")


        if "status" in j:
            raw = j["status"]
            status = bool(raw) if isinstance(raw, bool) else int(raw) == 1
        else:
            status = True

        return cls(
            id=int(j["id"]),
            username=str(j["username"]),
            email=str(j.get("email", "")),
            member_group_id=int(j["member_group_id"]),
            member_group_name=(str(j["member_group_name"])
                                if j.get("member_group_name") is not None else None),
            owner_id=int(j["owner_id"]) if j.get("owner_id") is not None else None,
            billing=billing,
            notes=str(j["notes"]) if j.get("notes") is not None else None,
            status=status,
            date_registered=_ts_to_dt(ts),
            credits_charged=(float(j["credits_charged"])
                              if j.get("credits_charged") is not None else None),
        )


@dataclass(frozen=True)
class Identity:
    type: str
    reg_user_id: int | None
    member_group_id: int | None
    member_group_name: str | None
    billing: BillingSnapshot | None
    permissions: dict[str, Any] | None
    key_id: int
    key_prefix: str
    scopes: list[str]

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Identity":
        key = j["key"]
        return cls(
            type=str(j["type"]),
            reg_user_id=int(j["reg_user_id"]) if j.get("reg_user_id") is not None else None,
            member_group_id=int(j["member_group_id"]) if j.get("member_group_id") is not None else None,
            member_group_name=str(j["member_group_name"]) if j.get("member_group_name") is not None else None,
            billing=BillingSnapshot.from_dict(j.get("billing")),
            permissions=j.get("permissions"),
            key_id=int(key["id"]),
            key_prefix=str(key["prefix"]),
            scopes=[str(s) for s in key.get("scopes", [])],
        )


@dataclass(frozen=True)
class Connection:
    connection_id: int
    content_type: str
    content_id: int | None
    content_name: str
    started_at: datetime
    elapsed_sec: int
    client_ip: str
    client_country: str
    is_serie: bool | None

    @classmethod
    def from_dict(cls, j: dict[str, Any]) -> "Connection":
        started = _ts_to_dt(j.get("started_at"))


        if started is None:
            raise ValueError("Connection.from_dict: 'started_at' is required")
        return cls(
            connection_id=int(j["connection_id"]),
            content_type=str(j["content_type"]),
            content_id=int(j["content_id"]) if j.get("content_id") is not None else None,
            content_name=str(j.get("content_name", "")),
            started_at=started,
            elapsed_sec=int(j.get("elapsed_sec", 0)),
            client_ip=str(j.get("client_ip", "")),
            client_country=str(j.get("client_country", "")),
            is_serie=bool(j["is_serie"]) if "is_serie" in j else None,
        )


@dataclass(frozen=True)
class RateLimitInfo:
    limit: int
    remaining: int
    reset_at: datetime

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> "RateLimitInfo | None":
        lower = {k.lower(): v for k, v in headers.items()}
        l = lower.get("x-ratelimit-limit")
        r = lower.get("x-ratelimit-remaining")
        x = lower.get("x-ratelimit-reset")
        if l is None or r is None or x is None:
            return None
        return cls(limit=int(l), remaining=int(r),
                   reset_at=datetime.fromtimestamp(int(x), tz=timezone.utc))


@dataclass(frozen=True)
class PaginatedResponse(Generic[T]):
    items: list[T]
    next_cursor: str | None

    @classmethod
    def from_dict(cls, j: dict[str, Any],
                   factory: Callable[[dict[str, Any]], T]) -> "PaginatedResponse[T]":
        items = [factory(x) for x in j.get("items", [])]
        cursor = j.get("next_cursor")
        return cls(items=items, next_cursor=str(cursor) if cursor is not None else None)
