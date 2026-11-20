# Data Privacy Taxonomy Explorer

An interactive sunburst over the [Fideslang](https://github.com/IABTechLab/fideslang)
privacy taxonomy — Data Categories, Data Uses and Data Subjects.

The IAB Tech Lab's own [Taxonomy Explorer](https://iabtechlab.github.io/fideslang/#taxonomy-explorer)
is a static SVG. This rebuilds it from the real taxonomy data as something you
can click, zoom, search and extend. See `NOTES.md` for the full background.

## Run it

Open `index.html` in a browser. That's it — no server, no network, no build step
required to *view* it. Everything (data, CSS, JS) is inlined in a single ~44 KB
file.

## Use it

- **Click a wedge** to zoom into that branch; **click the hub** to zoom out
- **Breadcrumbs** across the top jump to any ancestor
- **Tabs** switch between the three taxonomies
- **Search** dims non-matches and outlines hits; tab labels show per-taxonomy
  match counts
- **Table view** lists every term with key, parent and description
- **Light / dark** toggle, defaulting to your OS setting

## Embed it (e.g. in Notion)

Hosted on GitHub Pages at
<https://mleibel-tunnl.github.io/data-privacy-taxonomy-explorer/>. In Notion,
type `/embed` and paste a URL with `?embed` for the compact iframe layout:

| URL options | Effect |
|---|---|
| `?embed` | Hides the header, stacks the detail panel under the chart, adds an "Open full view ↗" link |
| `&tax=data_category` / `data_use` / `data_subject` | Starting taxonomy |
| `&theme=light` / `dark` | Forces a theme (an iframe follows the OS setting, not Notion's) |

Example: `https://mleibel-tunnl.github.io/data-privacy-taxonomy-explorer/?embed&tax=data_use`

Pages serves `index.html` from the root of `main`, so remember to commit the
rebuilt `index.html` after running `scripts/build.py`.

## Rebuild it

```bash
pip install -r requirements.txt
python scripts/fetch_taxonomy.py   # pull taxonomy -> data/*.json, *.csv
python scripts/build.py            # inline data into index.html
```

## Layout

```
.
├── index.html                 # GENERATED — do not edit directly
├── src/
│   └── shell.html             # the actual source: markup, CSS, chart code
├── data/
│   ├── fides_taxonomy.json    # GENERATED — nested-ready node lists per taxonomy
│   └── fides_taxonomy.csv     # GENERATED — flat: taxonomy, key, name, parent, depth, description
├── scripts/
│   ├── fetch_taxonomy.py      # fideslang -> data/
│   └── build.py               # src/shell.html + data/ -> index.html
├── NOTES.md                   # design decisions, known gaps, roadmap
└── CLAUDE.md                  # project context for Claude Code
```

Edit `src/shell.html`, then run `scripts/build.py`. `index.html` is a build
artifact and any edit to it is lost on the next build.

## Data

Built against **fideslang 3.1.4**: 85 data categories, 55 data uses, 15 data
subjects. The `fideslang` PyPI package ships the same content as
`IABTechLab/fideslang → data_files/`.

Fideslang is published by the IAB Tech Lab under Apache-2.0.
