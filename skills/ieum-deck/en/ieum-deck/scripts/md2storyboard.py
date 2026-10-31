#!/usr/bin/env python3
"""md2storyboard.py: hierarchical Markdown manuscript → storyboard.json draft (general deck and report-style PPT paths)
Usage: python3 md2storyboard.py <manuscript.md> <storyboard.json> [--kind report|brief|general] [--layout 16:9] [--title TITLE] [--company BIDDER] [--max SLIDES]
Rules
- "# title"       Chapter. Creates 1 divider slide and serves as the chapter tracker text on the right
- "## section"    1 slide. The section title goes left in the header, and the first sentence (">" quote or first bullet) is the headline candidate
- "### subtitle"  A panel on the same slide (up to 4). More panels split the slide
- "- item"        Panel bullet. "    + item" is a sub-bullet
- Table (| a | b |)  Split into a table template (1 table = 1 slide. A section without bullets creates only the table slide)
- "> 출처 ..."   The source field ("> Source ..." works the same). Quote lines with parentheses also count as sources, except a quote opening a section, which is a headline candidate
- The headline uses a bold "**...**" line or the section's first bullet. Otherwise the section title is placed temporarily with the [확인 필요] marker (shown as a lint warning)
Report style (--kind report) keeps 1 section = 1 slide with up to 5 panels
Briefing deck (--kind brief) groups 1 chapter = 1 slide with up to 3 panels, and --max caps the total slide count
The output is a draft skeleton, finished by rewriting headlines and replacing visuals
"""
import json
import re
import sys
from pathlib import Path

# Chapter Roman numerals. Uses Ⅰ-Ⅹ, which NanumGothic has glyphs for, and Arabic numerals from the 11th chapter
ROMAN = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ"]


def parse_table(lines):
    # Skip separator rows (|---|, |:---:|). Separator rows with alignment colons must not become data rows either (same test as company2slides.parse_tables)
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines if ln.strip().startswith("|") and not re.match(r"^\|?\s*:?-{2,}", ln.strip())]
    if not rows: return None
    return {"head": rows[0], "rows": rows[1:]}


def condense(slides, max_slides):
    """Briefing deck: drops dividers and groups each chapter into 1 slide. Splits by section again past the limit"""
    body = [s for s in slides if s["template"] != "divider"]
    by_ch = {}
    for s in body:
        by_ch.setdefault(s.get("chapter", ""), []).append(s)
    out = []
    for ch, items in by_ch.items():
        # Panels per section. With few items, switch to cards to avoid empty boxes
        title = ch.split(". ", 1)[-1] if ". " in ch else ch
        panels = []
        for s in items:
            merged = [x for p in (s.get("panels") or []) for x in (p.get("items") or [])] or (s.get("items") or [])
            if merged:
                panels.append({"head": s.get("section") or title, "items": merged[:3]})
        panels = panels[:3]
        head = items[0]
        base = {"id": f"S{len(out) + 1:03d}", "chapter": ch, "secNo": f"{len(out) + 1}.", "section": title,
                "headline": head.get("headline") or f"[확인 필요] {title} 결론 1문장", "marker": title}
        total = sum(len(p["items"]) for p in panels)
        if panels and total <= len(panels) * 1:
            # One line per section goes to cards (prevents long empty boxes)
            base.update({"template": "cards", "slots": {"cards": [{"title": p["head"], "text": p["items"][0] if p["items"] else ""} for p in panels]}})
        else:
            base.update({"template": "bullets", "panels": panels})
        out.append(base)
    if max_slides and len(out) > max_slides:
        out = out[:max_slides]
    for k, s in enumerate(out, 1):
        s["id"] = f"S{k:03d}"
        s["secNo"] = f"{k}."
    return out


def main():
    args = sys.argv[1:]
    if len(args) < 2: raise SystemExit(__doc__)
    src, dst = Path(args[0]), Path(args[1])
    opt = {k: args[args.index(k) + 1] for k in ("--kind", "--layout", "--title", "--company", "--max") if k in args}
    kind = opt.get("--kind", "general")
    panel_max = 5 if kind == "report" else 3 if kind == "brief" else 4
    max_slides = int(opt["--max"]) if "--max" in args else (12 if kind == "brief" else 0)
    lines = src.read_text(encoding="utf-8").splitlines()
    slides, chapter, sec_no, ch_no = [], "", 0, 0
    cur = None

    def flush():
        nonlocal cur
        if not cur: return
        panels = [p for p in (cur["panels"] or [{"head": None, "items": cur["items"]}]) if p["items"] or p["head"]]
        if not cur["headline"]:
            cur["headline"] = f"[확인 필요] {cur['section']}"
        # A section with only tables is carried by its table slides (no empty body slide). A section with neither tables nor bullets keeps a check marker so lint catches it
        if not panels and not cur["tables"]:
            panels = [{"head": None, "items": [f"[확인 필요] {cur['section']} 내용"]}]
        for i in range(0, len(panels), panel_max):
            chunk = panels[i:i + panel_max]
            slides.append({"id": f"S{len(slides) + 1:03d}", "template": "bullets", "chapter": chapter, "secNo": f"{sec_no}.", "section": cur["section"],
                           "headline": cur["headline"], "marker": cur["marker"] or cur["section"], "panels": [{"head": p["head"], "items": p["items"]} for p in chunk], "source": cur["source"] or None})
        for tb in cur["tables"]:
            slides.append({"id": f"S{len(slides) + 1:03d}", "template": "table", "chapter": chapter, "secNo": f"{sec_no}.", "section": cur["section"], "headline": cur["headline"], "marker": cur["marker"] or cur["section"], "slots": tb, "source": cur["source"] or None})
        cur = None

    i = 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("# "):
            flush(); ch_no += 1; sec_no = 0
            chapter = f"{ROMAN[ch_no - 1] if ch_no <= len(ROMAN) else ch_no}. {ln[2:].strip()}"
            slides.append({"id": f"S{len(slides) + 1:03d}", "template": "divider", "slots": {"no": chapter.split(".")[0], "title": ln[2:].strip(), "items": []}})
        elif ln.startswith("## "):
            flush(); sec_no += 1
            cur = {"section": ln[3:].strip(), "headline": "", "marker": "", "panels": [], "items": [], "tables": [], "source": []}
        elif ln.startswith("### ") and cur is not None:
            cur["panels"].append({"head": ln[4:].strip(), "items": []})
        elif ln.strip().startswith("|") and cur is not None:
            j = i
            while j < len(lines) and lines[j].strip().startswith("|"): j += 1
            tb = parse_table(lines[i:j])
            if tb: cur["tables"].append(tb)
            i = j; continue
        elif ln.startswith("> ") and cur is not None:
            q = ln[2:].strip()
            # A quote opening a section is a headline candidate even with parentheses ("2018-2026년(8년)"). A parenthesized quote after body text is a source in the "기관명(연도)" format
            lead = not cur["headline"] and not (cur["items"] or cur["panels"] or cur["tables"])
            if re.match(r"(출처|[Ss]ources?\b)", q) or ("(" in q and not lead): cur["source"].append(q)
            elif not cur["headline"]: cur["headline"] = q
        elif re.match(r"^\*\*.+\*\*\s*$", ln.strip()) and cur is not None and not cur["headline"]:
            cur["headline"] = ln.strip().strip("*").strip()
        elif re.match(r"^\s*[-*] ", ln) and cur is not None:
            text = re.sub(r"^\s*[-*] ", "", ln).strip()
            target = cur["panels"][-1]["items"] if cur["panels"] else cur["items"]
            target.append(text)
        elif re.match(r"^\s+\+ ", ln) and cur is not None:
            text = re.sub(r"^\s+\+ ", "", ln).strip()
            target = cur["panels"][-1]["items"] if cur["panels"] else cur["items"]
            if target and isinstance(target[-1], str): target[-1] = {"text": target[-1], "sub": [text]}
            elif target: target[-1]["sub"].append(text)
        i += 1
    flush()
    for k, s in enumerate(slides):
        if s["template"] == "divider":
            seen = []
            for x in slides[k + 1:]:
                if x["template"] == "divider": break  # A divider lists only its own chapter's sections (stops at the next divider)
                if x["section"] not in seen: seen.append(x["section"])
            s["slots"]["items"] = seen[:8]
    if kind == "brief":
        slides = condense(slides, max_slides)
    story = {"meta": {"title": opt.get("--title", src.stem), "kind": kind, "structure": "sections", "layout": opt.get("--layout", "16:9"), "headlineStyle": "noun", "company": opt.get("--company", "제안사")}, "slides": slides}
    dst.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{dst} slides={len(slides)} (divider {sum(1 for s in slides if s['template'] == 'divider')}, table {sum(1 for s in slides if s['template'] == 'table')})")


if __name__ == "__main__":
    main()
