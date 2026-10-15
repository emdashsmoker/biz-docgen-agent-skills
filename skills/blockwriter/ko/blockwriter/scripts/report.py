#!/usr/bin/env python3
"""blockwriter CLI: Markdown 원고 1개를 HWPX 또는 DOCX 보고서로 조판하고 검수한다.

명령
  build     원고.md → 문서.hwpx | 문서.docx   (확장자로 형식 결정)
  form      내장 양식(chapter, flat)을 빈 HWPX 파일로 저장
  skeleton  유저 양식.hwpx → 스켈레톤.hwpx + 프로파일 초안
  export    문서.hwpx → 원고.md
  fill      문서.hwpx + 치환.json → 문서
  render    문서(.hwpx, .docx) → PDF + 쪽 PNG
  check     문서 구조 검증
  docx2md   DOCX → 원고.md (2단계)
  xlsx2md   XLSX → 원고.md
  fonts     양식 글꼴의 설치 상태 확인, --setup 시 대체 글꼴 설정

본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
한/글, 한컴오피스, HWPX는 한글과컴퓨터의 상표이며 이 도구는 한글과컴퓨터와 제휴 관계가 없는 독립 도구임
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import warnings
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
warnings.filterwarnings("ignore", category=DeprecationWarning)

import config as C  # noqa: E402
import manuscript as M  # noqa: E402
from config import msg  # noqa: E402
from form import FORMS  # noqa: E402


def cmd_build(a):
    ext = os.path.splitext(a.output or "")[1].lower() if a.output else "." + a.format
    if ext not in (".hwpx", ".docx"):
        sys.exit(msg("err_format"))
    out = a.output or os.path.splitext(a.input)[0] + ext
    if a.labels:   # 다른 언어 문서의 라벨. 원고 표기 토큰을 추가하므로 원고 해석 전에 읽음
        C.set_labels(a.labels)
        M.compile_notation()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)   # 저장 시점의 폴더 없음 오류 방지
    elems, footnotes = M.parse_markdown(a.input)
    for issue in M.lint(elems, footnotes):   # LINT는 원고를 고쳐 해소
        print("LINT:", issue)
    # HITL은 유저가 고르는 조판 선택지. 옵션으로 이미 고른 항목은 알리지 않음
    for notice in M.hitl_notices(elems, ask_page_break=a.page_break is None, ask_long_table=a.long_table is None):
        print("HITL:", notice)
    a.page_break = a.page_break or C.DEFAULT_PAGE_BREAK
    a.long_table = a.long_table or C.DEFAULT_LONG_TABLE
    if ext == ".hwpx":
        import hwpx_writer
        hwpx_writer.build_hwpx(a, elems, footnotes, out)
    else:
        if a.profile not in FORMS or a.skeleton:
            sys.exit(msg("err_docx_builtin_only"))
        import docx_writer
        docx_writer.build_docx(a, elems, footnotes, out)
    print(msg("build_ok", out=out, n=len(elems), fn=count_footnotes(out)))


def count_footnotes(path: str) -> int:
    """산출 파일에 들어간 각주 수. 원고의 [^n] 각주와 출처 줄에서 옮긴 각주를 모두 센다."""
    with zipfile.ZipFile(path) as z:
        if path.lower().endswith(".hwpx"):
            return sum(len(re.findall(r"<hp:footNote\b", z.read(n).decode("utf-8")))
                       for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        if "word/footnotes.xml" not in z.namelist():
            return 0
        # 구분선용 각주(w:type 지정)를 뺀 본문 각주
        return len(re.findall(r"<w:footnote\b(?![^>]*w:type=)", z.read("word/footnotes.xml").decode("utf-8")))


def cmd_form(a):
    from hwpx_form import write_skeleton
    write_skeleton(FORMS[a.form], a.output)
    print(msg("builtin_ok", form=a.form, out=a.output))


def cmd_skeleton(a):
    import hwpx_writer
    hwpx_writer.skeleton_from_template(a.input, a.output, a.section)


def cmd_export(a):
    import convert
    convert.hwpx_to_md(a.input, a.output, a.profile, a.image_dir)


def cmd_fill(a):
    import hwpx_writer
    hwpx_writer.fill(a.input, a.mapping, a.output)


def cmd_render(a):
    import render
    render.render(a.input, a.outdir, a.dpi, a.engine, a.rhwp, a.keep_soft_hyphen)


def cmd_check(a):
    if a.input.lower().endswith(".docx"):
        import docx_writer
        sys.exit(1 if docx_writer.check_docx(a.input) else 0)
    import hwpx_writer
    sys.exit(1 if hwpx_writer.check(a.input, a.expect) else 0)


def cmd_docx2md(a):
    import convert
    convert.docx_to_md(a.input, a.output, a.map)


def cmd_xlsx2md(a):
    import convert
    convert.xlsx_to_md(a.input, a.output, a.allow_wide)


def cmd_fonts(a):
    import render
    faces = sorted({f for form in FORMS.values() for st in form.styles for f in st.char.faces}
                   | {f for form in FORMS.values() for f in form.default_char.faces})
    if a.setup:
        render.fonts_setup()
    render.fonts_report(faces)


def main():
    ap = argparse.ArgumentParser(description="blockwriter CLI", epilog=C.NOTICE[C.LANG],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="원고.md → 문서.hwpx | 문서.docx")
    b.add_argument("input")
    b.add_argument("output", nargs="?")
    b.add_argument("--format", choices=["hwpx", "docx"], default="hwpx", help="산출 경로를 생략할 때의 형식")
    b.add_argument("--profile", required=True,
                   help="chapter | flat | 프로파일 JSON. 두 양식은 번호와 글꼴 체계가 달라 기본값을 두지 않음")
    b.add_argument("--skeleton", help="유저 양식에서 추출한 스켈레톤 hwpx (HWPX 전용, 기본은 내장 양식 생성)")
    b.add_argument("--page-break", choices=["chapter", "section", "none"],
                   help="새 쪽 시작 단위: chapter=장마다(기본), section=장과 절마다, none=이어 쓰기")
    b.add_argument("--long-table", choices=["engine", "split"],
                   help=f"{C.LONG_TABLE_ROWS}행 초과 표: engine=쪽 경계 분할과 제목행 반복(기본), split=청크별 표로 물리 분할")
    b.add_argument("--toc", action="store_true", help="문서 앞에 목차 삽입 (기본 OFF)")
    b.add_argument("--toc-depth", type=int, default=2, choices=[1, 2, 3], help="목차 깊이: 1=장, 2=절(기본), 3=소절")
    b.add_argument("--page-number", action="store_true", help="꼬리말 가운데 쪽번호 '- N -' (기본 OFF)")
    b.add_argument("--cover", help='표지 (기본 OFF): "title=제목;subtitle=부제;date=작성 연월;org=기관명"')
    b.add_argument("--header", help='머리말 (기본 OFF): "텍스트;align=LEFT|CENTER|RIGHT"')
    b.add_argument("--merge", default="auto", choices=["auto", "explicit", "none"],
                   help="셀 병합: auto=선행 라벨 열 연속 동일값과 '^' '<' 지시(기본), explicit=지시만, none=병합 없음")
    b.add_argument("--rhwp", help="목차 쪽번호 산정에 쓸 rhwp 경로")
    b.add_argument("--numbered-square", action="store_true", help="'□ 1. 제목' 줄을 글머리 없는 숫자 헤더로 출력")
    b.add_argument("--labels", help="다른 언어 문서용 라벨 JSON: 번호 형식, 목차 제목, 캡션 라벨, 추가 원고 표기 토큰, "
                                    "언어 태그 (기본: 한국어 라벨)")
    b.set_defaults(func=cmd_build)

    f = sub.add_parser("form", help="내장 양식을 빈 HWPX 파일로 저장")
    f.add_argument("form", choices=sorted(FORMS))
    f.add_argument("output")
    f.set_defaults(func=cmd_form)

    s = sub.add_parser("skeleton", help="유저 양식.hwpx → 스켈레톤 + 프로파일 초안")
    s.add_argument("input")
    s.add_argument("output")
    s.add_argument("--section", type=int, help="본문 구역 번호 (기본 마지막 구역)")
    s.set_defaults(func=cmd_skeleton)

    e = sub.add_parser("export", help="문서.hwpx → 원고.md")
    e.add_argument("input")
    e.add_argument("output", nargs="?")
    e.add_argument("--image-dir")
    e.add_argument("--profile", help="지정 시 스타일 이름을 역할로 역대응하여 계위 원고로 복원 (chapter | flat | JSON)")
    e.set_defaults(func=cmd_export)

    fl = sub.add_parser("fill", help='치환 JSON {"replace": {...}, "cells": {"라벨 > right": "값"}}')
    fl.add_argument("input")
    fl.add_argument("mapping")
    fl.add_argument("-o", "--output")
    fl.set_defaults(func=cmd_fill)

    r = sub.add_parser("render", help="문서 → PDF + 쪽 PNG")
    r.add_argument("input")
    r.add_argument("--outdir")
    r.add_argument("--dpi", type=int, default=C.RENDER_DPI)
    r.add_argument("--rhwp")
    r.add_argument("--keep-soft-hyphen", action="store_true", help="HWPX 검수 사본 치환 없이 원본 그대로 렌더")
    r.add_argument("--engine", default="auto", choices=["auto", "rhwp", "soffice"],
                   help="HWPX: auto=rhwp 우선, 없으면 LibreOffice+H2Orestart. DOCX는 항상 LibreOffice")
    r.set_defaults(func=cmd_render)

    c = sub.add_parser("check", help="구조 검증 (HWPX: 스키마, 이미지 매니페스트, rhwp verify / DOCX: 구성 요약)")
    c.add_argument("input")
    c.add_argument("--expect", default="", help='rhwp verify 인자 예: "--expect-min-tables 2"')
    c.set_defaults(func=cmd_check)

    d = sub.add_parser("docx2md", help="DOCX → 원고.md (1단계: 문단 유형 출력, 2단계: --map JSON으로 변환)")
    d.add_argument("input")
    d.add_argument("output", nargs="?")
    d.add_argument("--map", help="계위 대응 JSON 경로")
    d.set_defaults(func=cmd_docx2md)

    x = sub.add_parser("xlsx2md", help="XLSX → 원고.md (시트마다 파이프 표)")
    x.add_argument("input")
    x.add_argument("output", nargs="?")
    x.add_argument("--allow-wide", action="store_true")
    x.set_defaults(func=cmd_xlsx2md)

    fo = sub.add_parser("fonts", help="양식 글꼴 설치 상태. --setup: 대체 글꼴 내려받기와 대체 규칙 기록")
    fo.add_argument("--setup", action="store_true")
    fo.set_defaults(func=cmd_fonts)

    a = ap.parse_args()
    # 입력 파일 확인. 없으면 이후 단계가 변환 실패 등 원인과 다른 오류를 냄
    if getattr(a, "input", None) and not os.path.exists(a.input):
        sys.exit(msg("err_no_input", path=a.input))
    a.func(a)


if __name__ == "__main__":
    main()
