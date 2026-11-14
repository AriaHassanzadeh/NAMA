# NAMA Analyze status

## Customer page review checkpoint — 2026-11-14

The user approved continuing after Idea. Following the agreed page-by-page review, this checkpoint implements Customer only. Branch: `work/frontend-customer`, based on the preserved Idea/auth checkpoint. Existing personal `.vscode/` settings remain untracked and untouched.

- Start at http://localhost:3000/start/idea and submit a valid idea to enter http://localhost:3000/start/customer.
- Direct Customer access waits for browser draft recovery, then returns to Idea if its answer is incomplete. Valid stored drafts survive reload; another tab invalidating Idea also returns Customer to Idea without deleting its answers.
- Customer follows the reference title, description, audience cards, optional market/budget fields, shared NAMA logo/fonts, RTL and dark/light entry themes. Mobile uses normal vertical scrolling with no overlapping composer or horizontal page overflow.
- Choose consumer/business/both or describe the customer with at least three trimmed characters. Cards expose selection state and support native keyboard activation; selecting a chosen card again clears it. Description maximum is 2000; optional market maximum is 100. Budget options and the clearly illustrative example match the reference.
- Every edit persists immediately and invalidates the saved acknowledgement/local completion. Enter saves Customer; Shift+Enter adds a newline; IME Enter does not submit. Reload, progress/back navigation, source/theme preferences and manual workspace-name fields are preserved. Blocked storage uses the existing clearly labelled in-memory fallback.
- Customer submit acknowledges saved answers and stays on Customer for review. Goal remains disabled; the complete project flow and Home are not claimed finished. Drafts remain browser-local, with no answer text in URLs. Existing Django auth and demo APIs continue to work.

### Files changed

- `frontend/src/app/start/customer/page.tsx`, `components/entry/customer-discovery.tsx`: real Customer route and form.
- `components/entry/discovery-header.tsx`, `draft-validation.ts`: shared step navigation/theme controls and bounded form validation/options. `entry-store.ts` exposes hydration readiness so the route guard does not mistake the server's empty snapshot for a missing draft.
- `components/entry/idea-discovery.tsx`: valid Idea submission now saves and navigates to Customer; edits invalidate Customer's saved acknowledgement while retaining its values. `idea-discovery.css` shares the entry layout and adds responsive Customer cards/fields.
- `scripts/customer_check.mjs`, `scripts/idea_check.mjs`: actual Chrome behavior checks for the new page and changed continuation. `README.md`, `docs/API.md`, this status entry: current routes, local draft mapping and scope.

No dependency installation, API contract or database migration was needed. Customer options are static form choices; Idea still uses the labelled mock example API. Future authenticated upload maps reference keys `customer` and `budget` to Django's existing `customer_description` and `budget_band`.

### Checks that passed

| Exact command/check | Actual result |
| --- | --- |
| `docker compose run --rm --no-deps frontend npm run lint` | Zero warnings/errors |
| `docker compose run --rm --no-deps frontend npm run typecheck` | Passed |
| `docker compose run --rm --no-deps frontend npm run build` | Passed; `/start/customer` generated alongside existing routes |
| `docker compose build frontend` | Current frontend image built using cached locked dependencies |
| `docker compose up -d --no-deps --wait frontend` | Frontend healthy; backend/database and persistent volume retained |
| `npm.cmd --prefix frontend run typecheck` | Local editor route types regenerated; TypeScript passed |
| `node scripts/customer_check.mjs` with `REFERENCE_ORIGIN=http://127.0.0.1:8766` | Guards, audience/text alternatives, example focus, keyboard/IME, optional fields, saved-state invalidation, reload/history/progress, manual-name preservation, real second-tab invalidation, malformed/blocked storage and reduced motion passed; no uncaught browser exceptions |
| Customer viewports | Both themes at 1440x1000, 1280x900, 768x1024, 390x844 and 844x390; aligned RTL content, loaded fonts, no horizontal overflow or overlapping form sections |
| `node scripts/idea_check.mjs` | Existing mock API/loading/error/retry/empty, validation, keyboard, persistence and layout cases passed with actual Customer continuation and return navigation |
| `python scripts/smoke_check.py` | Direct/proxied real-database health and solar HTML/RTL/logo passed |
| `git diff --check` | Passed |

Rendered desktop/mobile Customer screenshots were visually compared with the supplied readable reference, including the scrolled mobile composer. Dark and light layouts were inspected. Artifacts outside Git: `C:\Users\Admin\AppData\Local\Temp\nama-analyze-customer-BlzG1U` and `C:\Users\Admin\AppData\Local\Temp\nama-analyze-idea-xu1TEe`. The reference was served temporarily for inspection only. No new UI/runtime blocker remains.

**Next action:** user reviews Idea → Customer, saves/edits answers and checks mobile behavior. Implement Goal only after that review; authenticated project-brief upload and Home remain later parts of the entry milestone.

## Idea, email authentication and local restart — 2026-11-14

The user approved resuming the frontend, then expanded this checkpoint to include a solar **Sign in / Sign up** button, login, signup and email verification. They selected email/password with a verification email. Work began on November 12; an automatic approval-service usage-limit failure prevented the final migration/check command from executing then. On November 14 the user requested another project run; Docker Desktop was stopped, so it was started in the background and the current stack was rebuilt and brought up successfully. This entry supersedes the older pending-frontend notes below.

- Branch: `work/frontend-idea`, based on the preserved `work/database-demo-api` checkpoint.
- Solar entrance: http://localhost:3000/
- Idea review page: http://localhost:3000/start/idea
- Sign in: http://localhost:3000/auth/login/
- Sign up: http://localhost:3000/auth/signup/
- Email confirmation/resend: http://localhost:3000/auth/verify/
- Health: http://localhost:3000/health/; API explorer: http://localhost:3000/api/v1/docs/
- Frontend, backend and PostgreSQL are healthy. PostgreSQL remains on `127.0.0.1:5433` with its existing named volume. Personal `.vscode/`, local environments, credentials and reference sources were preserved.

### Completed UI and API behavior

- `frontend/src/app/start/`, `components/entry/idea-discovery.tsx` and its CSS implement only the Idea question using the supplied readable reference: shared NAMA mark/fonts, dark default, light theme, RTL, three-step progress, API example chips and a bottom composer in normal document flow.
- `components/entry/entry-store.ts` extracts the existing `nama-analyze-entry-v1` store without dropping unknown fields. Theme, motion preference and media source survive navigation. Idea saves while typing, restores after reload/back/forward, validates a trimmed minimum of 5 characters and a maximum of 2000, supports Enter/Shift+Enter and respects IME composition. Editing invalidates the saved acknowledgement and prior local completion. Unavailable storage falls back to memory and clearly explains that a reload cannot restore it.
- Solar/media Start actions now navigate to `/start/idea`. A valid Idea submission saves the draft and announces success; Customer/Goal progress controls remain disabled. No nonexistent Customer/Home route or completed project brief is presented.
- `components/query-provider.tsx`, `lib/api/entry-options.ts` connect the example chips to the existing same-origin demo endpoint with runtime validation and explicit loading/error/retry/empty states. Free entry remains usable when the examples fail. Answers are not placed in URLs or uploaded to private workspaces at this checkpoint.
- `frontend/src/app/auth/`, `components/auth/`, `lib/api/auth.ts` implement the requested matching logo/theme for login, signup, password visibility, confirmation validation, pending email state, explicit email confirmation, resend, signed-in account state and logout. Login success enters the existing Idea page. Unsafe calls fetch a CSRF token first and use Django HttpOnly sessions; passwords and verification tokens are absent from localStorage.
- `backend/accounts/models.py`, `api.py`, `verification.py`, `tests.py`, migration `0002_emailverification_user_email_verification_required_and_more.py`: email/password signup, Django password validation, case-insensitive unique nonblank emails, inactive/unverified new users and compatible legacy username/admin users. A shared normalized lookup also supports preserved legacy emails with surrounding spaces without rewriting those rows.
- Verification tokens use 32 random bytes, store only a SHA-256 digest bound to the recipient email, expire after 24 hours and work once. Resend serializes per user, has a 60-second cooldown and invalidates an older link. Opening the link does not activate an account; an explicit CSRF-protected POST does. Confirmation does not automatically log in. Signup/resend give generic responses and authentication has IP, identity and global limits. Development throttles use process-local cache; production shared-cache/rate-limit work is deferred.
- The additive migration checks duplicate normalized emails before changing schema. It applied successfully at startup; no existing account, user import or persistent volume was removed. Actual database metadata now contains 30 physical tables, including `accounts_emailverification`; the three ERDs and all application columns/constraints were refreshed.
- `backend/config/api_schema.py`, `docs/api/openapi.json`, `frontend/src/lib/api/generated.d.ts` document 34 API paths, including email auth and CSRF. `scripts/export_database_schema.py` includes the new verification table in the actual schema documentation.
- `compose.yaml`, `.env.example`, backend email settings, `.gitignore`, `backend/.dockerignore` configure file email for local development and environment-based SMTP later. No real SMTP credentials or external email subscription were added. `scripts/read_local_email.py` opens the newest matching local message; private links are only printed with an explicit `--json` flag for automation.
- `scripts/auth_check.mjs`, `scripts/idea_check.mjs`, updated `scripts/landing_check.mjs`, `README.md`, `docs/API.md` provide actual behavior checks and current local instructions.

New pinned UI dependencies: React Hook Form 7.92.0, resolvers 7.0.6, Zod 4.6.7, TanStack Query 5.107.1 and Lucide React 1.72.0. Stable versions/React peer ranges were checked against the official npm registry and [form](https://react-hook-form.com/get-started), [query](https://tanstack.com/query/latest/docs/framework/react/installation), [Zod](https://zod.dev/) and [Lucide](https://lucide.dev/guide/packages/lucide-react) documentation. Django's [password validation](https://docs.djangoproject.com/en/5.2/topics/auth/passwords/), [file email backend](https://docs.djangoproject.com/en/5.2/topics/email/#file-backend) and [database constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/#uniqueconstraint) were checked for the auth implementation. Existing framework/runtime pins remain unchanged.

### Actual verification results

| Exact command/check | Result |
| --- | --- |
| `docker compose config --quiet` | Valid configuration, without printing resolved secrets |
| `docker compose up -d --build --wait` | Both current images built; all three services healthy; pending additive auth migration applied at startup |
| `docker compose build` then `docker compose up -d --wait` | Final verified source packaged into both images and restarted healthy |
| `docker compose exec -T backend python manage.py migrate --noinput` | Final repeat found no pending migrations |
| `docker compose exec -T backend python manage.py check` | No issues |
| `docker compose exec -T backend python manage.py test --verbosity 1` | Final run: all 50 tests passed against PostgreSQL; temporary test database removed |
| `docker compose exec -T backend python manage.py makemigrations --check --dry-run` | No model drift |
| `docker compose exec -T backend python manage.py spectacular --file /tmp/nama-openapi.json --format openapi-json --validate --fail-on-warn` | Zero schema warnings/errors; 34 paths; copied to `docs/api/openapi.json` |
| `npm.cmd exec --yes --package=openapi-typescript@7.13.0 --package=typescript@5.9.3 -- openapi-typescript docs/api/openapi.json --output frontend/src/lib/api/generated.d.ts` | Generated updated frontend types in the isolated compatible tool environment |
| `docker compose run --rm --no-deps frontend npm run lint` | Zero warnings/errors |
| `docker compose run --rm --no-deps frontend npm run typecheck` | Passed after correcting the auth mutation's union response inference |
| `npm.cmd --prefix frontend run typecheck` | Local editor route declarations regenerated and TypeScript passed |
| `docker compose run --rm --no-deps frontend npm run build` | Passed; solar, health, Idea and all three auth routes generated |
| `docker compose run --rm --no-deps frontend npm audit` | Zero reported vulnerabilities |
| `node scripts/auth_check.mjs` | Real signup/local verification/verified login, replay rejection, missing-link recovery, disabled pending submit, password confirmation/toggle, rate/network recovery, keyboard login, session HttpOnly/CSRF and no credentials in localStorage passed |
| `node scripts/landing_check.mjs` | All original motion/theme/keyboard/layout checks plus real Idea navigation passed |
| `node scripts/idea_check.mjs` | Draft/example/validation/Enter/Shift+Enter/IME/reload/back/forward/error/retry/empty/blocked-storage cases passed; both themes at 1440x1000, 1280x900, 768x1024, 390x844 and 844x390 |
| `python scripts/smoke_check.py` | Direct/proxied database health and solar HTML/RTL/logo passed |
| `python scripts/api_smoke_check.py` | Existing 6/8/10 demo catalog, media/export, reports/Home/options, ownership rejection, 34-path schema and bundled Swagger assets passed |
| `python scripts/export_database_schema.py` | 30 actual PostgreSQL tables and three ERDs exported, including all verification columns/constraints |
| `git diff --check` | Passed |

Auth was visually inspected in dark/light desktop/mobile screenshots. Idea was compared with the actual readable reference at desktop/mobile sizes. Its light labels were darkened for readable contrast, and composer tools/send placement was corrected to match the reference. A Chrome/CDP `captureBeyondViewport` artifact initially showed an offset/crop despite correct DOM bounds; viewport-only captures and explicit root/center bounds checks confirmed the correct rendered layout. The browser harness was also corrected to await the current mounted form and distinct failure responses instead of reading a prior route during navigation. No remaining browser exception was observed.

Final browser artifacts (outside Git): `C:\Users\Admin\AppData\Local\Temp\nama-analyze-auth-KQBRZW`, `nama-analyze-landing-N1XgeC`, `nama-analyze-idea-wALnVU`. Earlier reference-comparison artifacts: `C:\Users\Admin\AppData\Local\Temp\nama-analyze-idea-8RfwKB`.

### Local verification mail and next review

Default delivery is **local file email**, not a real inbox. After signup, run `python scripts/read_local_email.py --recipient your-email@example.com --open`, click **تأیید ایمیل**, then sign in. The UI explicitly labels local delivery. SMTP settings are documented but real inbox delivery has not been configured or tested. Local browser checks leave isolated `example.test` accounts for inspection; no shared demo credentials were created.

No remaining local startup/auth/Idea check blocker. Password recovery, authenticated project-brief upload, Customer/Goal/Home UI and production delivery remain separate work. **Next action:** user reviews solar → Idea and solar → sign-in/signup/verification before the next Customer page. Do not implement the remaining frontend pages without that review.

## Database and demo API review checkpoint — 2026-11-12

The user approved continuing after the landing, then explicitly requested the database and APIs across the Analyze pages before further frontend implementation. This supersedes the earlier page-order checkpoint below. The next Idea page has not been implemented. Explanations are in English at the user's request; the application remains Persian RTL.

- Branch: `work/database-demo-api`, including the preserved landing work and the merge of `origin/main` after the user's PR #1 merge.
- Git delivery: `git push --set-upstream origin work/database-demo-api` passed. Local and remote checkpoint commit were both verified as `48930908ae085e694e51c0d1df40a7db5d11c5db`; only personal `.vscode/` remained untracked. This status delivery note is a subsequent documentation commit.
- Application: http://localhost:3000/ — solar entrance remains available.
- Interactive API explorer: http://localhost:3000/api/v1/docs/
- OpenAPI: http://localhost:3000/api/v1/schema/
- Actual PostgreSQL columns, constraints and three relationship diagrams: [DATABASE.md](DATABASE.md). Complete metadata covers 29 physical tables, including Django framework tables; no business rows or credentials are exported.
- Endpoint behavior, filters, units and session testing: [API.md](API.md).
- Desktop pgAdmin connection remains **NAMA Analyze (Docker local)** at `127.0.0.1:5433`. Refresh its `nama_analyze > Schemas > public > Tables` node to see the new tables. The existing PostgreSQL 18 server and the persistent project volume were preserved.

### Implemented files and behavior

- `backend/market/`: catalog models, initial migration, admin registration, original-reference fixture, idempotent `seed_demo`, validated read-only APIs, serializers, filters and behavior tests. The migrated database contains 6 demo shops, 8 products, 10 ads and 9 media definitions. Repeating the seed preserves IDs and unrelated manual records/snapshots; collisions roll back.
- Shop → Product → Ad foreign keys preserve the supplied relationships; an ad derives its shop through its product. Categories, countries, tags and media are normalized. Metric snapshots retain provenance, illustrative value kind, explicit USD units and nullable observation dates. Reported source totals remain separate from actual related-record counts.
- Public APIs cover list/detail/search/filter/order/pagination, related ads/products, ad comparison, CSV export, Home selections, filter options and report summaries. Undated trends retain ordinal indices; reports explicitly return `period_filter_applied=false`. Data is labelled demo, not live or verified market information. Relative pagination links and same-origin image paths were checked.
- `backend/workspaces/`: owned workspace/project-brief models, typed saved ads/products/shops, shop-watch preferences and saved report definitions, migration, APIs and ownership tests. Foreign workspace/report IDs return 404. Brief edits invalidate prior completion. Report filters use the catalog validators. Watches store preferences only.
- `backend/accounts/api.py`, `tests.py`: session login/logout/current-user/CSRF endpoints, protected unsafe requests, login throttling and tests. There is no seeded/shared account or authentication UI. `API.md` explains local `createsuperuser` and the CSRF token rotation flow.
- `backend/demo/`: three explicitly labelled mock idea examples for the later entry form; no new frontend page was introduced.
- `backend/config/`, `backend/requirements.txt`: registered apps/routes, drf-spectacular 0.30.0 and sidecar 2026.10.1 with a pinned dependency closure, local Swagger assets, explicit API contracts and CSRF header documentation. The validated schema has 31 paths.
- `docs/api/openapi.json`, `frontend/src/lib/api/generated.d.ts`: validated schema and generated frontend types. The generator uses an isolated pinned TypeScript 5.9.3 tool environment because its peer range excludes the application's TypeScript 6.0.2; the app version is unchanged.
- `frontend/next.config.mjs`: an explicit static-file rewrite before the API rewrite makes locally bundled Swagger assets work through port 3000. `frontend/public/demo-assets/` contains copies of the supplied image assets; references remain unchanged.
- `backend/market/management/commands/export_database_schema.py`, `scripts/export_database_schema.py`, `docs/database/`, `docs/DATABASE.md`: actual PostgreSQL introspection and reproducible catalog, metrics and workspace ERDs with all application columns and constraints.
- `scripts/api_smoke_check.py`, `README.md`, `docs/API.md`, this status entry: tested local URLs, setup/check commands, editor instructions and scope. Frontend package formatting and npm lockfile placement metadata were retained; direct dependency versions are unchanged.

### Editor import issue resolved

Docker already contained Django and DRF. VS Code was using the host Python without those dependencies. Created ignored `backend/.venv` with the existing Windows Python 3.14, installed the pinned requirements and verified every import the user reported, including `AbstractUser`, `SimpleRateThrottle`, `APIView`, Django test utilities and `APIClient`. Django was initialized for imports that require configured settings. An initial standalone import probe without Django settings failed with `ImproperlyConfigured`; the initialized probe passed. Docker Python 3.13 remains the application runtime.

Existing personal `.vscode/settings.json` was preserved, adding only missing Python interpreter/backend-analysis-path settings. `.vscode/` and `.venv/` are not committed. If Pylance retains old errors, select `backend/.venv/Scripts/python.exe` using **Python: Select Interpreter**, then **Developer: Reload Window**. No source-import backslashes or Python syntax error were found in the actual backend files.

### Checks that passed

| Exact command/check | Actual result |
| --- | --- |
| `docker compose exec -T backend python manage.py makemigrations market workspaces --no-header` | Generated the two committed initial application migrations |
| `docker compose exec -T backend python manage.py migrate --noinput` | Both migrations applied; subsequent check found no pending migrations |
| `docker compose exec -T backend python manage.py seed_demo` | Repeatable 6 shops / 8 products / 10 ads / 9 media assets |
| `docker compose exec -T backend python manage.py check` | No issues |
| `docker compose exec -T backend python manage.py test --verbosity 1` | Final run: all 36 tests passed against PostgreSQL; temporary test database removed |
| `docker compose exec -T backend python manage.py makemigrations --check --dry-run` | No model drift |
| `docker compose exec -T backend pip check` | No broken requirements |
| `docker compose exec -T backend python manage.py spectacular --file /tmp/nama-openapi.json --format openapi-json --validate --fail-on-warn` | Validated schema with zero warnings/errors; 31 paths |
| `npm.cmd exec --yes --package=openapi-typescript@7.13.0 --package=typescript@5.9.3 -- openapi-typescript docs/api/openapi.json --output frontend/src/lib/api/generated.d.ts` | Generated the frontend contract types |
| `python scripts/export_database_schema.py` | Exported 29 actual PostgreSQL tables and three ERDs |
| `docker compose build` | Both updated images built with locked dependencies |
| `docker compose up -d --wait` | Frontend, backend and database healthy |
| `python scripts/api_smoke_check.py` | Same-origin catalog list/detail/CSV/provenance, image, Home/options/report APIs, anonymous private-resource rejection, schema/CSRF documentation and local Swagger assets passed |
| `python scripts/smoke_check.py` | Direct/proxied real-database health plus landing HTML/RTL/logo passed |
| `docker compose run --rm --no-deps frontend npm run lint` | Zero warnings/errors |
| `docker compose run --rm --no-deps frontend npm run typecheck` | Passed, including generated API types |
| `docker compose run --rm --no-deps frontend npm run build` | Passed; existing `/` and `/health` routes generated |
| `docker compose run --rm --no-deps frontend npm audit` | Zero reported vulnerabilities |
| `backend/.venv/Scripts/python.exe -m pip check` and initialized local import probe | No broken requirements; all reported Django/DRF imports resolved |
| `git diff --check` | Passed |

The final regression run caught an old test expectation containing an extra image subdirectory after the served asset paths were flattened. Corrected the expectation to the actual path already verified over HTTP, then all 36 tests passed. Swagger static assets initially returned 404 through the generic slash rewrite; the explicit static-file rewrite fixed that integration and the final smoke check passed.

### Limits and next action

The repository ERDs and column/constraint lists are complete. Optional FigJam generation did not create a file because its tool required a team/organization selection in the widget; no paid plan or subscription was selected. The local/GitHub Mermaid diagrams are available without that external step.

No new UI page was added or visually reviewed in this backend checkpoint. CSV/manual imports, real providers, production deployment and authentication screens remain later work. Login throttling currently uses the development process cache. The previously documented ESLint deprecation/override limitation remains. A proposed manifest cleanup using `git restore` was rejected by automatic approval review because it could discard uncommitted changes; the files were preserved and the tested versions retained. No database flush, volume removal, force push or public deployment occurred.

**Next action:** user reviews the database diagrams/columns and demo APIs, then resumes the Idea frontend page. Continue one page at a time and request review after each completed page; do not build the remaining frontend pages before that review.

## Milestone 02 — solar landing review checkpoint — 2026-11-11

The user subsequently authorized frontend implementation page by page, with a review after each page. Only the solar entrance has been added for this checkpoint. Milestone 02 is in progress; do not implement Idea, Customer, Goal or Home before the user reviews this page.

- Landing: http://localhost:3000/
- Existing connection-status screen moved to http://localhost:3000/health/; both health API URLs are unchanged.
- pgAdmin was independently rechecked: exactly one **NAMA Analyze (Docker local)** entry exists at 127.0.0.1:5433, database `nama_analyze`, user `nama`; the existing PostgreSQL 18 server entry is intact. Refresh **Servers**, then expand **NAMA Analyze (Docker local) > Databases > nama_analyze > Schemas > public > Tables**.
- The foundation was pushed successfully: `git push --set-upstream origin work/milestone01`; local and remote commit both verified as `1364003c228fd0ff29c27546b75b3cffd80e0d2c`.
- This frontend review checkpoint uses branch `work/milestone02-landing`.

### Page changes

- `frontend/src/app/page.tsx` now renders a real React solar entrance; the original diagnostic React page is preserved at `frontend/src/app/health/page.tsx`.
- `frontend/src/components/entry/solar-entrance.tsx` and its scoped CSS reproduce the restrained flat orbital reference: three circular tracks, ten upright media marks, deterministic faint stars, the supplied red logo and local Anton/Vazirmatn/Be Vietnam fonts.
- Theme and pause preferences persist in the entry store, separately from future workspace theme preferences. Hover/focus pauses movement; reduced-motion preferences stop all animations and disable the motion button. Theme, motion and media selection support keyboard use.
- Start/media actions currently save the chosen entry source locally and announce the selection. Navigation to the Idea screen is intentionally not wired until that next page is built after this review; no unimplemented route or fake completed project brief is introduced.
- `frontend/src/app/layout.tsx` loads the supplied additional fonts locally; reference files remain unchanged.
- `scripts/browser_check.mjs` now checks `/health/`; `scripts/landing_check.mjs` adds actual Chrome interaction/layout checks. `README.md` documents both routes and checks.

### Checks that passed for this checkpoint

| Exact command/check | Actual result |
| --- | --- |
| `docker compose run --rm --no-deps frontend npm run lint` | Zero warnings/errors |
| `docker compose run --rm --no-deps frontend npm run typecheck` | Route generation and TypeScript passed |
| `docker compose run --rm --no-deps frontend npm run build` | Production build passed; routes `/` and `/health` generated |
| `docker compose build frontend` | Updated frontend image built using existing locked dependencies |
| `docker compose up -d --no-deps --wait frontend` | Frontend healthy; backend/database retained |
| `node scripts/landing_check.mjs` | All interaction, storage, motion and viewport checks passed |
| Viewports | 1440x1000, 1280x900, 768x1024, 390x844 and 844x390; fonts loaded, no page overflow, footer hint centered and visible |
| Interactions | Pause/reload/resume; hover/focus pause; keyboard media selection; start confirmation without changing URL; both themes and reload persistence; reduced motion; no uncaught browser exceptions |
| `node scripts/browser_check.mjs` | Relocated health screen still passes pending/ready/error/keyboard retry checks |
| `python scripts/smoke_check.py` | Landing HTML/RTL/logo and direct/proxied database health still pass |

Desktop, mobile and light screenshots were visually inspected against the readable solar reference. Review caught and fixed an RTL/logical-position centering issue in the footer; the final check explicitly verifies its centering at every viewport. Final artifacts: `C:\Users\Admin\AppData\Local\Temp\nama-analyze-landing-J8pA00` (outside Git).

Windows/Next initially retained the old route/CSS after file moves; restarting/recreating only the frontend loaded the current source. README records the restart command for newly added routes. An automatic permission review timed out before one write and one browser check executed; smaller workspace edits and one inspected-script retry completed the work. No remaining page-0 runtime blocker.

**Next action:** user reviews the solar entrance at `/`. Wait for that feedback before implementing `/start/idea`. The remaining milestone-02 flow is not claimed complete.

## Milestone 01 completed — 2026-11-11

The actual Next.js/Django/PostgreSQL scaffold runs locally in Docker Compose. This section records the completed foundation before the subsequent frontend checkpoint above.

User additions during this milestone were also handled: connect the existing GitHub repository, prepare the requested push on `work/milestone01`, add the database to the installed desktop pgAdmin, make `next/image` available to VS Code, and use English explanations. The application UI remains Persian RTL.

### Current running services

| Service | Local access | Verified state |
| --- | --- | --- |
| Next.js | http://localhost:3000/ | Healthy; client health screen works |
| Same-origin API | http://localhost:3000/api/v1/health/ | 200; real Django/PostgreSQL check |
| Django | http://localhost:8000/api/v1/health/ | 200; sanitized 503 on database failure |
| PostgreSQL 17 | 127.0.0.1:5433 | Healthy; named `nama-analyze_postgres_data` volume |
| Desktop pgAdmin | Servers > NAMA Analyze (Docker local) | Registered and actual connection verified |

The Compose project is `nama-analyze`, with `frontend`, `backend` and `db`. All host ports bind only to loopback. Existing local PostgreSQL 18 continues using 5432; its pgAdmin connection was preserved.

### Files and architecture

- `frontend/`: Next.js App Router + TypeScript + Tailwind, one npm lockfile, pinned Node version, Dockerfile, lint/typecheck configuration, local font/logo copies and a minimal accessible Persian RTL health screen with pending/success/error/retry states.
- `frontend/next.config.mjs`: server-side `/api/v1/` rewrite to Django, standalone output, and explicit `localhost`/`127.0.0.1` development origins. No domain API handlers or browser-visible container origin were introduced.
- `backend/`: Django configuration, pinned full Linux dependency closure, PostgreSQL settings, initial custom `accounts.User` migration, admin registration, ASGI/WSGI entry points, readiness endpoint and five behavior tests.
- `compose.yaml`: dev reload mounts, service readiness dependencies/healthchecks, pinned base images, local ports and the persistent PostgreSQL volume.
- `.env.example`: placeholders and documented local configuration. Ignored `.env` was generated with random local credentials; no secret was printed or committed.
- `scripts/setup_env.py`: idempotent local environment generation.
- `scripts/smoke_check.py`: direct/proxied API checks and optional real database outage/recovery/persistence verification.
- `scripts/browser_check.mjs`: Chrome checks using Node's built-in WebSocket, with no additional browser-test dependency.
- `scripts/register_pgadmin.py`: additive, idempotent registration in the installed desktop pgAdmin, settings backup, dedicated AppData passfile outside the repository, and a real Windows-to-Docker connection check.
- `README.md`: actual setup/start/stop/logs/migration/check commands, pgAdmin/editor instructions, version sources and limitations.
- `docs/STATUS.md`: this execution record. Other existing handoff files, prompts and references remain available. Font/logo copies match the reference SHA256 hashes.

No Ads/Products/Shops models, market fixtures, authentication screens, production deployment, paid APIs or milestone 02 UI were added. No database volume was removed or database flushed. `infra/` is deferred until deployment configuration is needed.

### Selected versions

| Runtime/package | Selection |
| --- | --- |
| Node image | `node:24.22.2-bookworm-slim`, supported Node 24 LTS |
| Next / React / React DOM | 16.4.6 / 19.3.1 / 19.3.1 |
| TypeScript / Tailwind | 6.0.2 / 4.3.5 |
| Python image | `python:3.13.18-slim-bookworm` |
| Django / DRF | 5.2.19 LTS security patch / 3.18.3 |
| Psycopg / asgiref / sqlparse | 3.3.8 / 3.13.0 / 0.6.1 |
| PostgreSQL image | `postgres:17.11-bookworm` |

Versions and compatibility were checked against official documentation, registries and Docker official-image manifests before selection; links are in README.md. Images do not use unpinned `latest` tags.

### Exact checks that passed

| Command/check | Actual result |
| --- | --- |
| `python scripts/setup_env.py` | Created ignored local credentials; existing files are preserved on repeat |
| `docker compose config --quiet` | Valid configuration without printing resolved secrets |
| `docker compose build` | Both final images built successfully; locked npm/pip dependencies installed |
| `docker compose up -d --renew-anon-volumes --wait` | All three final services healthy; named PostgreSQL volume retained |
| `docker compose run --rm backend python manage.py makemigrations accounts --no-header` | Custom user migration generated before the first application migration |
| `docker compose exec -T backend python manage.py check` | No issues |
| `docker compose exec -T backend python manage.py migrate --noinput` | Initial migrations applied at startup; explicit repeat found no pending migration |
| `docker compose exec -T backend python manage.py makemigrations --check --dry-run` | No model drift |
| `docker compose exec -T backend python manage.py test health --verbosity 2` | Five tests passed against PostgreSQL; temporary test database cleaned up |
| `docker compose exec -T backend pip check` | No broken requirements |
| `docker compose run --rm --no-deps frontend npm run lint` | Passed with zero lint warnings/errors |
| `docker compose run --rm --no-deps frontend npm run typecheck` | Route types and TypeScript passed |
| `docker compose run --rm --no-deps frontend npm run build` | Next.js production build succeeded |
| `docker compose run --rm --no-deps frontend npm audit` | Zero reported vulnerabilities |
| `npm.cmd --prefix frontend ls eslint minimatch --depth=2` | Valid dependency tree; no invalid ESLint peer dependency |
| `npm.cmd --prefix frontend run typecheck` | Local editor types generated; `next/image` module is installed |
| `python scripts/smoke_check.py --database-cycle` | Direct and proxied 200 -> 503 while DB stopped -> 200 after recovery; exact sanitized JSON/no-store; all 19 migration records persisted |
| `python scripts/smoke_check.py` | Rechecked final Next HTML, Persian RTL, logo and both 200 API paths |
| `node scripts/browser_check.mjs` | Actual client pending/ready/503/error/retry behavior passed; keyboard Enter retries; no uncaught browser exceptions |
| Browser viewports | 1440 x 1000 and 390 x 844; local font loaded; no horizontal overflow |
| `python scripts/register_pgadmin.py` | Saved NAMA connection once, preserved existing PostgreSQL 18 entry, authenticated to `nama_analyze` on PostgreSQL 17.11 through its AppData passfile |
| Reference asset SHA256 comparison | Copied font/logo match their originals |

Screenshots were visually inspected at desktop and mobile sizes: restrained red/white identity, correct Persian RTL, readable status card and wrapped mobile content. Final browser artifacts are outside Git at `C:\Users\Admin\AppData\Local\Temp\nama-analyze-browser-ccYH9x`. This verifies the milestone 01 diagnostic screen; solar/Home/sidebar/Products comparisons belong to their later UI work.

### Environment findings and resolved failures

- Windows 11 Home build 26200. Host Node 24.18.0, npm 11.16.0, Python 3.14.4 and Git 2.54.0 were present. Backend Python 3.13 and the selected Node runtime run in Docker; no system Python/Node upgrade was required.
- Docker Desktop was initially stopped. It was started; the working environment reports Desktop 4.99.0, Engine/CLI 29.9.3 and Compose 5.7.0.
- The workspace initially denied writes even outside the sandbox. An explicitly approved UAC operation granted Modify only to the execution account on this project directory; no parent folder or Everyone/Users grant was changed.
- PowerShell blocks `npm.ps1`; `npm.cmd` was used without changing execution policy.
- PostgreSQL 18 already occupied host 5432. Project PostgreSQL uses 5433 and leaves that installation untouched.
- The system HTTP proxy initially interrupted the Python localhost probe. The local smoke checker now bypasses proxies explicitly.
- Browser inspection initially exposed a genuine hydration failure at `127.0.0.1`: Next's dev origin check blocked its HMR WebSocket. The final local origin allowlist fixed it; actual browser health and retry then passed.
- The first lint run found an anonymous PostCSS export and effect-state lint issue; both were fixed. Final lint and build passed.
- pgAdmin's CLI needed its existing PostgreSQL DLL path. The registration helper supplies it only to the child process, uses the existing installed driver, and now verifies the connection.
- Local VS Code dependencies were installed with `npm.cmd ci --engine-strict=false --no-fund` because the host Node patch is older than the pinned Docker runtime. This override was limited to editor dependency installation. `.next` editor types were generated locally.

### Remaining limitations and blockers

No remaining milestone 01 runtime/check blocker. ESLint 9.39.5 is marked deprecated upstream but retained to satisfy the current Next plugin peer ranges. A narrow override moves only `@typescript-eslint/typescript-estree`'s minimatch to 11.0.1 for its audit fix; this exceeds its declared major range and was checked with lint/typecheck/build/audit. Revisit it when upstream plugins advertise the newer compatible releases.

Production deployment and authenticated workspaces are intentionally outside this milestone. No production deployment check was run. No UI checks for unimplemented solar/Home/Products screens are claimed.

### Git and next task

The directory initially had no `.git`. It is connected to `https://github.com/AriaHassanzadeh/NAMA.git`, preserving the existing `main` commit/history. Milestone 01 was pushed on `work/milestone01`; its local/remote commit was verified as `1364003c228fd0ff29c27546b75b3cffd80e0d2c`. `.env`, dependencies, build outputs and local credentials are ignored. No force push or public deployment occurred.

Next milestone: `prompts/02-ENTRY-AND-HOME.md`, only when the user requests it. Do not begin it automatically.

## Preserved initial handoff (historical)

The following is the pre-implementation status, retained for context; the completed milestone record above is authoritative.

<details>
<summary>Initial handoff before milestone 01</summary>

# Handoff status

## Current state

- Project: personal NAMA Analyze, Analyze-only.
- Updated design flow: solar entrance → idea → customer → goal → current Analyze Home.
- Design reference and corrected Products layout: included.
- Figma entry additions confirmed: solar 21:2, idea 22:2, customer 23:2, goal 24:2 in the existing file.
- Figma native layer inspection remains blocked by the Starter quota; no reusable component library or interactive Figma prototype wiring was added.
- Entry flow validated in the HTML reference: stage validation, back/reload persistence, completion to Home and profile editing. Mobile review at 390 px showed no horizontal overflow.
- These are reference-demo checks, not Next.js/Django application checks.
- Project instructions, architecture and milestone 01 prompt: included.
- Next.js app: not created.
- Django app/database schema/API: not created.
- Docker Compose / production deployment: not created.
- Local developer machine tools: not inspected from this chat.
- Application checks/tests: not run because there is no application scaffold yet.
- The hosted vanilla design demo has been updated to the same approved entry flow; it remains a design prototype.

## Next task

Run `prompts/01-START.md` in Codex from this project root.

## Update after each milestone

Record the milestone, concrete changes, exact checks that passed, checks that could not run, blockers and the next task. Keep completed work; do not reset the project to this initial handoff status.

</details>
