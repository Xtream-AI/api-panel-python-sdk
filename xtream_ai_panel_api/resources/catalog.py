from __future__ import annotations
from urllib.parse import urlencode

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.models import (
    Package, Bouquet, Stream, Vod, PaginatedResponse,
)


class CatalogResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def packages(self) -> list[Package]:
        r = self._transport.request("GET", "/panel-api/v1/packages")
        return [Package.from_dict(x) for x in r.body.get("items", [])]

    def bouquets(self) -> list[Bouquet]:
        r = self._transport.request("GET", "/panel-api/v1/bouquets")
        return [Bouquet.from_dict(x) for x in r.body.get("items", [])]

    def streams(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        category_id: int | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[Stream]:
        q: dict[str, str] = {}
        if limit is not None:       q["limit"]       = str(limit)
        if cursor is not None:      q["cursor"]      = cursor
        if category_id is not None: q["category_id"] = str(category_id)
        if search is not None:      q["q"]           = search
        path = "/panel-api/v1/streams" + ("?" + urlencode(q) if q else "")
        r = self._transport.request("GET", path)
        return PaginatedResponse.from_dict(r.body, Stream.from_dict)

    def stream(self, id: int) -> Stream:
        r = self._transport.request("GET", f"/panel-api/v1/streams/{id}")
        return Stream.from_dict(r.body)

    def vods(
        self,
        limit: int | None = None,
        cursor: str | None = None,
        category_id: int | None = None,
        q: str | None = None,
    ) -> PaginatedResponse[Vod]:
        query: dict[str, str] = {}
        if limit is not None:       query["limit"] = str(limit)
        if cursor is not None:      query["cursor"] = cursor
        if category_id is not None: query["category_id"] = str(category_id)
        if q is not None:           query["q"] = q
        path = "/panel-api/v1/vods" + ("?" + urlencode(query) if query else "")
        r = self._transport.request("GET", path)
        return PaginatedResponse.from_dict(r.body, Vod.from_dict)

    def vod(self, id: int) -> Vod:
        r = self._transport.request("GET", f"/panel-api/v1/vods/{id}")
        return Vod.from_dict(r.body)
