#!/usr/bin/env python3
"""own_catalog.py: generates the slot list document (own-slots.md) for custom slides (own-deck.json)

WHY: Slot keys of own:N slides are numbered in atom order, so a person cannot count keys by reading the coordinate file.
     Numbering and documenting keys with the same rules as build.js (atoms.playOwn) makes slot substitution reproducible.

Key rules (same as atoms.playOwn)
- t{k}: appearance order of atoms of kind shape or graphic that have paras
- tb{k}.r{i}c{j}: appearance order of table atoms with row and column (from 0)
- img{k}: appearance order of picture atoms
- ch{k}: appearance order of chart atoms
- "~start of original text": key matching the start of the original text (whitespace ignored)

Usage: python3 own_catalog.py <own-deck.json> <own-slots.md>
"""
import json
import sys

PREVIEW_CHARS = 30  # Characters of original text shown in the preview


def text_of(atom):
    return "\n".join("".join(r.get("t", "") for r in p.get("runs", [])) for p in (atom.get("paras") or []))


def catalog(geo):
    desc = geo.get("descriptions") or {}
    roles = geo.get("roles") or {}
    role_of = {}
    for role, nums in roles.items():
        for n in nums:
            role_of.setdefault(int(n), []).append(role)
    lines = [
        f"# Custom slide slot list ({len(geo['slides'])} slides)",
        "",
        f"- Source file: {geo.get('source', '')}",
        "- Text slots come in 2 kinds, t{k} and \"~start of original text\". The text key is recommended",
        "- Table cells are tb{k}.r{i}c{j}, images img{k}, charts ch{k}",
        "- A value of \"\" omits the box",
        "- The original text, table values and chart data shown are samples, so replace them with real content",
    ]
    for s in geo["slides"]:
        n = s["n"]
        band = s.get("band") or {}
        head = f"## own:{n}"
        if desc.get(str(n)):
            head += f" {desc[str(n)]}"
        head += f" (band mode {s.get('mode', 'full')})"
        lines += ["", head]
        if role_of.get(n):
            lines.append(f"- Roles: {', '.join(role_of[n])}")
        if band.get("headline"):
            lines.append(f"- Original headline: {band['headline']}")
        if band.get("marker"):
            lines.append(f"- Original marker: {band['marker']}")
        tk = bk = ik = ck = 0
        texts, tables, images, charts = [], [], [], []
        for a in s.get("atoms", []):
            kind = a.get("kind")
            if kind in ("shape", "graphic") and a.get("paras") is not None:
                tk += 1
                t = text_of(a).replace("\n", "\\n")
                if t.strip():
                    texts.append(f't{tk}="{t[:PREVIEW_CHARS]}"')
            elif kind == "table":
                bk += 1
                rows = a["table"]["rows"]
                tables.append(f"tb{bk} {len(rows)} rows x {max(len(r) for r in rows)} cols")
            elif kind == "image":
                ik += 1
                images.append(f"img{ik}" + (" (identifying element)" if a.get("identity") else ""))
            elif kind == "chart":
                ck += 1
                charts.append(f"ch{ck}({a['chart'].get('type', '')})")
        if tables:
            lines.append("- Tables: " + ", ".join(tables))
        if images:
            lines.append("- Image slots: " + ", ".join(images))
        if charts:
            lines.append("- Chart slots: " + ", ".join(charts))
        if texts:
            lines.append("- Text: " + " · ".join(texts))
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    geo = json.load(open(sys.argv[1], encoding="utf-8"))
    open(sys.argv[2], "w", encoding="utf-8").write(catalog(geo))
    print(sys.argv[2], len(geo["slides"]), "slides")


if __name__ == "__main__":
    main()
