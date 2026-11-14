# NAMA Analyze

Personal Market Analyzor project. Milestone 01 provides a local Next.js + Django + PostgreSQL development foundation and a Persian RTL connection-status screen.

The solar entrance opens Idea at `/start/idea` and includes **Sign in / Sign up**. Submitting a valid Idea continues to Customer at `/start/customer`, where you can choose an audience or describe the customer, and optionally add an initial market and experiment budget. Both pages preserve browser-local drafts, theme and media source. Customer is the current review checkpoint: submitting saves its answers; Goal and Analyze Home follow after review. Idea examples use the labelled mock API; Customer choices are static form options. Email/password signup requires email verification before sign-in. See [API documentation](docs/API.md) and [actual database diagrams/columns](docs/DATABASE.md) for the labelled sample database. The supplied `reference/` files remain design handoff material.

## Requirements and versions

Use Docker Desktop with Linux containers and Docker Compose. Python 3 on the host is sufficient for the small setup/smoke scripts; the backend runs on its pinned Python image.

| Component | Pinned version |
| --- | --- |
| Node | 24.22.2 LTS, `node:24.22.2-bookworm-slim` |
| Next.js / React | 16.4.6 / 19.3.1 |
| TypeScript / Tailwind | 6.0.2 / 4.3.5 |
| Python | `python:3.13.18-slim-bookworm` |
| Django / DRF | 5.2.19 LTS / 3.18.3 |
| PostgreSQL | `postgres:17.11-bookworm` |

The frontend uses npm and one `frontend/package-lock.json`. `backend/requirements.txt` pins the complete Linux/Python 3.13 dependency closure. No paid service or API key is required.

## Start locally

Run from this project directory:

```powershell
python scripts/setup_env.py
docker compose config --quiet
docker compose up -d --build --wait
docker compose exec -T backend python manage.py seed_demo
```

The setup script generates random local credentials in ignored `.env` and preserves an existing file. `.env.example` documents every setting with placeholders. The backend applies committed migrations before starting; the custom `accounts.User` exists in its initial migration.

Open:

- Application: http://localhost:3000/
- Idea page: http://localhost:3000/start/idea
- Customer page: http://localhost:3000/start/customer (requires a valid Idea draft)
- Sign in: http://localhost:3000/auth/login/
- Sign up: http://localhost:3000/auth/signup/
- Email confirmation/resend: http://localhost:3000/auth/verify/
- Connection-status screen: http://localhost:3000/health/
- Health through Next.js: http://localhost:3000/api/v1/health/
- Django health directly: http://localhost:8000/api/v1/health/
- API explorer: http://localhost:3000/api/v1/docs/
- OpenAPI: http://localhost:3000/api/v1/schema/

All published ports bind to `127.0.0.1`. PostgreSQL is available to desktop clients at `127.0.0.1:5433`, database `nama_analyze`, user `nama`. The password stays in `.env`. Port 5433 avoids the PostgreSQL 18 instance already installed on this machine.

The status screen makes a same-origin `/api/v1/health/` request. A server-side Next rewrite forwards it to Django, where `SELECT 1` verifies PostgreSQL readiness. Success returns HTTP 200; a database failure returns HTTP 503 with sanitized JSON and no-store headers. `BACKEND_ORIGIN` is server-side configuration, with no `NEXT_PUBLIC_` exposure.

The Next development allowlist contains only `localhost` and `127.0.0.1`, so the development WebSocket and client hydration work from both local URLs.

Django owns users, sessions, CSRF, authorization and business data. Its development defaults keep session cookies HttpOnly and CSRF middleware enabled. Email/password forms use the same-origin API and fetch a fresh CSRF token before unsafe requests; passwords and verification tokens are never written to browser storage.

## Local email verification

The default file email backend writes messages to ignored `backend/.local-emails/`; it does **not** send messages to a real inbox. Sign up in the UI, then open the latest matching local verification email:

```powershell
python scripts/read_local_email.py --recipient your-email@example.com --open
```

The browser page requires an explicit **تأیید ایمیل** click. Verification links expire after 24 hours, work once and are replaced by a newer resend. Resend has a 60-second cooldown. Confirmation activates the account; sign in with the same email/password afterward. The local helper never prints the private link unless explicitly given `--json` for automated checks.

For actual inbox delivery, set the documented `EMAIL_*` settings in ignored `.env`, select `django.core.mail.backends.smtp.EmailBackend`, set an appropriate sender and `ACCOUNT_VERIFICATION_ORIGIN`, then recreate backend with `docker compose up -d --wait backend`. SMTP credentials have not been configured or tested. Do not paste passwords or private verification links into Git.

## Daily commands

```powershell
docker compose up -d --wait
docker compose ps
docker compose logs --tail 50 frontend backend db
docker compose exec -T backend python manage.py migrate --noinput
docker compose stop
```

`stop` preserves containers and the named `nama-analyze_postgres_data` volume. Source bind mounts enable frontend/backend reload. After changing npm dependencies, rebuild and replace only frontend anonymous dependency/build volumes:

```powershell
docker compose up -d --build --renew-anon-volumes --wait frontend
```

The PostgreSQL volume is separate from those anonymous frontend volumes. Database credentials in `.env` must continue to match an already initialized database.

## Checks

Run against the started stack:

```powershell
docker compose config --quiet
docker compose exec -T backend python manage.py check
docker compose exec -T backend python manage.py makemigrations --check --dry-run
docker compose exec -T backend python manage.py test --verbosity 1
docker compose exec -T backend pip check
docker compose run --rm --no-deps frontend npm run lint
docker compose run --rm --no-deps frontend npm run typecheck
docker compose run --rm --no-deps frontend npm run build
docker compose run --rm --no-deps frontend npm audit
python scripts/smoke_check.py
python scripts/api_smoke_check.py
```

Run the optional outage check only when a brief interruption of this local database is acceptable:

```powershell
python scripts/smoke_check.py --database-cycle
```

It verifies direct/proxied health, temporarily stops only this project's `db`, checks sanitized 503 responses, restores the database in `finally`, and verifies recovery and persisted migration rows. Local HTTP checks bypass the machine's system proxy.

The browser check uses an installed Chrome plus Node's built-in WebSocket, with no additional npm package:

```powershell
node scripts/browser_check.mjs
node scripts/landing_check.mjs
node scripts/idea_check.mjs
node scripts/customer_check.mjs
node scripts/auth_check.mjs
```

Set `CHROME_PATH` if Chrome is elsewhere. The health-screen check targets `/health/`; the landing check targets `/`; the Idea check covers the mock API states, draft recovery, validation, keyboard/IME input and storage failures at `/start/idea`. The Customer check covers the prior-Idea guard, audience/text alternatives, optional fields and navigation/persistence at `/start/customer`. The auth check creates one isolated local test account and verifies signup, local email confirmation, protected sessions and sign-in. It uses `localhost` to match the verification origin, keeps credentials/private links out of diagnostics and leaves the test account available for inspection. Checks also cover RTL, fonts, responsive layout and motion preferences. Screenshots are saved outside the repository in the temporary directory printed by each script. If Next misses a newly added route on the Windows bind mount, run `docker compose restart frontend`.

Idea and Customer drafts use the existing `nama-analyze-entry-v1` browser storage key. Customer preserves reference keys `customer`, `audience`, `market` and `budget`; later authenticated upload will map `customer` to Django's `customer_description` and `budget` to `budget_band`. No answer is sent in a URL or uploaded to Django at this checkpoint. When storage is blocked/full, the page explains that the draft only remains in the current tab; reload cannot restore that in-memory fallback. Direct Customer access waits for draft recovery, then redirects to Idea if its required answer is incomplete.

## VS Code and native tools

For backend import resolution, create/select an isolated editor environment:

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

In VS Code use **Python: Select Interpreter** and choose `backend/.venv/Scripts/python.exe`; reload the window if Pylance cached the old interpreter. This machine's environment was created with Windows Python 3.14 and verified for Django/DRF imports. The application and all backend behavior checks continue to use Docker Python 3.13. Existing personal `.vscode` settings are preserved locally and are not committed.

Open the repository root. `next/image` is supplied by the `next` package; it has no separate installation. To make frontend dependencies/types available to VS Code, use Node 24.22.2 locally and run:

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run typecheck
```

This Windows machine initially had Node 24.18.0. The editor dependencies were installed with a one-off `--engine-strict=false` override; application checks use the pinned Docker runtime. If VS Code retains a stale module error, run **TypeScript: Restart TS Server**.

ESLint 9.39.5 is retained for the peer ranges of the plugins currently shipped by `eslint-config-next`; npm marks that ESLint line deprecated. A scoped development dependency override updates only `@typescript-eslint/typescript-estree`'s `minimatch` to 11.0.1 to address its audit advisory. This crosses that dependency's declared major range and is covered by lint/typecheck/build checks. Revisit it when the upstream plugin releases support newer ESLint and the patched minimatch range.

## Installed desktop pgAdmin

The existing PostgreSQL 18 connection is preserved. This machine also has **NAMA Analyze (Docker local)** under **Servers**. Refresh the Servers tree if needed, then expand `Databases > nama_analyze > Schemas > public > Tables`.

To register it again without duplicating the connection:

```powershell
python scripts/register_pgadmin.py
```

The script targets the installed desktop pgAdmin at `C:\Program Files\PostgreSQL\18\pgAdmin 4` by default; override `PGADMIN_INSTALL_DIR` when necessary. It uses pgAdmin's supported additive import, backs up its settings before the first import, preserves existing servers, stores a dedicated passfile in the user's AppData outside Git, and tests the same connection using pgAdmin's driver. Run it as the Windows user who owns the pgAdmin profile.

## Version sources and handoff

Versions were checked on 2026-11-11 against [Next.js installation documentation](https://nextjs.org/docs/app/getting-started/installation), [Node release support](https://nodejs.org/en/about/previous-releases), [Django 5.2.19 security release notes](https://docs.djangoproject.com/en/5.2/releases/5.2.19/), [DRF](https://pypi.org/project/djangorestframework/), [PostgreSQL versioning](https://www.postgresql.org/support/versioning/) and the [official Docker image manifests](https://github.com/docker-library/official-images/tree/master/library). Desktop import follows [pgAdmin's documentation](https://www.pgadmin.org/docs/pgadmin4/latest/import_export_servers.html).

Read `AGENTS.md`, `docs/PROJECT.md`, and the latest entry in `docs/STATUS.md` before continuing. `README-FA.md`, `prompts/` and `reference/` are preserved handoff material. Production infrastructure under `infra/` will be introduced when its milestone requires it.
