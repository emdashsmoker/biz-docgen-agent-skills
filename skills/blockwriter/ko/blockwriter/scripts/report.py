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
# python-hwpx는 다음 major에서 지울 API를 DeprecationWarning으로 예고하므로 이 경고만 보이게 둔다
warnings.filterwarnings("default", category=DeprecationWarning, message=r".*hwpx")

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
    if a.toc_scope and not a.toc:
        sys.exit(msg("err_toc_scope_alone"))
    a.toc_scope = M.parse_toc_kinds(a.toc_scope, C.TOC_SCOPE_KINDS, "--toc-scope") if a.toc_scope else C.TOC_SCOPE_DEFAULT
    if ext == ".hwpx":
        import hwpx_writer
        hwpx_writer.build_hwpx(a, elems, footnotes, out)
    else:
        if a.profile not in FORMS or a.skeleton:
            sys.exit(msg("err_docx_builtin_only"))
        import docx_writer
        docx_writer.build_docx(a, elems, footnotes, out)
    if a.footnote_merge:
        print(msg("build_ok_merged", out=out, n=len(elems), fn=count_footnotes(out), merged=count_merged_notes(out)))
    else:
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


def count_merged_notes(path: str) -> int:
    """산출 파일에서 첫 각주 번호의 상호참조로 대체된 각주 참조 수 (출처 각주 통합)"""
    with zipfile.ZipFile(path) as z:
        if path.lower().endswith(".hwpx"):
            # 목차 쪽 참조도 같은 CROSSREF 필드이므로 참조 대상이 각주인 필드만 센다
            return sum(z.read(n).decode("utf-8").count(">TARGET_FOOTNOTE<")
                       for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        return len(re.findall(r"<w:instrText[^>]*>\s*NOTEREF\b", z.read("word/document.xml").decode("utf-8")))


def cmd_toc_static(a):
    """사후 정적화: 제출 파일에서 지정한 종류의 책갈피를 지우고 그 책갈피를 가리키는 쪽 참조를 일반 글자로 바꾼다.
    쪽번호를 갱신하지 않은 항목(자리 표시 값)은 건너뛰고 알린다. Why: 실제 쪽은 한/글과 Word만 계산함"""
    import toc_refs
    style_kinds = static_style_kinds(a.profile, toc_refs.is_docx(a.input))
    items = toc_refs.scan(a.input, style_kinds)
    if not items:
        sys.exit(msg("err_static_no_refs"))
    for it in items:   # 종류, 쪽번호 저장값, 갱신 상태, 책갈피 이름, 책갈피가 놓인 문단의 글자
        print(f"{it.kind}\t{'|'.join(it.values)}\t{msg('static_state_' + it.state.value)}\t{it.name}\t{it.text}")
    kinds = (*toc_refs.KINDS, toc_refs.OTHER)
    counts = {k: sum(it.kind == k for it in items) for k in kinds}
    print(msg("static_counts", counts=", ".join(f"{k} {n}" for k, n in counts.items() if n)))
    if not a.scope:
        print(msg("static_need_scope", all=C.STATIC_SCOPE_ALL))
        return
    wanted = set(toc_refs.KINDS) if a.scope == C.STATIC_SCOPE_ALL else set(M.parse_toc_kinds(a.scope, kinds, "--scope"))
    chosen = [it for it in items if it.kind in wanted]
    targets = [it for it in chosen if it.state is toc_refs.RefState.UPDATED]
    skipped = [it for it in chosen if it.state is not toc_refs.RefState.UPDATED]
    if skipped:
        key = "warn_static_skipped_docx" if toc_refs.is_docx(a.input) else "warn_static_skipped_hwpx"
        print(msg(key, n=len(skipped), items=", ".join(it.name for it in skipped)))
    if not targets:
        print(msg("static_none"))
        return
    stem, ext = os.path.splitext(a.input)
    out = a.output or f"{stem}{C.STATIC_SUFFIX}{ext}"
    if os.path.abspath(out) == os.path.abspath(a.input):
        sys.exit(msg("err_static_same_path"))
    toc_refs.make_static(a.input, out, {it.name for it in targets})
    print(msg("static_ok", out=out, done=len(targets), skipped=len(skipped), kept=len(toc_refs.scan(out, style_kinds))))


def static_style_kinds(profile_spec: str, docx: bool) -> dict[str, str]:
    """문단 스타일 이름 → 목차 항목 종류. HWPX는 프로파일의 스타일 이름, DOCX는 조판기가 만든 Word 스타일 이름"""
    if not docx:
        import hwpx_writer
        profile = hwpx_writer.load_profile(profile_spec)
        return {profile[role]: kind for role, kind in C.STATIC_STYLE_ROLES.items() if profile.get(role)}
    import docx_writer
    return docx_writer.style_kinds(profile_spec)


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
    b.add_argument("--footnote-merge", choices=list(C.NOTE_MERGE_SCOPES),
                   help="출처 각주 통합 (기본 OFF): 범위 안에서 문구가 같은 각주를 첫 각주 번호의 상호참조로 대체. "
                        "범위: square=□, section=절(##), chapter=장(#), document=문서 전체")
    b.add_argument("--toc", action="store_true",
                   help="문서 앞에 목차 삽입 (기본 OFF). --page-number와 함께 켜면 수록 항목마다 책갈피를 붙이고 쪽번호를 쪽 참조 필드로 기록")
    b.add_argument("--toc-scope", help=f"목차 수록 범위 (쉼표 구분, 기본 {','.join(C.TOC_SCOPE_DEFAULT)}). "
                                       f"항목: {', '.join(C.TOC_SCOPE_KINDS)}. table과 figure는 번호 캡션이 붙은 표와 그림")
    b.add_argument("--page-number", action="store_true", help="꼬리말 가운데 쪽번호 '- N -' (기본 OFF)")
    b.add_argument("--cover", help='표지 (기본 OFF): "title=제목;subtitle=부제;date=작성 연월;org=기관명"')
    b.add_argument("--header", help='머리말 (기본 OFF): "텍스트;align=LEFT|CENTER|RIGHT"')
    b.add_argument("--merge", default="auto", choices=["auto", "explicit", "none"],
                   help="셀 병합: auto=선행 라벨 열 연속 동일값과 '^' '<' 지시(기본), explicit=지시만, none=병합 없음")
    b.add_argument("--numbered-square", action="store_true", help="'□ 1. 제목' 줄을 글머리 없는 숫자 헤더로 출력")
    b.add_argument("--labels", help="다른 언어 문서용 라벨 JSON: 번호 형식, 목차 제목, 캡션 라벨, 추가 원고 표기 토큰, "
                                    "언어 태그 (기본: 한국어 라벨)")
    b.set_defaults(func=cmd_build)

    ts = sub.add_parser("toc-static", help="산출 이후 정적화: 지정한 항목의 책갈피를 지우고 목차 쪽번호를 일반 글자로 바꾼 사본 생성")
    ts.add_argument("input", help="한/글 또는 Word에서 쪽번호를 갱신하여 저장한 hwpx 또는 docx")
    ts.add_argument("--scope", help=f"정적화할 항목 종류 (쉼표 구분 또는 {C.STATIC_SCOPE_ALL}). 생략하면 항목 현황만 출력")
    ts.add_argument("-o", "--output", help=f"산출 경로 (기본: 원본 이름에 {C.STATIC_SUFFIX} 접미)")
    ts.add_argument("--profile", default="chapter", help="스타일 이름으로 항목 종류를 판별할 프로파일 (chapter | flat | 프로파일 JSON)")
    ts.set_defaults(func=cmd_toc_static)

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
