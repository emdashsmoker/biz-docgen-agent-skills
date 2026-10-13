#!/usr/bin/env python3
"""own_catalog.py: 커스텀 슬라이드(own-deck.json)의 슬롯 목록 문서(own-slots.md) 생성

WHY: own:N 슬라이드의 슬롯 키는 원자 순서로 매겨지므로 사람이 좌표 파일을 읽고 키를 셀 수 없다.
     build.js(atoms.playOwn)와 같은 규칙으로 키를 매겨 문서화해야 슬롯 치환이 재현된다.

키 규칙 (atoms.playOwn 와 동일)
- t{k}: 종류가 shape 또는 graphic 이고 paras 가 있는 원자의 출현 순서
- tb{k}.r{i}c{j}: 표 원자의 출현 순서와 행, 열 (0 부터)
- img{k}: 그림 원자의 출현 순서
- ch{k}: 차트 원자의 출현 순서
- "~원문 앞부분": 텍스트 원문의 앞부분 일치 키 (공백 무시)

사용: python3 own_catalog.py <own-deck.json> <own-slots.md>
"""
import json
import sys

PREVIEW_CHARS = 30  # 원문 미리보기 글자 수


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
        f"# 커스텀 슬라이드 슬롯 목록 ({len(geo['slides'])}장)",
        "",
        f"- 원본 파일: {geo.get('source', '')}",
        "- 텍스트 슬롯은 t{k} 와 \"~원문 앞부분\" 의 2종이며 원문 키를 권장",
        "- 표 셀은 tb{k}.r{i}c{j}, 이미지는 img{k}, 차트는 ch{k}",
        "- 값을 \"\" 로 주면 해당 상자를 생략",
        "- 표시된 원문과 표 값과 차트 데이터는 견본이므로 실제 내용으로 교체",
    ]
    for s in geo["slides"]:
        n = s["n"]
        band = s.get("band") or {}
        head = f"## own:{n}"
        if desc.get(str(n)):
            head += f" {desc[str(n)]}"
        head += f" (밴드 모드 {s.get('mode', 'full')})"
        lines += ["", head]
        if role_of.get(n):
            lines.append(f"- 역할: {', '.join(role_of[n])}")
        if band.get("headline"):
            lines.append(f"- 헤드라인 원문: {band['headline']}")
        if band.get("marker"):
            lines.append(f"- 마커 원문: {band['marker']}")
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
                tables.append(f"tb{bk} {len(rows)}행x{max(len(r) for r in rows)}열")
            elif kind == "image":
                ik += 1
                images.append(f"img{ik}" + (" (식별 요소)" if a.get("identity") else ""))
            elif kind == "chart":
                ck += 1
                charts.append(f"ch{ck}({a['chart'].get('type', '')})")
        if tables:
            lines.append("- 표: " + ", ".join(tables))
        if images:
            lines.append("- 이미지 슬롯: " + ", ".join(images))
        if charts:
            lines.append("- 차트 슬롯: " + ", ".join(charts))
        if texts:
            lines.append("- 텍스트: " + " · ".join(texts))
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    geo = json.load(open(sys.argv[1], encoding="utf-8"))
    open(sys.argv[2], "w", encoding="utf-8").write(catalog(geo))
    print(sys.argv[2], len(geo["slides"]), "slides")


if __name__ == "__main__":
    main()
