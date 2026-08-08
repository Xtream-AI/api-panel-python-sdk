
from __future__ import annotations
from typing import Any


class PanelApiException(Exception):

    def __init__(
        self,
        slug: str,
        message: str,
        request_id: str | None = None,
        details: dict[str, Any] | None = None,
        status_code: int = 0,
    ) -> None:
        super().__init__(message)
        self.slug = slug
        self.request_id = request_id
        self.details: dict[str, Any] = details or {}
        self.status_code = status_code


class BadRequestException(PanelApiException):
    pass


class AuthenticationException(PanelApiException):
    pass


class InsufficientCreditsException(PanelApiException):
    pass


class AuthorizationException(PanelApiException):
    pass


class NotFoundException(PanelApiException):
    pass


class ConflictException(PanelApiException):
    pass


class ValidationException(PanelApiException):
    @property
    def field(self) -> str | None:
        v = self.details.get("field")
        return str(v) if v is not None else None


class RateLimitException(PanelApiException):
    def __init__(
        self,
        slug: str,
        message: str,
        request_id: str | None,
        details: dict[str, Any] | None,
        status_code: int,
        retry_after: int = 60,
    ) -> None:
        super().__init__(slug, message, request_id, details, status_code)
        self.retry_after = retry_after


class ServerException(PanelApiException):
    pass


class ServiceUnavailableException(PanelApiException):
    pass


class UnknownApiException(PanelApiException):
    pass
