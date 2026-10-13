#!/usr/bin/env python3
"""md2storyboard.py: 계층 표기 Markdown 원고 → storyboard.json 초안 (일반 발표자료, 보고서형 PPT 경로)
사용: python3 md2storyboard.py <원고.md> <storyboard.json> [--kind report|brief|general] [--layout 16:9] [--title 제목] [--company 제안사] [--max 슬라이드수]
규칙
- "# 제목"        장(chapter). 간지 슬라이드 1장 생성, 우측 장 추적기 텍스트로 사용
- "## 절"         슬라이드 1장. 절 제목이 헤더 좌측, 첫 문장(">" 인용 또는 첫 불릿)이 헤드라인 후보
- "### 소제목"    같은 슬라이드 안의 패널(최대 4개). 초과 시 슬라이드 분할
- "- 항목"        패널 불릿. "    + 항목" 은 하위 불릿
- 표(| a | b |)  table 템플릿으로 분리 (표 1개 = 슬라이드 1장, 불릿이 없는 절은 표 슬라이드만 생성)
- "> 출처 ..."   source 필드 ("> Source ..." 도 같음). 괄호가 든 인용 줄도 출처로 보되 절 첫머리 인용은 헤드라인 후보
- 헤드라인은 "**...**" 굵은 한 줄 또는 절 첫 불릿을 사용하고, 없으면 절 제목을 [확인 필요] 표기로 임시 배치 (lint 경고로 표시)
보고서형(--kind report)은 절 1개 = 슬라이드 1장을 유지하고 패널 상한 5개
브리핑 덱(--kind brief)은 장 1개 = 슬라이드 1장으로 묶고 패널 상한 3개, --max 로 총 장수 상한 지정
산출물은 초안 골격이며 헤드라인 재작성과 시각화 교체를 거쳐 완성
"""
import json
import re
import sys
from pathlib import Path

# 장 번호 로마 숫자. 나눔고딕이 글리프를 갖는 Ⅰ-Ⅹ 까지 쓰고 11번째 장부터는 아라비아 숫자
ROMAN = ["Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ"]


def parse_table(lines):
    rows = [[c.strip() for c in ln.strip().strip("|").split("|")] for ln in lines if ln.strip().startswith("|") and not re.match(r"^\|?\s*-{2,}", ln.strip())]
    if not rows: return None
    return {"head": rows[0], "rows": rows[1:]}


def condense(slides, max_slides):
    """브리핑 덱: 간지를 빼고 장 1개를 슬라이드 1장으로 묶음. 상한을 넘으면 절 단위로 다시 나눔"""
    body = [s for s in slides if s["template"] != "divider"]
    by_ch = {}
    for s in body:
        by_ch.setdefault(s.get("chapter", ""), []).append(s)
    out = []
    for ch, items in by_ch.items():
        # 절 단위 패널. 항목이 적으면 카드형으로 바꿔 빈 상자를 만들지 않음
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
            # 절마다 한 줄이면 카드로 배치 (긴 빈 상자 방지)
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
        # 표만 있는 절은 표 슬라이드가 절을 맡음 (빈 본문 슬라이드를 만들지 않음). 표도 불릿도 없는 절은 확인 표기를 남겨 lint 가 잡게 함
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
            # 절 첫머리 인용은 괄호("2018-2026년(8년)")가 있어도 헤드라인 후보. 본문 뒤 괄호 인용은 "기관명(연도)" 형식의 출처
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
                if x["template"] == "divider": break  # 간지 목차는 자기 장의 절만 (다음 간지에서 멈춤)
                if x["section"] not in seen: seen.append(x["section"])
            s["slots"]["items"] = seen[:8]
    if kind == "brief":
        slides = condense(slides, max_slides)
    story = {"meta": {"title": opt.get("--title", src.stem), "kind": kind, "structure": "sections", "layout": opt.get("--layout", "16:9"), "headlineStyle": "noun", "company": opt.get("--company", "제안사")}, "slides": slides}
    dst.write_text(json.dumps(story, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{dst} slides={len(slides)} (divider {sum(1 for s in slides if s['template'] == 'divider')}, table {sum(1 for s in slides if s['template'] == 'table')})")


if __name__ == "__main__":
    main()
