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
    for line in M.gate_adjust(elems, a.adjust_chars, a.adjust_lines):   # adjustments are OFF by default and apply only with their options
        print(line)
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
    """Number of footnotes in the output file, counting both [^n] footnotes and footnotes moved from source lines."""
    with zipfile.ZipFile(path) as z:
        if path.lower().endswith(".hwpx"):
            return sum(len(re.findall(r"<hp:footNote\b", z.read(n).decode("utf-8")))
                       for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        if "word/footnotes.xml" not in z.namelist():
            return 0
        # body footnotes, excluding separator footnotes (those with w:type)
        return len(re.findall(r"<w:footnote\b(?![^>]*w:type=)", z.read("word/footnotes.xml").decode("utf-8")))


def count_merged_notes(path: str) -> int:
    """Number of footnote references in the output file replaced by a cross-reference to the first footnote number (source footnote merging)"""
    with zipfile.ZipFile(path) as z:
        if path.lower().endswith(".hwpx"):
            # TOC page references are the same CROSSREF field, so count only fields whose target is a footnote
            return sum(z.read(n).decode("utf-8").count(">TARGET_FOOTNOTE<")
                       for n in z.namelist() if re.match(r"Contents/section\d+\.xml$", n))
        return len(re.findall(r"<w:instrText[^>]*>\s*NOTEREF\b", z.read("word/document.xml").decode("utf-8")))


def cmd_toc_static(a):
    """Post-build static conversion: removes bookmarks of the given kinds from the submitted file and turns the page references to them into plain text.
    Items whose page numbers were not updated (placeholder) are skipped and reported. Why: only Hangul and Word calculate the real pages"""
    import toc_refs
    style_kinds = static_style_kinds(a.profile, toc_refs.is_docx(a.input))
    items = toc_refs.scan(a.input, style_kinds)
    if not items:
        sys.exit(msg("err_static_no_refs"))
    for it in items:   # kind, stored page number, update state, bookmark name, text of the paragraph holding the bookmark
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
    """Paragraph style name → TOC item kind. HWPX uses the style names of the profile; DOCX uses the Word style names the builder creates"""
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
    b.add_argument("--footnote-merge", choices=list(C.NOTE_MERGE_SCOPES),
                   help="source footnote merging (default OFF): replaces a footnote that repeats the same text inside the scope "
                        "with a cross-reference to the first footnote number. "
                        "Scope: square=□, section=section (##), chapter=chapter (#), document=whole document")
    b.add_argument("--source-layout", choices=list(C.SOURCE_LAYOUTS), default=C.DEFAULT_SOURCE_LAYOUT,
                   help="layout of multiple sources under tables and figures: auto=break at <br> in the manuscript (default), break=one source per line, "
                        "inline=one line. Lines after the first align with the text after the label")
    b.add_argument("--adjust-chars", action="store_true",
                   help="apply '(조정: 장평 N, 자간 N)' (width, spacing) directives in the manuscript (default OFF). Values are %%p added to the style values")
    b.add_argument("--adjust-lines", action="store_true",
                   help="apply '(조정: 줄 간격 N)' (line spacing) directives in the manuscript (default OFF). Values are %%p added to the style value")
    b.add_argument("--toc", action="store_true",
                   help="insert a table of contents at the front (default OFF). With --page-number, each listed item gets a bookmark and its page number is written as a page reference field")
    b.add_argument("--toc-scope", help=f"TOC scope (comma-separated, default {','.join(C.TOC_SCOPE_DEFAULT)}). "
                                       f"Items: {', '.join(C.TOC_SCOPE_KINDS)}. table and figure are tables and figures with numbered captions")
    b.add_argument("--page-number", action="store_true", help="footer page number '- N -' at center (default OFF)")
    b.add_argument("--cover", help='cover (default OFF): "title=title;subtitle=subtitle;date=date;org=organization"')
    b.add_argument("--header", help='header (default OFF): "text;align=LEFT|CENTER|RIGHT"')
    b.add_argument("--merge", default="auto", choices=["auto", "explicit", "none"],
                   help="cell merge: auto=consecutive identical values in leading label columns plus '^' '<' directives (default), explicit=directives only, none=no merge")
    b.add_argument("--numbered-square", action="store_true", help="print '□ 1. title' lines as numbered headers without a bullet")
    b.add_argument("--labels", help="label JSON for documents in another language: numbering, TOC title, caption labels, "
                                    "extra manuscript tokens, language tags (default: Korean labels)")
    b.set_defaults(func=cmd_build)

    ts = sub.add_parser("toc-static", help="post-build static conversion: makes a copy in which the bookmarks of the given items are removed and their TOC page numbers are plain text")
    ts.add_argument("input", help="hwpx or docx saved after updating page numbers in Hangul or Word")
    ts.add_argument("--scope", help=f"item kinds to make static (comma-separated or {C.STATIC_SCOPE_ALL}). Omit it to print the item status only")
    ts.add_argument("-o", "--output", help=f"output path (default: the source name with the {C.STATIC_SUFFIX} suffix)")
    ts.add_argument("--profile", default="chapter", help="profile used to identify item kinds from style names (chapter | flat | profile JSON)")
    ts.set_defaults(func=cmd_toc_static)

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
