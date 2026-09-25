# Xtream AI Panel API — Python SDK

Official Python SDK for the [Xtream AI Streaming Panel API](https://xtreamai.net/docs/?page=panel-api-overview).

Full coverage of the native v1 endpoints, with typed models, typed exceptions, automatic retry (429 / 5xx), and automatic idempotency for writes.

## Requirements

- Python 3.10+
- `requests >= 2.28`

## Install

Install directly from GitHub (no PyPI publication):

```bash
pip install "git+https://github.com/Xtream-AI/api-panel-python-sdk.git@v1.3.0"
```

Or in `requirements.txt`:

```
xtream-ai-api-panel-sdk @ git+https://github.com/Xtream-AI/api-panel-python-sdk.git@v1.3.0
```

## Quickstart

```python
from xtream_ai_panel_api import PanelApiClient
from xtream_ai_panel_api.exceptions import (
    RateLimitException, InsufficientCreditsException,
)

client = PanelApiClient(
    base_url="https://panel.example.com",
    token="pk_live_...",
)

try:
    line = client.lines.create(
        package_id=42, member_id=260595, username="johndoe",
    )
    print(line.id, "expires", line.exp_date.isoformat())
except InsufficientCreditsException:
    ...
except RateLimitException as e:
    import time
    time.sleep(e.retry_after)
```

## Documentation

Full documentation lives at [xtreamai.net/docs](https://xtreamai.net/docs/?page=panel-api-sdks). The README below is a quick reference. For deep dives:

| Topic | Docs page |
|---|---|
| SDK overview and design rationale | [SDKs Overview](https://xtreamai.net/docs/?page=panel-api-sdks) |
| Install, version pinning, upgrade | [Install](https://xtreamai.net/docs/?page=panel-api-sdk-install) |
| First-line end-to-end walk-through | [Quickstart](https://xtreamai.net/docs/?page=panel-api-quickstart) |
| Constructing the client, `me()`, rotation, custom User-Agent | [Authentication with the SDK](https://xtreamai.net/docs/?page=panel-api-sdk-auth) |
| Exception hierarchy, `slug`/`request_id`/`details`, 401 vs 403 | [Errors with the SDK](https://xtreamai.net/docs/?page=panel-api-sdk-errors) |
| Retry policy, Idempotency-Key, business keys, 409 handling | [Retry and Idempotency](https://xtreamai.net/docs/?page=panel-api-sdk-retry-idempotency) |
| One-liners for every operation | [Cheat sheet](https://xtreamai.net/docs/?page=panel-api-sdk-cheatsheet) |
| Copy-paste recipes (provisioning, renewals, reconciliation) | [Common Tasks](https://xtreamai.net/docs/?page=panel-api-migration-recipes) |
| Working with resources (Lines / Catalog / Resellers) | [Lines](https://xtreamai.net/docs/?page=panel-api-lines) · [Catalog](https://xtreamai.net/docs/?page=panel-api-catalog) · [Resellers](https://xtreamai.net/docs/?page=panel-api-resellers) |
| What resellers can and cannot do | [For Resellers](https://xtreamai.net/docs/?page=panel-api-for-resellers) |
| The underlying HTTP endpoints (v1) | [XAI API Reference](https://xtreamai.net/docs/?page=xai-ref-overview) |

## Resources

- `client.lines` — `create`, `list`, `get`, `update`, `enable`, `disable`, `renew`, `reset_password`, `delete`, `connections` (`reset_password` returns the new password as a `str`, not a `Line`; `delete` returns `bool`)
- `client.catalog` — `packages`, `bouquets`, `streams`, `stream`, `vods`, `vod`
- `client.resellers` — `list`, `create`, `get`, `update`, `billing`, `adjust_billing`
- `client.me` — `get`
- `client.health()` — public probe (no auth)

`lines.update()` also accepts `bouquets` (`list[int]`) and `notes` (`str`, `""` clears them), and `lines.renew()` accepts `bouquets` — both usable with a reseller key, which on `update` is limited to those two fields and can only narrow the line's current bouquet set. These three arguments are **keyword-only** (`update(id, ..., bouquets=[...])`), so positional calls written against 1.0.0 keep binding `idempotency_key` as before. A bouquet list is capped at 512 ids by the API.

With an admin key, `lines.update()` also accepts `package_id` (`int`, keyword-only) to move a line to another package without renewing it: `client.lines.update(172504295, package_id=7)`. The package's `max_connections` and `is_restreamer` are applied, anything passed explicitly in the same call wins over the package, and omitting `bouquets` inherits the new package's bouquets. The expiry date is untouched and no credits are spent. A reseller key gets `403 admin_only_field`, a trial package `422 trial_package_not_allowed`. The panel does not store a line's package (`Line` has no package field): the package is a template applied at the moment of the call, so an integrator that needs to know which package a line is on has to keep that mapping on its own side.

### Sub-resellers with a reseller key

The same `resellers` methods work with a **reseller** key when the key carries the opt-in scopes, with no SDK change needed (any 1.x release works):

- `subresellers:read` enables `list`, `get` and `billing`. The key sees its own sub-resellers and their sub-resellers (two levels down, the same accounts the panel shows under **Resellers Network**), never itself, its parent, its siblings or an administrator account. An ID outside that tree raises `NotFoundException`, exactly like an ID that does not exist. The reseller's member group needs **Can Create Subresellers**, otherwise every call raises `AuthorizationException` with slug `sub_reseller_view_not_allowed`.
- `subresellers:credits` turns `adjust_billing()` into a **transfer** from the caller's own balance: a positive `delta` moves credits from the caller to the sub-reseller, and a negative `delta` takes them back. Taking credits back needs the panel's **Reseller credit debit** setting and works only on direct sub-resellers. Both accounts must be in credits mode.

```python
import os
reseller = PanelApiClient(base_url="https://panel.example.com", token=os.environ["RESELLER_KEY"])

for sub in reseller.resellers.list().items:
    print(sub.username, sub.billing.credits if sub.billing else None)

after = reseller.resellers.adjust_billing(262260, delta=25, reason="WHMCS invoice #1042")
```

| Slug | Exception | Meaning |
|---|---|---|
| `insufficient_credits` (402) | `InsufficientCreditsException` | The caller does not have enough credits to transfer. |
| `negative_balance_not_allowed` (422) | `ValidationException` | A negative `delta` larger than the sub-reseller's balance. |
| `mismatched_mode` (422) | `ValidationException` | The caller or the sub-reseller is in users (slots) mode. |
| `sub_reseller_debit_disabled` (403) | `AuthorizationException` | Negative `delta` while the panel's Reseller credit debit setting is off. |
| `debit_direct_only` (403) | `AuthorizationException` | Negative `delta` on a sub-reseller that is not a direct child. |
| `duplicate_transfer` (409) | `ConflictException` | The same transfer (same sub-reseller and amount) within 5 seconds. Not retried by the SDK. |
| `transfer_failed` (500) | `ServerException` | Nothing was moved. The SDK retries it with the same `Idempotency-Key`. |

With an admin key `adjust_billing()` keeps its original meaning: an adjustment that does not debit anyone. `list` and `get` do not return `owner_id`, so `Reseller.owner_id` is `null` on those calls; it is filled on the responses of `create` and `update`.

## Pagination

`list()` methods return `PaginatedResponse[T]` with `.items` and `.next_cursor`. The SDK does **not** loop automatically — you drive it:

```python
page = client.lines.list(limit=100)
for line in page.items:
    handle(line)

while page.next_cursor is not None:
    page = client.lines.list(cursor=page.next_cursor, limit=100)
    for line in page.items:
        handle(line)
```

`next_cursor` is an opaque string — always pass it back verbatim.

## Idempotency

Every mutating call auto-generates a UUID v4 and sends it as `Idempotency-Key`. Retries triggered by the SDK reuse the same key.

For webhook handlers, derive the key from a business ID so a re-fired webhook is a no-op:

```python
client.lines.create(
    package_id=42, member_id=260595, username="johndoe",
    idempotency_key=f"invoice-{invoice_id}",
)
```

## Retry policy

- 5xx (500-599) → exponential backoff, up to 3 retries.
- 429 → honor Retry-After header (capped 60s), up to 3 retries.
- 4xx (not 429) → never retried.
- Network errors → retried like 5xx.

Configurable:

```python
client = PanelApiClient(
    base_url="...", token="...",
    timeout=30.0,       # seconds
    max_retries=3,
)
```

## Exception hierarchy

All exceptions extend `xtream_ai_panel_api.exceptions.PanelApiException`.

| Class | HTTP | Triggers (common slugs) |
|---|---|---|
| `BadRequestException`           | 400 | `invalid_body`, `missing_idempotency_key` |
| `AuthenticationException`       | 401 | `invalid_key`, `caller_disabled` |
| `InsufficientCreditsException`  | 402 & 422 | `insufficient_credits`, `billing_expired`, `insufficient_slots` |
| `AuthorizationException`        | 403 | `insufficient_scope`, `admin_only_endpoint`, `admin_only_field`, `owner_must_be_self`, `delete_not_allowed`, `password_change_not_allowed`, `sub_reseller_creation_not_allowed`, `sub_reseller_view_not_allowed`, `sub_reseller_debit_disabled`, `debit_direct_only` |
| `NotFoundException`             | 404 | `not_found`, `caller_not_found` |
| `ConflictException`             | 409 | `idempotency_conflict`, `duplicate_transfer` (in_flight is retried transparently) |
| `ValidationException`           | 422 | `validation_error` + many domain-specific slugs (`cap_below_active_users`, `negative_balance_not_allowed`, `no_sub_reseller_setup`, `owner_id_required`, `line_has_no_expiry`, `renew_with_trial_package_not_allowed`, `mismatched_mode`, …). Use `.field` for the failing field name. |
| `RateLimitException`            | 429 | `rate_limited` (`.retry_after` in seconds) |
| `ServerException`               | 5xx | `internal_error`, `delete_failed`, `transfer_failed`, `network_error` |
| `ServiceUnavailableException`   | 503 | `api_disabled`, `service_unavailable` |
| `UnknownApiException`           | other | fallback for status codes the SDK doesn't recognize |

All exceptions carry `.slug`, `str(exception)`, `.request_id`, `.details`, `.status_code`.

**Note on `insufficient_slots`:** the server emits this with HTTP 422 (not 402), but it's semantically the users-mode analog of `insufficient_credits`. The SDK special-cases it and raises `InsufficientCreditsException` — one `except InsufficientCreditsException` block handles both billing modes.

## Rate limit awareness

Every request captures `X-RateLimit-*` headers — including on 4xx errors:

```python
info = client.last_rate_limit
if info is not None and info.remaining < 10:
    time.sleep(0.5)
```

## Thread safety

`PanelApiClient` is **not thread-safe**. It holds a `requests.Session` (which the `requests` project explicitly documents as not safe across threads) and a mutable `last_rate_limit` attribute. In a Django/Flask billing webhook handler with a shared module-level client and threaded WSGI workers, concurrent calls will interleave connection-pool state and stomp `last_rate_limit`.

Options:

- One `PanelApiClient` per thread / per worker (simplest and recommended).
- Or wrap access with your own `threading.Lock` and treat the client as a shared resource.

Async (asyncio / aiohttp) is out of scope for v1 — use a synchronous thread pool for now, or wait for the async client planned for v1.1.

## Testing

```bash
pip install -e '.[test]'
pytest tests -v
```

The `tests/integration/` suite hits a live harness at `HARNESS_URL` (default `http://127.0.0.1:9955`) with `HARNESS_TOKEN`. Skipped when neither is available.

## License

MIT — see [LICENSE](LICENSE).

## Not covered

The `/panel-api/xc/*` and `/panel-api/onestream/*` compatibility dialects are **not** in this SDK. Migrations from those panels reuse their existing SDK and only change the base URL. See: [XC compat](https://xtreamai.net/docs/?page=panel-api-xtream-codes-compatibility) — [OneStream compat](https://xtreamai.net/docs/?page=panel-api-onestream-compatibility).
