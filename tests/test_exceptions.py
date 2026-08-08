from xtream_ai_panel_api.exceptions import (
    PanelApiException, BadRequestException, AuthenticationException,
    AuthorizationException, NotFoundException, ConflictException,
    ValidationException, RateLimitException, InsufficientCreditsException,
    ServerException, ServiceUnavailableException, UnknownApiException,
)


def test_base_carries_all_fields():
    class Concrete(PanelApiException): pass
    e = Concrete(slug="slug", message="msg", request_id="r-1",
                 details={"field": "x"}, status_code=422)
    assert e.slug == "slug"
    assert str(e) == "msg"
    assert e.request_id == "r-1"
    assert e.details == {"field": "x"}
    assert e.status_code == 422


def test_each_subclass_extends_base():
    for cls in [
        BadRequestException, AuthenticationException, AuthorizationException,
        NotFoundException, ConflictException, ValidationException,
        RateLimitException, InsufficientCreditsException, ServerException,
        ServiceUnavailableException, UnknownApiException,
    ]:
        assert issubclass(cls, PanelApiException)


def test_unknown_api_exception_is_stable_class():


    e1 = UnknownApiException("x", "y", "r1", {}, 418)
    e2 = UnknownApiException("x", "y", "r2", {}, 418)
    assert type(e1) is UnknownApiException
    assert type(e1) is type(e2)


def test_rate_limit_exposes_retry_after():
    e = RateLimitException(slug="rate_limited", message="x",
                            request_id="r", details={}, status_code=429,
                            retry_after=12)
    assert e.retry_after == 12


def test_validation_field_helper():
    e = ValidationException(slug="validation_error", message="bad",
                             request_id="r", details={"field": "username"},
                             status_code=422)
    assert e.field == "username"
    e2 = ValidationException(slug="x", message="y", request_id="r",
                              details={}, status_code=422)
    assert e2.field is None
