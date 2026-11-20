#!/usr/bin/env python3
"""Export the Fideslang default taxonomy to data/fides_taxonomy.{json,csv}.

Source of truth is the `fideslang` PyPI package, which ships the same content as
IABTechLab/fideslang -> data_files/. Re-run after bumping the pin in
requirements.txt to pick up taxonomy changes.

    pip install -r requirements.txt
    python scripts/fetch_taxonomy.py
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import fideslang
from fideslang import DEFAULT_TAXONOMY

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# attribute on DEFAULT_TAXONOMY -> (display label, subtitle shown in the UI)
TAXONOMIES = {
    "data_category": ("Data Categories", "What kind of data it is"),
    "data_use": ("Data Uses", "What the data is used for"),
    "data_subject": ("Data Subjects", "Whose data it is"),
}

# Deprecated terms are dropped. Flip to True to keep them (they'd need a visual
# treatment in the sunburst — strikethrough label or a muted fill).
INCLUDE_DEPRECATED = False


def collect() -> dict:
    out: dict = {"__version__": getattr(fideslang, "__version__", "unknown")}
    for attr, (label, subtitle) in TAXONOMIES.items():
        nodes = []
        for item in getattr(DEFAULT_TAXONOMY, attr):
            d = item.model_dump()
            if d.get("version_deprecated") and not INCLUDE_DEPRECATED:
                continue
            nodes.append(
                {
                    "key": d["fides_key"],
                    "name": d.get("name") or d["fides_key"],
                    "description": (d.get("description") or "").strip(),
                    "parent": d.get("parent_key"),
                }
            )
        out[attr] = {"label": label, "subtitle": subtitle, "nodes": nodes}
    return out


def validate(data: dict) -> None:
    """Cheap integrity gate — catches an upstream rename before it ships."""
    for attr, block in data.items():
        if attr.startswith("__"):
            continue
        nodes = block["nodes"]
        keys = {n["key"] for n in nodes}
        assert len(keys) == len(nodes), f"{attr}: duplicate fides_key"
        orphans = [n["key"] for n in nodes if n["parent"] and n["parent"] not in keys]
        assert not orphans, f"{attr}: parent_key missing from taxonomy: {orphans}"
        mismatch = [
            n["key"]
            for n in nodes
            if n["parent"] and not n["key"].startswith(n["parent"] + ".")
        ]
        assert not mismatch, f"{attr}: key is not prefixed by its parent: {mismatch}"
        roots = sum(1 for n in nodes if not n["parent"])
        print(f"  {attr:<14} {len(nodes):>3} terms, {roots:>2} root(s)")


def main() -> None:
    DATA.mkdir(exist_ok=True)
    data = collect()
    print(f"fideslang {data['__version__']}")
    validate(data)

    (DATA / "fides_taxonomy.json").write_text(json.dumps(data, indent=1))

    with (DATA / "fides_taxonomy.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["taxonomy", "fides_key", "name", "parent_key", "depth", "description"])
        for attr, block in data.items():
            if attr.startswith("__"):
                continue
            for n in block["nodes"]:
                w.writerow(
                    [attr, n["key"], n["name"], n["parent"] or "",
                     n["key"].count("."), n["description"]]
                )

    print(f"wrote {DATA/'fides_taxonomy.json'} and {DATA/'fides_taxonomy.csv'}")


if __name__ == "__main__":
    main()
