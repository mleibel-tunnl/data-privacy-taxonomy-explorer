#!/usr/bin/env python3
"""Inline data/fides_taxonomy.json into src/shell.html -> index.html.

index.html is a generated artifact: edit src/shell.html, never index.html.
The whole point of the inline step is that the result opens from file:// with
no server and no network — don't replace it with a fetch().

    python scripts/build.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SHELL = ROOT / "src" / "shell.html"
DATA = ROOT / "data" / "fides_taxonomy.json"
OUT = ROOT / "index.html"

PLACEHOLDER = "<script>/*DATA*/</script>"


def main() -> None:
    shell = SHELL.read_text()
    if PLACEHOLDER not in shell:
        raise SystemExit(f"{SHELL} is missing the {PLACEHOLDER} placeholder")

    data = json.loads(DATA.read_text())
    blob = "const TAXONOMY = " + json.dumps(data, separators=(",", ":")) + ";"
    OUT.write_text(shell.replace(PLACEHOLDER, f"<script>\n{blob}\n</script>"))

    kb = OUT.stat().st_size / 1024
    terms = sum(len(v["nodes"]) for k, v in data.items() if not k.startswith("__"))
    print(f"wrote {OUT} ({kb:.1f} KB, {terms} terms, fideslang {data['__version__']})")


if __name__ == "__main__":
    main()
