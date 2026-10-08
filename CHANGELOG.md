# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Documentation

- Sub-resellers with a reseller key. Since 2026-09-25 the panel accepts two opt-in scopes on
  reseller keys: `subresellers:read` (`resellers` `list`, `get` and `billing` over the caller's
  own sub-resellers, two levels down) and `subresellers:credits` (``adjust_billing()`` becomes a transfer from
  the caller's balance). The request and response shapes are the same as with an admin key, so
  every 1.x release already supports them; the README now documents the scopes and the new slugs
  (`sub_reseller_view_not_allowed`, `sub_reseller_debit_disabled`, `debit_direct_only`,
  `duplicate_transfer`, `mismatched_mode`, `transfer_failed`) with the exception each one raises.
- Tests pin that `409 duplicate_transfer` is raised without a retry and that the new 403 slugs map
  to the authorization exception.
- `lines.connections`: panels updated on 2026-10-07 fill `content_id` and `content_name` for every
  session whose channel or VOD still exists, and report VOD sessions as `content_type: "movie"`
  (with `is_serie` for series episodes). Earlier panels returned them empty and labeled every
  session `"live"`. The response shape did not change, so no SDK change is needed; the
  `connections-populated-200.json` fixture now reflects the corrected output and a parity test
  pins it.

## [1.3.0] - 2026-09-19

### Added

- `Line` exposes `email` and `notes` (both strings, `""` when the panel has none). The panel
  returns them on every line response since 2026-09-14: `get`, `list`, `create`, `update` and
  `renew`. Admin keys read the admin contact record and reseller keys read their own reseller
  contact record. Lines created through `create()` carry a `Created via panel-api | ` prefix in
  front of the notes that were sent, which is where an integration keeps its reconciliation tag.
  Older panels that do not send the fields still parse: both default to `""`.

### Notes

- `403 insufficient_scope` responses now include `required_scope` in the error `details`
  (`AuthorizationException.details["required_scope"]`), naming the scope the key is missing.
  No SDK change was needed to read it.

## [1.2.0] - 2026-09-13

### Added

- `lines.update()`: new optional `package_id: int` argument. It is **keyword-only** and comes
  after `notes`, so every existing positional call keeps binding to the same parameters. It is
  sent only when passed (`None` omits the key from the body).
- Changing the package applies the package template to an existing line without touching its
  expiry date and without spending credits: `max_connections` and `is_restreamer` come from the
  package, and any value passed explicitly in the same call wins over the package. When
  `bouquets` is omitted the line inherits the new package's bouquets; when sent, the ids must be
  a non-empty subset of the new package's bouquets.
- The field is admin-only: a reseller key returns `403 admin_only_field`, and a trial package
  returns `422 trial_package_not_allowed`. The panel does not store the package of a line, so
  reading the line back does not report it. The package is a template applied at the moment of
  the call and `Line` has no package field, so an integrator that needs to know which package a
  line is on has to keep that mapping on its own side.

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

[1.3.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.3.0
[1.2.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.2.0
[1.1.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.1.0
[1.0.0]: https://github.com/Xtream-AI/api-panel-python-sdk/releases/tag/v1.0.0
