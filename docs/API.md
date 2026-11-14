# Database and demo API checkpoint

All application requests use the same-origin `/api/v1/` prefix. Django owns the data, authentication and business rules. Next only proxies requests and serves the supplied demo images. The real health endpoint still checks PostgreSQL.

## Open and explore

- Interactive Swagger: http://localhost:3000/api/v1/docs/
- OpenAPI JSON: http://localhost:3000/api/v1/schema/
- Ads: http://localhost:3000/api/v1/ads/
- Products: http://localhost:3000/api/v1/products/
- Shops: http://localhost:3000/api/v1/shops/
- Home data: http://localhost:3000/api/v1/home/
- Report data: http://localhost:3000/api/v1/reports/overview/
- Filter choices: http://localhost:3000/api/v1/filter-options/

Swagger JavaScript/CSS assets are bundled locally. No API subscription, provider integration, scraping or AI service is used.

## Data meaning

The fixture contains **6 shops, 8 products, 10 ads and 9 image assets**. Business records expose `source_kind=demo`, a source reference, import timestamp and null observation date when that date is unknown. Metric snapshots expose `value_kind=illustrative` and explicit USD currency. They are not verified market intelligence.

- Ad `active_days` means days active. Product/shop `active_ads_count` is a reported illustrative aggregate, rather than the count of seeded ad rows.
- Shop revenue is an estimated daily USD amount; visits are monthly. Product prices are USD. Growth units and the 30-day shop growth window are named explicitly.
- `actual_products_count` and `actual_ads_count` count related demo rows. They remain separate from reported source totals.
- Trends contain ordinal `{index,value}` points without dates. Report `period_filter_applied=false` explains why requesting 7/30/90 days does not fabricate dated observations.
- Report distributions are calculated from actual demo record counts. The original independent 62/26/12 scenario and 72% traffic-share placeholder are not presented as measured values.
- `format=video` describes the ad format; the supplied media is an image thumbnail and `video_url=null`. Crop/source dimensions are preserved.

## Catalog resources

| Method/path | Behavior |
| --- | --- |
| GET `ads/`, `products/`, `shops/` | Validated filtering, search, ordering and bounded pagination |
| GET `<kind>/<uuid>/` | Detail with bounded related previews and typed latest metric snapshot |
| GET `products/<uuid>/ads/` | Related demo ads |
| GET `shops/<uuid>/ads/`, `shops/<uuid>/products/` | Related demo records |
| GET `ads/compare/?ids=<uuid>,<uuid>` | Two or three distinct ads, preserving requested order |
| GET `<kind>/export/` | UTF-8 CSV with provenance/currency; maximum 1000 filtered records |
| GET `filter-options/` | Current category, country, platform and format choices |
| GET `home/?selection_index=0` | Prepared demo selections and actual available-record counts |
| GET `reports/overview/?focus=ads&period_days=30` | Explicitly illustrative aggregates and undated trends |
| GET `demo/entry-options/` | Three labelled mock idea examples for the later question screen |

Catalog resources are read-only. Invalid filters return 400; missing records/pages return 404. `page_size` is 1–100, default 12. Pagination links are relative, so no container-only backend address reaches the browser. Data responses use no-store headers.

Common filters: `search`, `category`, `country`, `page`, `page_size`, `source_kind=demo`.

| Kind | Additional filters | Ordering |
| --- | --- | --- |
| Ads | `platform`, `format`, `min_active_days`, `shop`, `product` | `-reach`, `-roas`, `-active_days`, `active_days` |
| Products | `max_price`, `min_active_ads`, `shop`, `one_per_shop` | `-published_on`, `-growth`, `price`, `-active_ads` |
| Shops | `min_daily_revenue`, `min_growth`, `min_active_ads` | `-growth`, `-revenue`, `-visits`, `-active_ads` |

Examples:

```text
/api/v1/ads/?platform=meta&format=video&country=DE&min_active_days=40&page_size=5
/api/v1/products/?ordering=-growth&one_per_shop=true&max_price=100
/api/v1/shops/?min_daily_revenue=3000&ordering=-growth
```

## Sessions and private workspaces

Private endpoints require a Django session. There is no automatic/shared demo account and no token in localStorage. The solar **Sign in / Sign up** button opens `/auth/login/`; `/auth/signup/` creates an email/password account that remains inactive until its email is verified. Default local delivery writes ignored email files rather than sending to an inbox:

```powershell
python scripts/read_local_email.py --recipient your-email@example.com --open
```

Open the local message and explicitly confirm at `/auth/verify#token=...`, then sign in. The fragment is removed after the confirmation attempt; it is never sent in HTTP URLs/access logs. For a legacy local admin account, the Django command is still available:

```powershell
docker compose exec backend python manage.py createsuperuser
```

Enter the password in that local terminal. PostgreSQL credentials in `.env` belong to the database role and are separate from this Django application account.

Session flow:

1. GET `auth/csrf/`; keep its cookie and the returned `csrfToken`.
2. POST `auth/login/` with your username/password and `X-CSRFToken`.
3. Login sets an HttpOnly session cookie and returns a rotated CSRF token. Use that new token for subsequent unsafe requests.
4. GET `auth/me/` reads the current identity. POST `auth/logout/` requires CSRF and clears the session.

The Swagger forms explicitly expose `X-CSRFToken` for unsafe operations. Browser requests use the same localhost hostname throughout, so session cookies are shared across the proxy. Login attempts are throttled using the development process cache; production cache/rate-limit infrastructure belongs to the production milestone.

| Method/path | Email authentication behavior |
| --- | --- |
| POST `auth/signup/` | `{email,password,display_name?}`; Django password validation, case-insensitive unique nonblank email, inactive new account |
| POST `auth/verification/resend/` | `{email}`; generic response, 60-second resend cooldown, replaces the previous link |
| POST `auth/verification/confirm/` | `{token}`; explicit action, 24-hour expiry, single use, activates account without automatic login |
| POST `auth/login/` | `{email,password}`; verified new accounts only; legacy `{username,password}` remains compatible |

Signup/resend return generic 202 `{detail,delivery_mode}` independent of whether the email exists. `delivery_mode=local` means file delivery, `smtp` means the configured SMTP backend; it does not claim account-specific delivery success. Raw verification tokens appear only in the email, while PostgreSQL stores their SHA-256 digests and destination email. Email changes invalidate an earlier destination's link. Existing username/admin accounts with blank email remain usable. New accounts use the email sign-in flow. Authentication is protected by IP, identity and global request limits; unknown/wrong/unverified sign-in failures share the same response.

| Method/path | Owned resource |
| --- | --- |
| GET/POST `workspaces/` | List/create your workspaces; owner is assigned by Django |
| GET/PATCH/DELETE `workspaces/<id>/` | Your workspace and its manually chosen name |
| GET/PATCH `workspaces/<id>/brief/` | Draft Idea/Customer/Goal fields |
| POST `workspaces/<id>/brief/complete/` | Validate minimum idea/customer/goal requirements and mark completion |
| GET `workspaces/<id>/saved/<kind>/` | Saved target references and display metadata |
| PUT/DELETE `workspaces/<id>/saved/<kind>/<target_id>/` | Idempotent typed bookmark, `<kind>` is ads/products/shops |
| GET `workspaces/<id>/watches/` | Stored watch preferences |
| PUT/DELETE `workspaces/<id>/shops/<shop_id>/watch/` | Store/disable a preference; no outbound notifications are sent |
| GET/POST `workspaces/<id>/reports/` | Validated saved report configurations |
| GET/PATCH/DELETE `workspaces/<id>/reports/<report_id>/` | Your saved definition |
| GET `workspaces/<id>/reports/<report_id>/run/` | Recompute its demo summary using validated filters |

Anonymous requests to private resources return 403. Foreign workspace/report IDs return 404. Editing a project brief invalidates its prior completion, while preserving the workspace name. Saved report filters use the corresponding catalog validator; arbitrary SQL/expression keys are rejected.

## Schema, types and regeneration

See [the actual database diagrams and all columns](DATABASE.md), [OpenAPI JSON](api/openapi.json) and [generated frontend types](../frontend/src/lib/api/generated.d.ts).

```powershell
docker compose exec -T backend python manage.py spectacular --file /tmp/nama-openapi.json --format openapi-json --validate --fail-on-warn
docker compose cp backend:/tmp/nama-openapi.json docs/api/openapi.json
npm.cmd exec --yes --package=openapi-typescript@7.13.0 --package=typescript@5.9.3 -- openapi-typescript docs/api/openapi.json --output frontend/src/lib/api/generated.d.ts
python scripts/export_database_schema.py
```

The type generator runs in an isolated pinned TypeScript 5.9.3 tool environment because its current peer range is TypeScript 5. The application retains TypeScript 6.0.2. No forced/ignored peer dependency was added to the frontend.

Pinned backend additions are drf-spectacular 0.30.0 and drf-spectacular-sidecar 2026.10.1; their complete dependency closure is in `backend/requirements.txt`.

## Checks and scope

```powershell
docker compose exec -T backend python manage.py test --verbosity 1
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend pip check
python scripts/api_smoke_check.py
python scripts/smoke_check.py
```

The checkpoint covers the existing Analyze resource fields, read operations and owned preferences, plus Idea, Customer and email authentication screens. Start actions navigate to Idea, and valid Idea submission continues to Customer. Their browser-local answers are not yet uploaded into authenticated workspaces. Reference draft keys `customer` and `budget` will map to `customer_description` and `budget_band` on that future upload. Customer form options/sample are static UI examples; there is no live market request. Goal/Home frontend pages resume after review. CSV/manual imports, password recovery, real providers, production deployment and production SMTP verification remain later work.
