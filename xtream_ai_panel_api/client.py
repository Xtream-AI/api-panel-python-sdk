from __future__ import annotations
from typing import Any, Callable

import requests

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.models import RateLimitInfo
from xtream_ai_panel_api.resources.lines import LinesResource
from xtream_ai_panel_api.resources.catalog import CatalogResource
from xtream_ai_panel_api.resources.resellers import ResellersResource
from xtream_ai_panel_api.resources.me import MeResource


class PanelApiClient:

    def __init__(
        self,
        base_url: str,
        token: str,
        timeout: float = 30.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
        sleeper: Callable[[float], None] | None = None,
    ) -> None:
        self._transport = HttpTransport(
            base_url=base_url, token=token,
            timeout=timeout, max_retries=max_retries,
            session=session, sleeper=sleeper,
        )
        self.lines     = LinesResource(self._transport)
        self.catalog   = CatalogResource(self._transport)
        self.resellers = ResellersResource(self._transport)
        self.me        = MeResource(self._transport)

    @property
    def last_rate_limit(self) -> RateLimitInfo | None:
        return self._transport.last_rate_limit

    def health(self) -> dict[str, Any]:
        r = self._transport.request("GET", "/panel-api/v1/health")
        return r.body
