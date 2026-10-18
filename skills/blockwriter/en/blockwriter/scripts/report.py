#!/usr/bin/env python3
"""blockwriter CLI: typesets one Markdown manuscript into an HWPX or DOCX report and checks it.

Commands
  build     manuscript.md → document.hwpx | document.docx   (format from the extension)
  form      save a built-in form (chapter, flat) as an empty HWPX file
  skeleton  user form.hwpx → skeleton.hwpx + draft profile
  export    document.hwpx → manuscript.md
  fill      document.hwpx + replacements.json → document
  render    document (.hwpx, .docx) → PDF + page PNGs
  check     document structure validation
  docx2md   DOCX → manuscript.md (2 steps)
  xlsx2md   XLSX → manuscript.md
  fonts     check installation of the form fonts; --setup configures substitute fonts

본 제품은 한컴의 HWP 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
(This product was developed with reference to Hancom's published HWP document file (.hwp) specification.)
Hangul, Hancom Office, and HWPX are trademarks of Hancom Inc. This tool is independent and not affiliated with Hancom Inc.
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
# python-hwpx announces APIs it will drop in the next major release with DeprecationWarning, so keep those visible
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
    if a.labels:   # labels for documents in another language. Read before parsing because they add manuscript tokens
        C.set_labels(a.labels)
        M.compile_notation()
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)   # avoid a missing-folder error at save time
    elems, footnotes = M.parse_markdown(a.input)
    for issue in M.lint(elems, footnotes):   # LINT is resolved by fixing the manuscript
        print("LINT:", issue)
    # HITL lines are typesetting choices for the user. Items already chosen by option are not reported
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
    """Number of footnotes in the output file, counting both [^n] footnotes and footnotes moved from source lines."""
    with zipfile.ZipFile(path) as z:
        if path.lower().endswith(".hwpx"):
            return sum(len(re.findall(r"<hp:footNote\b", z.read(n).decode("utf-8")))
                       for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        if "word/footnotes.xml" not in z.namelist():
            return 0
        # body footnotes, excluding separator footnotes (those with w:type)
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

    b = sub.add_parser("build", help="manuscript.md → document.hwpx | document.docx")
    b.add_argument("input")
    b.add_argument("output", nargs="?")
    b.add_argument("--format", choices=["hwpx", "docx"], default="hwpx", help="format used when the output path is omitted")
    b.add_argument("--profile", required=True,
                   help="chapter | flat | profile JSON. The two forms differ in numbering and fonts, so there is no default")
    b.add_argument("--skeleton", help="skeleton hwpx extracted from a user form (HWPX only; by default the built-in form is generated)")
    b.add_argument("--page-break", choices=["chapter", "section", "none"],
                   help="new page unit: chapter=each chapter (default), section=each chapter and section, none=continuous")
    b.add_argument("--long-table", choices=["engine", "split"],
                   help=f"tables over {C.LONG_TABLE_ROWS} rows: engine=split at page boundaries with repeated title rows (default), split=physically split into chunk tables")
    b.add_argument("--toc", action="store_true", help="insert a table of contents at the front (default OFF)")
    b.add_argument("--toc-depth", type=int, default=2, choices=[1, 2, 3], help="TOC depth: 1=chapter, 2=section (default), 3=subsection")
    b.add_argument("--page-number", action="store_true", help="footer page number '- N -' at center (default OFF)")
    b.add_argument("--cover", help='cover (default OFF): "title=title;subtitle=subtitle;date=date;org=organization"')
    b.add_argument("--header", help='header (default OFF): "text;align=LEFT|CENTER|RIGHT"')
    b.add_argument("--merge", default="auto", choices=["auto", "explicit", "none"],
                   help="cell merge: auto=consecutive identical values in leading label columns plus '^' '<' directives (default), explicit=directives only, none=no merge")
    b.add_argument("--rhwp", help="rhwp path used for TOC page-number calculation")
    b.add_argument("--numbered-square", action="store_true", help="print '□ 1. title' lines as numbered headers without a bullet")
    b.add_argument("--labels", help="label JSON for documents in another language: numbering, TOC title, caption labels, "
                                    "extra manuscript tokens, language tags (default: Korean labels)")
    b.set_defaults(func=cmd_build)

    f = sub.add_parser("form", help="save a built-in form as an empty HWPX file")
    f.add_argument("form", choices=sorted(FORMS))
    f.add_argument("output")
    f.set_defaults(func=cmd_form)

    s = sub.add_parser("skeleton", help="user form.hwpx → skeleton + draft profile")
    s.add_argument("input")
    s.add_argument("output")
    s.add_argument("--section", type=int, help="body section number (default: last section)")
    s.set_defaults(func=cmd_skeleton)

    e = sub.add_parser("export", help="document.hwpx → manuscript.md")
    e.add_argument("input")
    e.add_argument("output", nargs="?")
    e.add_argument("--image-dir")
    e.add_argument("--profile", help="if given, maps style names back to roles and restores a leveled manuscript (chapter | flat | JSON)")
    e.set_defaults(func=cmd_export)

    fl = sub.add_parser("fill", help='replacement JSON {"replace": {...}, "cells": {"label > right": "value"}}')
    fl.add_argument("input")
    fl.add_argument("mapping")
    fl.add_argument("-o", "--output")
    fl.set_defaults(func=cmd_fill)

    r = sub.add_parser("render", help="document → PDF + page PNGs")
    r.add_argument("input")
    r.add_argument("--outdir")
    r.add_argument("--dpi", type=int, default=C.RENDER_DPI)
    r.add_argument("--rhwp")
    r.add_argument("--keep-soft-hyphen", action="store_true", help="render the HWPX as is, without the review-copy substitutions")
    r.add_argument("--engine", default="auto", choices=["auto", "rhwp", "soffice"],
                   help="HWPX: auto=rhwp first, otherwise LibreOffice+H2Orestart. DOCX always uses LibreOffice")
    r.set_defaults(func=cmd_render)

    c = sub.add_parser("check", help="structure validation (HWPX: schema, image manifest, rhwp verify / DOCX: structure summary)")
    c.add_argument("input")
    c.add_argument("--expect", default="", help='rhwp verify arguments, e.g. "--expect-min-tables 2"')
    c.set_defaults(func=cmd_check)

    d = sub.add_parser("docx2md", help="DOCX → manuscript.md (step 1: print paragraph types, step 2: convert with a --map JSON)")
    d.add_argument("input")
    d.add_argument("output", nargs="?")
    d.add_argument("--map", help="path of the level mapping JSON")
    d.set_defaults(func=cmd_docx2md)

    x = sub.add_parser("xlsx2md", help="XLSX → manuscript.md (one pipe table per sheet)")
    x.add_argument("input")
    x.add_argument("output", nargs="?")
    x.add_argument("--allow-wide", action="store_true")
    x.set_defaults(func=cmd_xlsx2md)

    fo = sub.add_parser("fonts", help="form font installation status. --setup: download substitute fonts and write substitution rules")
    fo.add_argument("--setup", action="store_true")
    fo.set_defaults(func=cmd_fonts)

    a = ap.parse_args()
    # check the input file. If it is missing, later steps report a different error such as a conversion failure
    if getattr(a, "input", None) and not os.path.exists(a.input):
        sys.exit(msg("err_no_input", path=a.input))
    a.func(a)


if __name__ == "__main__":
    main()
