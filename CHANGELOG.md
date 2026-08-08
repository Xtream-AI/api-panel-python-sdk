# Changelog

All notable changes to this project are documented here.

## [1.0.0] - 2026-08-07

### Added

- Initial release.
- Full coverage of the 24 native v1 Panel API endpoints (lines, catalog, resellers, me, health).
- Typed frozen dataclasses (`Line`, `Package`, `Bouquet`, `Stream`, `Vod`, `Reseller`, `BillingSnapshot`, `Identity`, `Connection`, `RateLimitInfo`, `PaginatedResponse`).
- Typed exception hierarchy (12 classes: a base `PanelApiException` + 11 typed subclasses).
- Automatic retry with exponential backoff on 429 (honoring `Retry-After`) and 5xx.
- Automatic `Idempotency-Key` generation for writes, overrideable per call.
- Rate-limit awareness via `PanelApiClient.last_rate_limit`.
- Single runtime dependency: `requests>=2.28`.
- Unit test suite using `responses` mock library.
- Integration smoke test suite (skippable, hits a local harness).
- GitHub Actions CI matrix on Python 3.10 / 3.11 / 3.12.

[1.0.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.0.0
