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

**Palette is validated, not eyeballed.** Eight categorical hues from a palette
checked for colorblind separation (worst adjacent CVD ΔE 9.1, normal-vision ΔE
19.6) and a lightness band. Hues are assigned in fixed slot order and **never
cycled** — past 8 branches (Data Uses has 12) a second, lighter *band* of the
same hues is used, so the same hue+shade never repeats in one ring. Depth is
encoded by mixing toward the surface color via `color-mix(in oklab, …)`.

Three of the light-mode hues sit under 3:1 contrast against the surface, which
is why slice labels and the table view are both non-negotiable — they're the
relief path for anyone who can't separate the fills.

**Table view is a first-class view, not a fallback.** Same data, searchable,
and the only place the full description text is always readable.

## 4. How the rendering works

- `build(key)` — turns the flat node list into a tree under a virtual root,
  computes `depth`, `leaves`, sorts children by name, seeds colors.
- `layout(root, focus)` — assigns angular extents; `focus` spans the full
  circle. Renders at most `maxRings = 4` rings below the focus.
- `arcPath(a0,a1,r0,r1)` — SVG arc path with a small angular pad for the 2px
  gap between wedges. Has a special case for a full 360° ring.
- `render()` — rebuilds `svg.innerHTML` wholesale. Cheap enough at 85 nodes;
  if it ever feels slow, that's the thing to change first.
- Geometry constants: `R0 = 118` (hub radius), `RW = 92` (ring width), viewBox
  `-500 -500 1000 1000`.

Labels are drawn only when `span * midRadius >= 34` px of arc, rotated to the
wedge, flipped on the left half, and truncated to a character budget derived
from arc length. Everything else relies on the hover tooltip.

## 5. Known gaps / rough edges

- **Zoom is instantaneous.** No tween between layouts. A rAF angle interpolation
  would make drilling in much more legible.
- **Outer-ring labels truncate hard** (`User C…`, five of them in a row under
  Contact Data). Needs either a leader-line treatment, a radial label outside the
  ring, or dropping labels past ring 3 entirely.
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
   (`--s1`…`--s8`) at the top of `src/shell.html`. Any replacement should be
   re-validated for CVD separation rather than picked by eye.
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
