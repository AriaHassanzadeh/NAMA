# Milestones

The user wants to work step by step. Finish and verify one milestone per requested task. Only milestone 01 is authorized by the initial handoff prompt; the rest records the intended sequence.

| Step | Build | Completion evidence |
| --- | --- | --- |
| 01 | Next.js + Django + PostgreSQL development foundation, custom user, Compose and same-origin health request | Clean startup, migrations, DB readiness check, frontend checks/build and documented commands |
| 02 | Solar entry, three-step project discovery, shared React shell and existing Home | Working idea/customer/goal flow, draft restoration, reference-matching dark entrance and red/white RTL workspace, responsive review |
| 03 | Domain models, demo seed and read API | Related shops/products/ads, provenance, repeatable seed, filtering/pagination, schema and generated types |
| 04 | Ads view | Card/table modes, working filters/sort/pagination, details, empty/loading/error states |
| 05 | Products and Shops | Corrected Products columns, Shops table/sparklines, working search/filter/details and mobile layout |
| 06 | Django sessions, workspaces and Saved | Login/logout/CSRF, ownership isolation, persistent bookmarks, access-control tests |
| 07 | Reports and CSV import | Recharts/TanStack tables, selected metrics, explicit demo labels, validated import preview/errors, source timestamps |
| 08 | Production preparation | Production images, Caddy config, secure settings, CI, health checks, backup/restore instructions; deploy only when requested |

Use `prompts/02-ENTRY-AND-HOME.md` for milestone 02.

During milestone 02, temporary typed demo fixtures are acceptable for visual development; document them and replace the data-access boundary with Django in milestone 03. Do not present browser localStorage as the final source of truth for domain data or authenticated bookmarks.

Add dark-mode parity with the supplied design once the light shared shell is stable. Introduce each optional dependency when needed. Redis/Celery, real ad-provider APIs and scraping are deferred until an actual use case is selected.

Milestones are checkpoints, not a reason to ask permission for every file edit or ordinary local test within the current task.
