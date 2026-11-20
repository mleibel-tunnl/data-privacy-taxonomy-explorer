# Notes — Data Privacy Taxonomy Explorer

Working notes for the Fideslang sunburst explorer. Written 2026-11-20.
`README.md` covers how to run it; this file covers *why it is the way it is* and
what's still open.

---

## 1. Origin: the IAB page has no chart to extract

The ask started as "can we extract the sunburst from
<https://iabtechlab.github.io/fideslang/#taxonomy-explorer>". Short answer: no,
because there's nothing dynamic there.

That page is MkDocs (`mkdocs-material` 7.2.5) and the "Taxonomy Explorer"
section is three static images dropped in with Markdown image tags:

- `img/Tree@1x.svg`
- `img/Radial Tree@1x.svg`
- `img/Sunburst@1x.svg`

No `<script>` tags, no JSON/CSV fetch, no chart library. The geometry and the
labels are baked into the SVG paths. You *could* scrape text out of the SVG, but
you'd get label strings with no parent/child structure — strictly worse than
going to the source data.

So this project ignores the image and rebuilds the view from the real taxonomy.

## 2. Where the data comes from

Two equivalent sources:

| Source | Notes |
|---|---|
| `fideslang` on PyPI | What `scripts/fetch_taxonomy.py` uses. `from fideslang import DEFAULT_TAXONOMY`. Pinned in `requirements.txt`. |
| `IABTechLab/fideslang` → `data_files/` | Same content as CSV, JSON **and** YAML. Good for eyeballing diffs between versions. |

Currently built against **fideslang 3.1.4**:

| Taxonomy | Terms | Roots | Max depth |
|---|---|---|---|
| Data Categories | 85 | 2 (`system`, `user`) | 4 |
| Data Uses | 55 | 12 | 4 |
| Data Subjects | 15 | 15 (flat) | 1 |

Each term is `fides_key`, `name`, `description`, `parent_key`. The hierarchy is
*also* encoded in the key itself (`user.contact.email`), which is a useful
redundancy — `fetch_taxonomy.py` asserts the two agree.

Note the upstream model also carries `version_added`, `version_deprecated`,
`replaced_by`, `is_default`, `tags`. We currently drop deprecated terms and
discard the rest. See open items.

## 3. Design decisions worth keeping

**Single file, no CDN, no server.** `index.html` opens from `file://`. Data is
inlined at build time rather than `fetch()`ed, because `fetch()` on `file://` is
blocked by CORS in every browser. Don't "improve" this into a fetch without also
adding a dev server.

**No chart library.** The arc math is ~40 lines (`arcPath`, `layout`). Pulling in
D3 would add ~280 KB inline for `d3.partition` + `d3.arc`, both of which are
small. If the chart grows transitions and brushing, revisit — but the current
trade is deliberate.

**Wedge size = leaf count, not term count.** Every leaf weighs 1; a node's angle
is the sum of its leaves. This matches how the IAB sunburst reads and keeps deep
narrow branches visible. Switching to "every term weighs 1" would fatten shallow
branches — easy change, in `build()`.

**Hue seeding is adaptive.** The naive rule (hue = top-level branch) fails on
Data Categories, which has only two roots — `user` holds 66 of 68 leaves, so the
whole chart came out one color. `build()` instead walks down to the first level
with ≥3 children and seeds hues there; rings above the seed level are grey.
Data Categories seeds at depth 2, Data Uses at depth 1.

**Palette is validated, not eyeballed.** Eight muted slate/blue slots
(max OKLCH chroma 0.085), replacing an earlier vivid 8-hue palette on
2026-11-20 because it read as busy. With hue nearly constant, branches are told
apart by **lightness**: slots are ordered dark/light/dark/… so neighbours in a
ring always differ. `scripts/palette.py` generates and checks them — worst
adjacent-slot ΔE (OKLab ×100) is 15.0 normal / 14.4 under deuteranopia in light
mode, 13.3 / 12.6 in dark (the old vivid palette's worst CVD ΔE was 9.1).
Hues are assigned in fixed slot order and **never cycled** — past 8 branches
(Data Uses has 12) a second, lighter *band* (+22%) of the same slots is used.
Depth is encoded by mixing toward the surface in oklab (16% per level, capped
at 50%), done in JS so label ink can be chosen per fill.

Several slots are deliberately pale (contrast vs surface down to ~1.6:1), so a
wedge is defined by its neighbours and the 2px gaps rather than against the
background — slice labels and the table view remain the relief path.

**Table view is a first-class view, not a fallback.** Same data, searchable,
and the only place the full description text is always readable.

## 4. How the rendering works

- `build(key)` — turns the flat node list into a tree under a virtual root,
  computes `depth`, `leaves`, sorts children by name, seeds colors.
- `layout(root, focus)` — assigns angular extents; `focus` spans the full
  circle. Renders at most `maxRings = 4` rings below the focus.
- `arcPath(a0,a1,r0,r1)` — SVG arc path with a small angular pad for the 2px
  gap between wedges. Has a special case for a full 360° ring.
- `ringRadii(focus)` — ring boundaries between `R0 = 92` and `RMAX = 490`
  (viewBox `-500 -500 1000 1000`). Rings above the hue seed level are thinner
  (0.55×); the ring count follows the focus subtree's height, so zooming in
  makes rings wider. Leaves extend to `RMAX` (`outerOf`).
- `render()` — rebuilds `svg.innerHTML` wholesale. Cheap enough at 85 nodes;
  if it ever feels slow, that's the thing to change first.
- `sizeChart()` — sets the SVG height to fill the viewport below the controls
  (min 480px); re-run on resize via `refit()` / `ResizeObserver`.

Labels are sized in screen pixels: `--u` (viewBox units per px) scales a 13px
font. For each wedge, both orientations are measured with canvas
`measureText` — tangential (straight text across the wedge, kept inside the
outer radius) and radial (starting where the wedge is wide enough for a line
of text). Preference: full name at 13px, then full name at 11.5px, then the
longest truncation. Ink is black or white by WCAG contrast against the fill,
which is why fills are mixed in JS (oklab) instead of CSS `color-mix()`.

*Fixed 2026-11-20:* labels used to be sized in viewBox units (≈5px on screen
in a Notion embed) and their length budget was measured along the arc while
the text was drawn along the radius.

## 5. Known gaps / rough edges

- **Zoom is instantaneous.** No tween between layouts. A rAF angle interpolation
  would make drilling in much more legible.
- **Some labels still truncate at the top level**: the five `User Contact …`
  address leaves (ring 4) and a few narrow mid-ring parents (`Observed…`,
  `Health and…`). They read in full after zooming in, and in the tooltip.
- **`maxRings = 4` silently clips.** Nothing in the UI tells you there's more
  below. Fine at depth 4; a lurking bug if the taxonomy deepens.
- **No deep linking.** Focus, taxonomy and search aren't in the URL, so you
  can't send someone a link to `user.contact`.
- **No keyboard navigation and the wedges aren't focusable.** The SVG has one
  `role="img"` label. Real a11y would need focusable paths with arrow-key
  traversal, or a parallel tree widget.
- **Search is substring-only** over key/name/description, scoped to the active
  taxonomy. Tab labels show per-taxonomy match counts as a workaround.
- **Deprecated terms are dropped silently** by `fetch_taxonomy.py`.
- **No tests.** The only guard is the assertion block in `fetch_taxonomy.py`.
- **`Object.keys(TAXONOMY)` is filtered by `__` prefix** in two places to skip
  the `__version__` key. Slightly fragile — a nested `meta` object would be
  cleaner.

## 6. Ideas worth doing next

Roughly in order of payoff:

1. **Animated zoom** — the single biggest feel improvement.
2. **URL state** (`?tax=data_use&focus=marketing.advertising&q=email`) so views
   are shareable.
3. **Deprecated / version overlay** — keep `version_added` and
   `version_deprecated` in the export, then let the chart answer "what changed
   between fideslang 2.x and 3.x". This is the thing the IAB page can't do at
   all, and probably the most genuinely useful feature here.
4. **Swap in Tunnl brand colors** — the palette slots are CSS custom properties
   (`--s1`…`--s8`) at the top of `src/shell.html`. Generate and validate any
   replacement with `scripts/palette.py` rather than picking by eye.
5. **Overlay our own coverage** — join an internal mapping of which Tunnl data
   elements map to which `fides_key`, and shade covered vs. uncovered branches.
   That turns this from a reference viewer into an actual gap analysis.
6. **Alternate layouts** — icicle and radial tree, matching the other two images
   on the IAB page. The tree build is already layout-agnostic.
7. **Export** — PNG/SVG download of the current view for dropping into decks.

## 7. Loose ends from the build

- Fetching `raw.githubusercontent.com/IABTechLab/fideslang/main/data_files/*.csv`
  needed an approval that didn't come through, so counts were verified against
  the PyPI package rather than diffed against the repo CSVs directly. Same
  upstream content, but the diff hasn't actually been run.
- The original `Sunburst@1x.svg` was never downloaded. If a visual side-by-side
  against the IAB version is wanted, grab it from the docs site.
