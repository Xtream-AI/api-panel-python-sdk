from __future__ import annotations

from xtream_ai_panel_api.transport import HttpTransport
from xtream_ai_panel_api.models import Identity


class MeResource:
    def __init__(self, transport: HttpTransport) -> None:
        self._transport = transport

    def get(self) -> Identity:
        r = self._transport.request("GET", "/panel-api/v1/me")
        return Identity.from_dict(r.body)
