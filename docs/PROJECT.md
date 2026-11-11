# Project brief

## Purpose and current state

Build the latest NAMA Analyze design as a personal full-stack project. The original team startup work was paused because reliable Iranian market data was not available. This implementation is independent personal work and must remain useful with demo data and, later, user-supplied imports.

The current handoff includes a working vanilla design demo, a restored solar entrance with three project questions, a static corrected Products layout and project instructions. It does not include a Next.js/Django implementation, a deployed backend or a configured production server.

## Product scope

| View | Intended behavior |
| --- | --- |
| Entry | Solar entrance → idea → customer → goal; preserve draft answers and enter the existing Home |
| Home | Reference hero/header banners, onboarding cards, daily top items, Ads / Products / Shops tabs and discovery entry points |
| Ads | Search, platform/category/country/format filters, sorting, card/table views, details and save actions |
| Products | Search and filters, product + shop information + related ads rows, details and save actions |
| Shops | Search and filters, shop table with visits, sample revenue, ad/product thumbnails, country and actions; tracked shops |
| Reports | Demo metrics, charts, tables, filters and clear provenance; later summaries from imported data |
| Saved | Saved ads/products/shops, consistent details and empty states |

Release, publishing/calendar, generated content, live scraping and paid data providers are not part of the initial product. The solar entrance and project discovery are now included again by explicit user instruction. Release and publishing remain outside the current navigation.

## Technical decisions

| Area | Decision |
| --- | --- |
| Frontend | Next.js + TypeScript + App Router; npm for a simple single frontend package |
| UI | Tailwind + shadcn/ui where useful, Lucide icons, local Vazirmatn, Persian RTL |
| Remote state | TanStack Query after API integration starts |
| Tables/charts | TanStack Table / Recharts when those views are built |
| Forms | React Hook Form + Zod; server validation remains authoritative |
| Backend | Python 3.13 + Django 5.2 LTS + Django REST Framework; django-filter when needed |
| Database | PostgreSQL; proposed starting major 17, with a persistent volume |
| API contract | Versioned REST `/api/v1/`, drf-spectacular, generated frontend types with openapi-typescript when endpoints exist |
| Authentication | Django custom user and Django sessions; same-origin cookies + CSRF |
| Development | Docker Compose, frontend and backend hot reload, environment template |
| Production later | Single VPS, Caddy HTTPS, Gunicorn, Next standalone runtime, PostgreSQL |
| Later background work | Redis/Celery only after an actual asynchronous task needs them |
| Later delivery | GitHub Actions/GHCR, tested immutable images, controlled migrations and backups |

The user explicitly selected Next.js rather than Vite. Avoid unnecessary monorepo tooling, Kubernetes, microservices and a second auth stack.

## Data policy for this build

The supplied reference includes 10 demo ads, 8 demo products and 6 demo shops. Their business metrics, examples and `.example` domains are illustrative. Placeholder media marked as video does not guarantee that a playable video asset exists.

Keep a clear Persian demo-data label on relevant pages and reports. Never claim that these figures are verified Iranian business intelligence. Preserve record relationships when turning fixtures into database seed data. Seed commands must be repeatable and must not delete user imports.

For later imports, record source kind (demo/manual/CSV/provider), source reference, observation date and import timestamp. Currency must be explicit; do not relabel the demo dollar prices as toman. Distinguish observed values from estimates. An unavailable field should stay unavailable rather than being silently invented.

CSV/manual import is the first real data path. Real provider integrations remain optional future work, with no dependency on purchasing one now.

## Later quality requirements

Tenant/workspace ownership must be enforced by Django before exposing private saved items and imports. Authentication, input limits, server-side validation, import error reporting and data isolation are milestones, not features already present in this bundle. Avoid suggesting the app is production-ready before they are implemented and tested.
