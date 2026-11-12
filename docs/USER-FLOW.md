# Current approved entry flow

The latest user change restores the earlier NAMA solar entrance and step-by-step project discovery. The existing Analyze Home is the destination after the questions; its layout remains the current approved one.

## Order

| Order | Screen | Action/result |
| --- | --- | --- |
| 0 | Solar entrance | Central red NAMA mark/wordmark, orbiting media icons, faint stars, motion pause and theme controls; click NAMA to start |
| 1 | Idea | “اول، از ایده‌ات بگو.”; example chips and a bottom composer; require a meaningful short idea |
| 2 | Customer | “مشتری تو چه کسی است؟”; customer type and/or free text, optional initial market and experiment budget |
| 3 | Goal | “از این بررسی چه می‌خواهی؟”; select market understanding, competitor comparison or opportunity discovery; optional note |
| 4 | Workspace Home | Enter the current CF-inspired Analyze Home with its existing cards, banners, daily selections and navigation |

## Visual requirements

Restore the restrained earlier orbital appearance from the supplied references. No additional Saturn tilt, heavy 3D treatment or redesigned marketing page is requested. Use the red central mark, subtle tinted media icons and slightly visible stars. The entry and questions default to dark; the workspace keeps its own existing theme preference.

The question view has a left NAMA wordmark, centered three-step progress, right back/theme controls, centered title/options and a wide bottom input. Keep mobile comfortable and allow vertical scrolling rather than overlapping form sections with a fixed composer.

## Interaction requirements

- One question screen at a time; back and progress navigation preserve previous answers.
- Save draft inputs as the user types; reloading the same step must restore its contents.
- Validate each stage; direct access to a later stage without required earlier answers returns to the first incomplete stage.
- Enter continues; Shift + Enter adds a newline. Respect IME composition.
- Completing stage 3 saves a project brief, enters Home and makes the answers available from the workspace/project profile for editing.
- The “مستقیم به نمونه برو” link explicitly opens the prepared demo without pretending a project brief was completed.
- Motion can be paused, hover/focus pauses orbital movement, and reduced-motion preferences are respected.
- User answers must never be placed in URLs. This demo uses browser-local state; the future app will persist private project briefs through Django once authentication/workspaces exist.
- No AI generation or live market research is performed by this flow. Demo metrics retain their labels.

## Routes

The reference HTML uses hashes: `#/`, `#/start/idea`, `#/start/customer`, `#/start/goal`, then `#/workspace/home`.

The Next.js implementation should use normal App Router paths: `/`, `/start/idea`, `/start/customer`, `/start/goal`, `/workspace/home`. Render the entrance outside the workspace sidebar layout. Preserve the existing Ads, Products, Shops, Reports and Saved workspace views.

The corrected Products layout remains authoritative. This entry change does not reintroduce Release or publishing.
