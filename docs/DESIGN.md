# Design source and implementation notes

## Source precedence

1. Use `reference/NAMA-Analyze-Design.html` for the latest approved entry flow and Analyze appearance: solar entrance → idea → customer → goal → the existing Home. See `docs/USER-FLOW.md`.
2. For Products desktop column alignment, use `reference/NAMA-Products-Layout-Fixed.html` and corrected Figma frame `17:2`.
3. Use `reference/demo/analyze/app.css`, `data.js` and `app.js` as readable reference. Rebuild as React components; these files are not the production architecture.

The corrected Products HTML is a static reference at a 1280 px canvas, not an interactive production screen. Its row limit for capture is not a product requirement. The final Next.js app still needs all seeded items, responsive layouts, real filters and pagination.

The restored entrance and three question screens have now also been captured into the same Figma file. The import service confirmed all four additions. They are raw captured frames; detailed native layer/font auditing was blocked by the account Starter read quota. Existing workspace Home is still the destination.

## Figma links

- [01 — Solar entrance](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=21-2)
- [02 — Idea](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=22-2)
- [03 — Customer](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=23-2)
- [04 — Goal](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=24-2)

- [Design file](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ)
- [Home light](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=2-2)
- [Products — corrected layout](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=17-2)
- [Ads light](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=7-2)
- [Shops light](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=9-2)
- [Reports light](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=3-2)
- [Saved light](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=4-2)
- [Home dark](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=10-2)
- [Shops dark](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=8-2)
- [Reports dark](https://www.figma.com/design/pUpoTIp8ZmLQYmCg1l0YWQ?node-id=5-2)

These are captured editable frames, not an audited reusable component library. The original Products frame `6:2` still exists and has the overlap defect; do not use it as the final alignment source. The corrected frame was added, not substituted for the original.

In the preceding session, native Figma inspection hit the account read quota and the cloud browser could not render the editor because of WebGL. Local HTML is included so that implementation can proceed without additional Figma access. No need to repeatedly retry the same blocked access.

## Visual identity

CF-inspired NAMA identity: red primary actions, white/light gray surfaces, dark ink, thin borders, generous spacing and restrained shadows. Do not replace it with a generic purple AI dashboard or copy Minea's orange palette.

| Token | Light | Dark |
| --- | --- | --- |
| Primary | `#e12c35` | `#e12c35` |
| Primary hover | `#c5222b` | `#c5222b` |
| Ink | `#191722` | `#f6f5fa` |
| Muted | `#81808b` | `#a29eb0` |
| Surface | `#ffffff` | `#161321` |
| Canvas | `#f8f9fb` | `#0c0917` |
| Raised | `#f5f5f7` | `#201c2d` |
| Border | `#e7e7ec` | `#302b3d` |
| Primary soft | `#fff0f1` | `#341924` |
| Positive | `#16865c` | `#8bcead` |
| Positive soft | `#eaf6ef` | `#172e26` |
| Chart | `#e12c35` | `#94b3ff` |
| Chart area | `#fff0f1` | `#212a40` |

Use local `vazirmatn.woff2` for Persian. `anton.ttf` is the reference display/wordmark font; `be-vietnam-pro-600.ttf` supports Latin labels. Reuse `mark.svg`. In Next.js, configure the local fonts rather than adding an external font dependency.

## Products overlap fix

At the corrected 1280 px reference canvas, sidebar width is 248 px, workspace width 1032 px and content horizontal padding 32 px. Rows have width 968 px and end 32 px before the sidebar. The physical left-to-right columns are related ads (30%), shop (22%), product main (48%); text inside remains RTL where appropriate.

The capture fix uses an explicit LTR layout container with RTL content children. In React, choose a robust responsive flex/grid layout with `min-width: 0` and logical spacing. Do not apply a fixed 1280 px width to the actual application or combine a full-width main area with an overlaid fixed sidebar.

Inspect at approximately 1440, 1280, 768 and 390 px. Use a collapsible sidebar on small screens. Tables may scroll inside their wrapper, while the whole page should not overflow horizontally.

## Readable reference map

- `reference/demo/index.html`: small static shell; relative fonts/assets.
- `reference/demo/analyze/app.css`: exact workspace styles and responsive rules.
- `reference/demo/analyze/entry.css` and `entry.js`: restored solar entrance and three-step discovery.
- `reference/demo/analyze/app.js`: `shell`, `home`, `adCard`, `adsTable`, `productRow`, `shopsTable`, `reportPage` and dialogs.
- `reference/demo/analyze/data.js`: explicitly illustrative records and image crop coordinates.

Some images are reference screenshot crops defined by `sw/sh/x/y/w/h` in `data.js`. Port their intended crop rather than showing an entire source screenshot inside a card. Do not fabricate video playback when only a thumbnail is available.
