# NAMA Analyze — project instructions

This is a personal learning/build project. Continue from these files even when the previous chat is unavailable. Explain changes and the next practical action in Persian; keep code and identifiers in English.

## Read first

1. `docs/PROJECT.md`
2. `docs/STATUS.md`
3. The task the user selected, initially `prompts/01-START.md`
4. `docs/DESIGN.md` and `docs/USER-FLOW.md` before UI work

## Scope and agreed choices

- Start with the restored solar entrance, then idea → customer → goal questions, then the existing Analyze Home. See `docs/USER-FLOW.md`.
- Implement Analyze only within the workspace: Home, Ads, Products, Shops, Reports, Saved.
- Frontend: Next.js, TypeScript, App Router, Tailwind CSS. Do not substitute Vite.
- Backend: Python 3.13, Django 5.2 LTS, Django REST Framework, PostgreSQL.
- Add shadcn/ui, Lucide, TanStack Query/Table, Recharts, React Hook Form and Zod when the relevant milestone needs them.
- Run locally with Docker Compose. Production later targets one VPS with Caddy, Gunicorn, a Next.js standalone image and persistent PostgreSQL.
- Release, publishing, content generation, payments and paid external APIs are outside the current scope.
- The initial app uses explicitly labelled demo data. CSV/manual imports come later. Never present illustrative records as verified or live Iranian market data.
- No paid service or new subscription is needed for the initial milestones.

## Work in small completed milestones

Complete the requested milestone, including relevant checks and fixes, before returning. Do not implement later milestones unless asked. Resolve ordinary implementation details yourself. Preserve unrelated user changes.

Read `docs/STATUS.md` at the beginning and update it at the end with files changed, exact commands that passed, remaining blockers and the next milestone. If a check could not run, state why; do not mark it passed. Do not claim the app already exists just because the reference demo runs.

## Repository layout to create in milestone 01

- `frontend/`: Next.js application, one npm lockfile.
- `backend/`: Django application and pinned dependency lock/requirements.
- `infra/`: deployment configuration as it becomes necessary.
- Root `compose.yaml`, `.env.example`, README with tested local commands.
- Existing `reference/`, `docs/`, and `prompts/` remain available as handoff material.

Check official documentation before resolving compatible exact versions. Keep Django on 5.2 LTS with the current security patch in that line. Choose a supported Node LTS compatible with the chosen stable Next.js release and pin it. PostgreSQL 17 is the proposed starting major version; record the actual selection. Do not use prereleases or unpinned `latest` container tags.

## Architecture

Django owns authentication, authorization, database models and business rules. Configure a minimal custom Django user before initial migrations. Next.js renders the UI and calls Django; do not duplicate the domain in Next API handlers or introduce a second ORM/database.

Use same-origin `/api/v1/` browser requests, proxied to Django. Container-only backend addresses belong in server-side configuration. Future authentication uses Django sessions with HttpOnly cookies and CSRF protection for unsafe requests. Do not store access tokens in localStorage or disable CSRF to fix integration errors.

Use environment variables for secrets, no committed `.env` or real credentials. `.env.example` contains placeholders and documented local setup. Keep a named database volume. Never remove volumes, flush a database, reset user changes or deploy publicly without the relevant user instruction.

## Design requirements

Use the restrained dark orbital entrance and question screens from the reference before the workspace. Preserve the latest NAMA / CF red-and-white workspace identity, Persian RTL, Vazirmatn, spacious cards, clear tables, compact filters and a right sidebar. Reuse the supplied logo and fonts. See `docs/DESIGN.md` for exact tokens, source precedence and the corrected Products layout.

Build real React components and interactions; do not iframe the HTML, screenshot the UI, or serve the vanilla demo as the finished Next.js app. Reference files are read-only source material, not application code. Do not read base64-heavy HTML in full when the readable CSS/JS contains the needed information.

Use logical spacing properties and explicit layout direction for mixed RTL/LTR content. Validate the sidebar and Products columns at desktop and mobile widths. Keep table overflow inside its container. Add usable focus, keyboard support, labels, empty/loading/error states as their features are introduced.

## Verification

Run checks appropriate to the milestone: frontend lint/typecheck/build, Django checks and migrations, targeted API behavior tests, and Compose smoke checks. Test real behavior rather than mirroring implementation. After passing checks, report their results once. For UI milestones, inspect the rendered result and compare with the reference; record if visual inspection was unavailable.

Keep each task bounded for the user's available Codex allowance: inspect the needed files, make focused edits, and avoid reinstalling or rereading the entire repository without a reason.
