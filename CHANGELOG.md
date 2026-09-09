# Changelog

All notable changes to this project are documented here.

## [1.1.0] - 2026-09-09

### Added

- `lines.update()`: new optional `bouquets: list[int]` and `notes: str` arguments. They are
  **keyword-only** and come after `idempotency_key`, so every existing positional call keeps
  binding to the same parameters. Both are sent only when passed (`None` omits the key from the
  body). `notes=""` clears the stored notes.
- `lines.renew()`: new optional **keyword-only** `bouquets: list[int]` argument, after
  `idempotency_key` — `renew(id, package_id, "idem-1")` still means `idempotency_key="idem-1"`.
  When omitted, the line keeps its current bouquets; when sent, the ids must be a non-empty subset
  of the target package's bouquets (at most 512 ids).

### Changed

- `POST /lines/{id}/update` is no longer admin-only on the API side: a reseller key may now send
  `notes` and `bouquets` (its `bouquets` must be a non-empty subset of the line's current set —
  it can only remove). Any admin-only field in the body still returns `403 admin_only_field`.
- Documentation: `lines.create()` without `bouquets` (or with an empty list) inherits the
  package's bouquets — this was a server-side bug fix, no SDK signature change.

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

[1.1.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.1.0
[1.0.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.0.0
