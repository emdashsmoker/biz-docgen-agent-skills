#!/usr/bin/env python3
"""finalize.py - post-processes the PPTX produced by build.js so PowerPoint can open it

WHY: Packages made by pptxgenjs open in LibreOffice, but PowerPoint (Windows) and
     the iOS preview refuse to open them. Measurement confirmed that a LibreOffice re-serialized copy opens.
     Re-serialization is part of the build pipeline, and OPC violations are removed before and after it.

HOW: 1) OPC normalization - remove directory entries, put [Content_Types].xml first,
        remove Overrides for missing parts, apply recursively to embedded xlsx
     2) XML correction - reassign cNvPr ids, remove dLblPos from stacked charts, set the East Asian font of chart text, set the language tags of runs and charts (meta.labels.language),
        correct the core properties relationship type, clear the application name, remove the document language and presentation format name,
        replace the OpenSymbol bullet font with the text font, write the line break unit attributes on every paragraph (meta.lineBreak)
     3) Re-serialize with soffice and reapply 1 and 2. Without soffice, stop after step 2
     4) Print metrics before and after processing

Usage:
    python scripts/finalize.py deck.pptx
    python scripts/finalize.py deck.pptx --no-soffice
"""

from __future__ import annotations

import argparse
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Settings. These are format constants, not typesetting constants, so they live in this file instead of tokens.js
# ---------------------------------------------------------------------------

CONTENT_TYPES_NAME = "[Content_Types].xml"

# Parts that hold another package inside. The same normalization applies recursively
EMBEDDED_PACKAGE_SUFFIXES = (".xlsx",)

# Parts whose cNvPr ids are reassigned. Only parts with a shape tree
SHAPE_TREE_PART_PATTERN = re.compile(
    r"^ppt/(slides|slideLayouts|slideMasters|notesSlides|notesMasters)/[^/]+\.xml$"
)

# cNvPr id assignment rule for slide XML
# WHY: The shape tree root (nvGrpSpPr of p:spTree) uses 1 by convention and shapes start at 2.
#      pptxgenjs uses a separate counter for tables (graphicFrame), which collides with shape ids
SHAPE_TREE_ROOT_ID = 1
SHAPE_ID_START = 2

# Grouping of stacked series charts. With these values, data label positions cannot be set
STACKED_GROUPINGS = ("stacked", "percentStacked")

# Chart kinds that have a grouping. Checked for stacking
GROUPING_CHART_TAGS = (
    "c:barChart",
    "c:bar3DChart",
    "c:lineChart",
    "c:line3DChart",
    "c:areaChart",
    "c:area3DChart",
)

# Data label position removed from stacked charts
FORBIDDEN_STACKED_LABEL_POSITION = "outEnd"

# Slide part matching. Counted for duplicate ids
SLIDE_PART_PATTERN = re.compile(r"^ppt/slides/slide\d+\.xml$")

# LibreOffice conversion time limit in seconds
SOFFICE_TIMEOUT_SEC = 300

SOFFICE_COMMAND = "soffice"

CNVPR_ID_PATTERN = re.compile(r'(<p:cNvPr\s+id=")(\d+)(")')

OVERRIDE_PATTERN = re.compile(r"<Override\s[^>]*?/>")

PART_NAME_PATTERN = re.compile(r'PartName="([^"]+)"')

# Package relationships part and extended properties part
PACKAGE_RELS_NAME = "_rels/.rels"
APP_PROPS_NAME = "docProps/app.xml"

# Core properties relationship type. soffice re-serialization writes a nonstandard type under the officedocument path,
# so tools that look up core properties by the standard type cannot read the title and author
NONSTANDARD_CORE_REL_TYPE = "http://schemas.openxmlformats.org/officedocument/2006/relationships/metadata/core-properties"
CORE_REL_TYPE = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties"

# Application name. Cleared so the re-serialization tool name and version do not remain in the delivered file properties
APPLICATION_PATTERN = re.compile(r"<Application>[^<]*</Application>")

# Core properties part and custom properties part
CORE_PROPS_NAME = "docProps/core.xml"
CUSTOM_PROPS_NAME = "docProps/custom.xml"

# Document language. The raw build has none, and soffice re-serialization fills it from the runtime locale (en-US when LANG is unset), so it is removed
DOCUMENT_LANGUAGE_PATTERN = re.compile(r"<dc:language>[^<]*</dc:language>")

# Presentation format name. pptxgenjs writes "On-screen Show (16:9)" regardless of the layout, and soffice re-serialization
# moves it into the custom properties, so it is removed in both places (filling the right name would need a name table per layout, so removal was chosen)
PRESENTATION_FORMAT_PATTERNS = (
    re.compile(r"<PresentationFormat>[^<]*</PresentationFormat>"),
    re.compile(r'<property\b[^>]*\bname="PresentationFormat"[^>]*>.*?</property>', re.S),
)


# ---------------------------------------------------------------------------
# Package input and output
# ---------------------------------------------------------------------------


def read_package(data: bytes) -> list[tuple[str, bytes]]:
    """Extracts only file entries from ZIP bytes in original order. Directory entries are excluded"""
    entries = []
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            entries.append((item.filename, archive.read(item.filename)))
    return entries


def write_package(entries: list[tuple[str, bytes]]) -> bytes:
    """Serializes an entry list to ZIP bytes. Keeps the input order"""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, payload in entries:
            archive.writestr(name, payload)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Step 1. OPC normalization
# ---------------------------------------------------------------------------


def strip_ghost_overrides(content_types_xml: str, part_names: set[str]) -> tuple[str, int]:
    """Removes Override declarations for parts that do not exist

    WHY: pptxgenjs declares slideMaster{N}.xml Overrides for as many slides as there are,
         but the only real part is slideMaster1.xml. PowerPoint refuses to open on this mismatch
    """
    removed = 0

    def keep(match: re.Match) -> str:
        nonlocal removed
        found = PART_NAME_PATTERN.search(match.group(0))
        if not found:
            return match.group(0)
        if found.group(1).lstrip("/") in part_names:
            return match.group(0)
        removed += 1
        return ""

    return OVERRIDE_PATTERN.sub(keep, content_types_xml), removed


def normalize_package(data: bytes) -> tuple[bytes, dict]:
    """Removes directory entries, puts [Content_Types].xml first and removes ghost Overrides

    Applies the same processing recursively to embedded packages (xlsx)
    """
    entries = read_package(data)
    part_names = {name for name, _ in entries}
    stats = {"ghost_overrides": 0}

    normalized = []
    for name, payload in entries:
        if name == CONTENT_TYPES_NAME:
            fixed_xml, removed = strip_ghost_overrides(payload.decode("utf-8"), part_names)
            stats["ghost_overrides"] += removed
            payload = fixed_xml.encode("utf-8")
        elif name.lower().endswith(EMBEDDED_PACKAGE_SUFFIXES):
            payload, inner_stats = normalize_package(payload)
            stats["ghost_overrides"] += inner_stats["ghost_overrides"]
        normalized.append((name, payload))

    # WHY: The OPC standard requires [Content_Types].xml as the first entry. pptxgenjs writes directory
    #      entries first and violates this condition
    normalized.sort(key=lambda item: 0 if item[0] == CONTENT_TYPES_NAME else 1)
    return write_package(normalized), stats


# ---------------------------------------------------------------------------
# Step 2. XML correction
# ---------------------------------------------------------------------------


def renumber_shape_ids(xml: str) -> tuple[str, int]:
    """Reassigns cNvPr ids in the shape tree as 1 for the root and a sequence from 2 for shapes"""
    counter = {"index": 0}
    changed = {"count": 0}

    def assign(match: re.Match) -> str:
        counter["index"] += 1
        new_id = SHAPE_TREE_ROOT_ID if counter["index"] == 1 else SHAPE_ID_START + counter["index"] - 2
        if str(new_id) != match.group(2):
            changed["count"] += 1
        return f"{match.group(1)}{new_id}{match.group(3)}"

    return CNVPR_ID_PATTERN.sub(assign, xml), changed["count"]


def strip_stacked_label_position(xml: str) -> tuple[str, int]:
    """Removes data label positions not allowed in stacked series charts

    WHY: ECMA-376 does not allow outEnd with stacked and percentStacked.
         PowerPoint responds to this value with a repair prompt or refuses to open
    """
    label_pattern = re.compile(
        r'<c:dLblPos\s+val="%s"\s*/>' % FORBIDDEN_STACKED_LABEL_POSITION
    )
    removed = {"count": 0}

    def clean_group(match: re.Match) -> str:
        block = match.group(0)
        grouping = re.search(r'<c:grouping\s+val="([^"]+)"', block)
        if not grouping or grouping.group(1) not in STACKED_GROUPINGS:
            return block
        cleaned, hits = label_pattern.subn("", block)
        removed["count"] += hits
        return cleaned

    for tag in GROUPING_CHART_TAGS:
        group_pattern = re.compile(r"<%s(?:\s[^>]*)?>[\s\S]*?</%s>" % (tag, tag))
        xml = group_pattern.sub(clean_group, xml)
    return xml, removed["count"]


def strip_alien_chart_extensions(xml: str) -> tuple[str, int]:
    """Removes chart extension blocks that have no standard-namespace children

    WHY: LibreOffice re-serialization adds a c:extLst holding only showLeaderLines in the c15
         namespace. Schema validators strip non-standard namespace elements before checking,
         so it remains as an empty c:ext and FAILs. The setting equals the default, so removing it changes nothing on screen
    """
    ext_pattern = re.compile(r"<c:extLst>([\s\S]*?)</c:extLst>")
    standard_child_pattern = re.compile(r"<c:(?!ext\b|extLst\b)[A-Za-z]")
    removed = {"count": 0}

    def drop_if_alien(match: re.Match) -> str:
        if standard_child_pattern.search(match.group(1)):
            return match.group(0)
        removed["count"] += 1
        return ""

    return ext_pattern.sub(drop_if_alien, xml), removed["count"]


# Text properties that set only a Latin font (a:latin) with no East Asian font (a:ea) after it
LATIN_ONLY_FONT_PATTERN = re.compile(r'(<a:latin typeface="([^"]*)"\s*/>)(?!\s*<a:ea\b)')


def add_chart_east_asian_fonts(xml: str) -> tuple[str, int]:
    """Adds East Asian (a:ea) and complex script (a:cs) settings with the same font after each Latin font in chart text properties

    WHY: pptxgenjs writes only a:latin for chart categories, legends and data labels. Hangul follows the East Asian font,
         so without it Hangul shows in the theme default font (Malgun Gothic) or a renderer fallback font that differs from the body typeface
    """
    return LATIN_ONLY_FONT_PATTERN.subn(r'\1<a:ea typeface="\2"/><a:cs typeface="\2"/>', xml)


# Bullet font set to the LibreOffice-only symbol font (OpenSymbol). The text font setting goes in the same place (buFont and buFontTx are alternatives)
OPENSYMBOL_BULLET_FONT_PATTERN = re.compile(r'<a:buFont\s+typeface="OpenSymbol"[^>]*/>')
TEXT_BULLET_FONT = "<a:buFontTx/>"


def use_text_font_for_opensymbol_bullets(xml: str) -> tuple[str, int]:
    """Replaces the OpenSymbol bullet font with the text font setting (a:buFontTx)

    WHY: soffice reserialization sets OpenSymbol on bullet characters it cannot move to a PowerPoint symbol font (the hyphen "-" of sub items).
         PowerPoint without OpenSymbol shows these bullets as empty boxes. LibreOffice review renders look correct because OpenSymbol is installed with it.
         The hyphen exists in the body font (NanumGothic), so following the text font makes both programs show the same bullet
    """
    return OPENSYMBOL_BULLET_FONT_PATTERN.subn(TEXT_BULLET_FONT, xml)


PARA_PATTERN = re.compile(r"<a:p>(.*?)</a:p>", re.S)
PPR_PATTERN = re.compile(r"<a:pPr\b[^>]*/>|<a:pPr\b[^>]*>.*?</a:pPr>", re.S)


def strip_duplicate_paragraph_props(xml: str) -> tuple[str, int]:
    """Removes the second and later a:pPr inside one paragraph (a:p).
    pptxgenjs writes a pPr per run, which violates the schema and makes PowerPoint ask for repair"""
    removed = 0

    def clean(match: re.Match) -> str:
        nonlocal removed
        body = match.group(1)
        seen = False
        parts = []
        pos = 0
        for m in PPR_PATTERN.finditer(body):
            parts.append(body[pos:m.start()])
            if not seen:
                parts.append(m.group(0))
                seen = True
            else:
                removed += 1
            pos = m.end()
        parts.append(body[pos:])
        return "<a:p>" + "".join(parts) + "</a:p>"

    return PARA_PATTERN.sub(clean, xml), removed

ADJ_NAME_PATTERN = re.compile(r'<p:cNvPr id="(\d+)" name="adj:(\d+)"')

# Targets of the Hangul run language setting. Hangul syllables, jamo and compatibility jamo
HANGUL_PATTERN = re.compile(r"[ᄀ-ᇿ㄰-㆏가-힣]")
RUN_PATTERN = re.compile(r"<a:r>(.*?)</a:r>", re.S)
RUN_TEXT_PATTERN = re.compile(r"<a:t(?:\s[^>]*)?>(.*?)</a:t>", re.S)
RUN_LANG_PATTERN = re.compile(r'(<a:rPr\b[^>]*?\blang=")([^"]*)(")')
# Language tags. pptxgenjs writes every run, paragraph end and chart with en-US, so they are changed to the tags of the build record (meta.labels.language)
# The defaults are language in assets/labels.json (the same table build.js reads). latin is the tag of ordinary runs, east_asia the tag of runs that contain Hangul
PPTXGENJS_LANG = "en-US"
LABELS_PATH = Path(__file__).resolve().parent.parent / "assets" / "labels.json"
RUN_LANGUAGE = dict(json.loads(LABELS_PATH.read_text(encoding="utf-8"))["language"])
LANG_TAG_PATTERN = re.compile(r"[A-Za-z]{2,3}(-[A-Za-z0-9]{2,8})*")
LATIN_LANG_PATTERN = re.compile(r'(<a:(?:rPr|endParaRPr|defRPr)\b[^>]*?\blang="|<c:lang val=")' + re.escape(PPTXGENJS_LANG) + '(")')


def set_latin_language(xml: str) -> tuple[str, int]:
    """Changes the en-US tags pptxgenjs wrote (runs, paragraph ends, default run properties, chart language) to RUN_LANGUAGE["latin"]. The default en-US changes nothing"""
    latin = RUN_LANGUAGE.get("latin") or PPTXGENJS_LANG
    if latin == PPTXGENJS_LANG:
        return xml, 0
    return LATIN_LANG_PATTERN.subn(lambda m: m.group(1) + latin + m.group(2), xml)


def set_hangul_run_language(xml: str) -> tuple[str, int]:
    """Record the language (a:rPr lang) of runs that contain Hangul as RUN_LANGUAGE["east_asia"] (default ko-KR)

    WHY: pptxgenjs writes every run with lang="en-US". LibreOffice re-serialization fills the language of the East Asian
         part of a run with the default of the runtime locale, so in an environment with no locale set Hangul is saved as zh-CN.
         Recording the language of Hangul runs in the document keeps ko-KR regardless of the runtime (the render is the same)
    """
    count = 0
    east = RUN_LANGUAGE["east_asia"]

    def rep(m: re.Match) -> str:
        nonlocal count
        body = m.group(1)
        if not HANGUL_PATTERN.search("".join(RUN_TEXT_PATTERN.findall(body))):
            return m.group(0)
        lang = RUN_LANG_PATTERN.search(body)
        if lang is None or lang.group(2) == east:
            return m.group(0)
        count += 1
        return "<a:r>" + body[:lang.start(2)] + east + body[lang.end(2):] + "</a:r>"

    return RUN_PATTERN.sub(rep, xml), count


# Paragraph attribute values per line break unit (meta.lineBreak). word keeps Korean eojeol and English words whole at line ends; char breaks at the last character on the line
LINE_BREAK_ATTRS = {
    "word": {"eaLnBrk": "0", "latinLnBrk": "0"},
    "char": {"eaLnBrk": "1", "latinLnBrk": "1"},
}
DEFAULT_LINE_BREAK = "word"
# Line break unit applied during the run. finalize() updates it from the build record (lineBreak)
LINE_BREAK = {"mode": DEFAULT_LINE_BREAK}
PPR_OPEN_PATTERN = re.compile(r"<a:pPr(?:\s[^>]*)?/?>")
PARA_WITHOUT_PPR_PATTERN = re.compile(r"<a:p>(?!\s*<a:pPr\b)")


def line_break_attrs() -> dict:
    """Paragraph attribute values for the line break unit in the build record (LINE_BREAK["mode"])"""
    return LINE_BREAK_ATTRS[LINE_BREAK["mode"]]


def set_paragraph_line_break(xml: str) -> tuple[str, int]:
    """Writes the line break unit attributes (eaLnBrk, latinLnBrk) on every paragraph property (a:pPr). Paragraphs without one get a new paragraph property

    WHY: Both attributes are line break options PowerPoint reads per paragraph (allow Korean word break, allow Latin word break).
         soffice reserialization removes txStyles from the master and defaultTextStyle from presentation.xml,
         so values left to inheritance fall back to PowerPoint's program defaults. Writing them on each paragraph gives the same result in PowerPoint.
         Existing values are overwritten so no value that disagrees with the build record's line break unit remains
    """
    attrs = line_break_attrs()
    count = 0

    def set_attrs(m: re.Match) -> str:
        nonlocal count
        tag = m.group(0)
        closing = "/>" if tag.endswith("/>") else ">"
        body = tag[:-len(closing)]
        for name, val in attrs.items():
            body = re.sub(rf'\s{name}="[^"]*"', "", body) + f' {name}="{val}"'
        if "hangingPunct=" not in body:
            body += ' hangingPunct="1"'
        count += 1
        return body + closing

    xml = PARA_WITHOUT_PPR_PATTERN.sub("<a:p><a:pPr/>", xml)
    return PPR_OPEN_PATTERN.sub(set_attrs, xml), count


def count_line_break_unset(xml: str) -> int:
    """Number of paragraphs whose line break unit attributes are missing or differ from the build record (including paragraphs without a paragraph property)"""
    attrs = line_break_attrs()
    unset = 0
    for m in PARA_PATTERN.finditer(xml):
        ppr = PPR_OPEN_PATTERN.search(m.group(1))
        if ppr is None or any(f'{name}="{val}"' not in ppr.group(0) for name, val in attrs.items()):
            unset += 1
    return unset


# Short side restoration for straight line shapes
# WHY: soffice reserialization writes the zero height of horizontal lines and the zero width of vertical lines as one LibreOffice internal unit (1/100 mm = 360 EMU).
#      A line shape runs from the top left to the bottom right of its box, so PowerPoint shows such a line as a diagonal slanted by 0.01 mm
LO_UNIT_EMU = 360
STRAIGHT_LINE_SHAPE_PATTERN = re.compile(r"<p:(sp|cxnSp)\b.*?</p:\1>", re.S)
STRAIGHT_LINE_PRESET_PATTERN = re.compile(r'<a:prstGeom prst="(?:line|straightConnector1)"')
SHAPE_EXT_PATTERN = re.compile(r'<a:ext cx="(\d+)" cy="(\d+)"\s*/>')


def straighten_lines(xml: str) -> tuple[str, int]:
    """Resets the short side of a straight line shape to 0 when it is at most one LibreOffice unit, restoring horizontal and vertical lines.
    A diagonal whose short side is at most 0.01 mm cannot be told apart from a horizontal or vertical line, so intended diagonals are unaffected"""
    count = 0

    def fix_ext(m):
        nonlocal count
        cx, cy = int(m.group(1)), int(m.group(2))
        if 0 < cy <= LO_UNIT_EMU < cx:
            cy = 0
        elif 0 < cx <= LO_UNIT_EMU < cy:
            cx = 0
        else:
            return m.group(0)
        count += 1
        return f'<a:ext cx="{cx}" cy="{cy}"/>'

    def fix_shape(m):
        body = m.group(0)
        if not STRAIGHT_LINE_PRESET_PATTERN.search(body):
            return body
        return SHAPE_EXT_PATTERN.sub(fix_ext, body, count=1)  # The first a:ext is the shape's own xfrm

    return STRAIGHT_LINE_SHAPE_PATTERN.sub(fix_shape, xml), count


def apply_shape_adjust(xml: str) -> tuple[str, int]:
    """Moves the shape name adj:N into the adj value of prstGeom avLst (pptxgenjs does not support adjust values, so they travel in objectName)
    Used to match the tip width of chevrons and home plates and the radius of rounded rectangles to the source"""
    count = 0
    out = []
    pos = 0
    for m in ADJ_NAME_PATTERN.finditer(xml):
        adj = m.group(2)
        # Find the prstGeom of this shape (p:sp) and replace its avLst
        sp_end = xml.find("</p:sp>", m.end())
        seg = xml[m.end():sp_end]
        geom = re.search(r'<a:prstGeom prst="([a-zA-Z0-9]+)">\s*<a:avLst\s*/>|<a:prstGeom prst="([a-zA-Z0-9]+)"><a:avLst></a:avLst>', seg)
        if geom is None:
            continue
        prst = geom.group(1) or geom.group(2)
        new_geom = f'<a:prstGeom prst="{prst}"><a:avLst><a:gd name="adj" fmla="val {adj}"/></a:avLst>'
        out.append(xml[pos:m.end()])
        out.append(seg[:geom.start()] + new_geom + seg[geom.end():])
        pos = sp_end
        count += 1
    out.append(xml[pos:])
    return "".join(out), count


def fix_core_properties_rel_type(xml: str) -> tuple[str, int]:
    """Corrects the core properties type in the package relationships to the standard type"""
    return xml.replace(NONSTANDARD_CORE_REL_TYPE, CORE_REL_TYPE), xml.count(NONSTANDARD_CORE_REL_TYPE)


def clear_application_name(xml: str) -> tuple[str, int]:
    """Clears the application name in the extended properties"""
    return APPLICATION_PATTERN.subn("<Application></Application>", xml)


def clear_document_language(xml: str) -> tuple[str, int]:
    """Removes the document language from the core properties"""
    return DOCUMENT_LANGUAGE_PATTERN.subn("", xml)


def clear_presentation_format(xml: str) -> tuple[str, int]:
    """Removes the presentation format name from the extended and custom properties"""
    removed = 0
    for pattern in PRESENTATION_FORMAT_PATTERNS:
        xml, count = pattern.subn("", xml)
        removed += count
    return xml, removed


def fix_part_xml(name: str, payload: bytes) -> tuple[bytes, dict]:
    """Applies XML correction to one part. Returns the original if the part is not a target"""
    stats = {"renumbered_ids": 0, "stacked_labels": 0, "alien_extensions": 0, "duplicate_ppr": 0, "shape_adjust": 0}

    if name == PACKAGE_RELS_NAME:
        xml, stats["core_rel_type"] = fix_core_properties_rel_type(payload.decode("utf-8"))
        return xml.encode("utf-8"), stats

    if name == APP_PROPS_NAME:
        xml, stats["application"] = clear_application_name(payload.decode("utf-8"))
        xml, stats["presentation_format"] = clear_presentation_format(xml)
        return xml.encode("utf-8"), stats

    if name == CUSTOM_PROPS_NAME:
        xml, stats["presentation_format"] = clear_presentation_format(payload.decode("utf-8"))
        return xml.encode("utf-8"), stats

    if name == CORE_PROPS_NAME:
        xml, stats["document_language"] = clear_document_language(payload.decode("utf-8"))
        return xml.encode("utf-8"), stats

    if SHAPE_TREE_PART_PATTERN.match(name):
        xml, changed = renumber_shape_ids(payload.decode("utf-8"))
        stats["renumbered_ids"] = changed
        xml, dup = strip_duplicate_paragraph_props(xml)
        stats["duplicate_ppr"] = dup
        xml, adj = apply_shape_adjust(xml)
        stats["shape_adjust"] = adj
        xml, sl = straighten_lines(xml)
        stats["straightened_lines"] = sl
        xml, cf = fix_table_cell_fills(xml)
        stats["cell_fill"] = cf
        xml, cm = restore_cell_vertical_margins(xml)
        stats["cell_margin"] = cm
        xml, bf = use_text_font_for_opensymbol_bullets(xml)
        stats["opensymbol_bullets"] = bf
        xml, _ = set_paragraph_line_break(xml)
        xml, _ = set_latin_language(xml)
        xml, lang = set_hangul_run_language(xml)
        stats["hangul_lang"] = lang
        return xml.encode("utf-8"), stats

    if name.startswith("ppt/charts/") and name.endswith(".xml"):
        xml, removed = strip_stacked_label_position(payload.decode("utf-8"))
        stats["stacked_labels"] = removed
        xml, dropped = strip_alien_chart_extensions(xml)
        stats["alien_extensions"] = dropped
        xml, fonts = add_chart_east_asian_fonts(xml)
        stats["chart_ea_fonts"] = fonts
        xml, _ = set_latin_language(xml)
        return xml.encode("utf-8"), stats

    return payload, stats


def fix_package_xml(data: bytes) -> tuple[bytes, dict]:
    """Applies XML correction to the whole package"""
    entries = read_package(data)
    stats = {"renumbered_ids": 0, "stacked_labels": 0, "alien_extensions": 0, "duplicate_ppr": 0, "shape_adjust": 0}

    fixed = []
    for name, payload in entries:
        payload, part_stats = fix_part_xml(name, payload)
        for key in stats:
            stats[key] += part_stats[key]
        fixed.append((name, payload))

    fixed.sort(key=lambda item: 0 if item[0] == CONTENT_TYPES_NAME else 1)
    return write_package(fixed), stats


# ---------------------------------------------------------------------------
# Step 3. LibreOffice re-serialization
# ---------------------------------------------------------------------------


def find_soffice() -> str | None:
    return shutil.which(SOFFICE_COMMAND)


def build_soffice_env() -> dict:
    """Sets a virtual output device so soffice does not look for a window system in headless environments"""
    env = os.environ.copy()
    env.setdefault("SAL_USE_VCLPLUGIN", "svp")
    return env


def reserialize_with_soffice(pptx_path: Path) -> bool:
    """Resaves the pptx with LibreOffice and swaps in a package PowerPoint accepts

    WHY: Fixing the 3 format violations still leaves PowerPoint unable to open the file. Measurement confirmed
         that only the re-serialized copy opens, so re-serialization was adopted in place of a root-cause search
    """
    soffice = find_soffice()
    if not soffice:
        return False

    with tempfile.TemporaryDirectory() as work_dir:
        work = Path(work_dir)
        source = work / pptx_path.name
        shutil.copy2(pptx_path, source)
        profile = work / "soffice_profile"
        profile.mkdir()

        result = subprocess.run(
            [
                soffice,
                "--headless",
                f"-env:UserInstallation=file://{profile}",
                "--convert-to",
                "pptx",
                "--outdir",
                str(work / "out"),
                str(source),
            ],
            env=build_soffice_env(),
            capture_output=True,
            timeout=SOFFICE_TIMEOUT_SEC,
        )

        converted = work / "out" / f"{source.stem}.pptx"
        if result.returncode != 0 or not converted.exists():
            return False
        shutil.copy2(converted, pptx_path)
    return True


# ---------------------------------------------------------------------------
# Step 4. Check metrics
# ---------------------------------------------------------------------------


def count_package_defects(data: bytes) -> dict:
    """Structural defect counts of one package. Embedded package defects are added in"""
    counts = {"parts": 0, "dir_entries": 0, "content_types_misplaced": 0, "ghost_overrides": 0}

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        names = archive.namelist()
        counts["dir_entries"] = sum(1 for item in archive.infolist() if item.is_dir())
        part_names = {item.filename for item in archive.infolist() if not item.is_dir()}
        counts["parts"] = len(part_names)

        if not names or names[0] != CONTENT_TYPES_NAME:
            counts["content_types_misplaced"] = 1

        if CONTENT_TYPES_NAME in part_names:
            declared = PART_NAME_PATTERN.findall(archive.read(CONTENT_TYPES_NAME).decode("utf-8"))
            counts["ghost_overrides"] = sum(
                1 for part in declared if part.lstrip("/") not in part_names
            )

        for name in sorted(part_names):
            if name.lower().endswith(EMBEDDED_PACKAGE_SUFFIXES):
                inner = count_package_defects(archive.read(name))
                for key in ("dir_entries", "content_types_misplaced", "ghost_overrides"):
                    counts[key] += inner[key]
    return counts


def count_xml_defects(data: bytes) -> dict:
    """XML-level defect counts. Number of slides with duplicate ids, label positions in stacked charts, OpenSymbol bullets in slides, slide paragraphs without the line break unit and slanted straight lines in slides"""
    counts = {"duplicate_id_slides": 0, "stacked_label_positions": 0, "opensymbol_bullets": 0, "line_break_unset": 0, "slanted_lines": 0}

    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for name in archive.namelist():
            if SLIDE_PART_PATTERN.match(name):
                xml = archive.read(name).decode("utf-8")
                ids = [match.group(2) for match in CNVPR_ID_PATTERN.finditer(xml)]
                if len(ids) != len(set(ids)):
                    counts["duplicate_id_slides"] += 1
                counts["opensymbol_bullets"] += len(OPENSYMBOL_BULLET_FONT_PATTERN.findall(xml))
                counts["line_break_unset"] += count_line_break_unset(xml)
                counts["slanted_lines"] += straighten_lines(xml)[1]
            elif name.startswith("ppt/charts/") and name.endswith(".xml"):
                xml = archive.read(name).decode("utf-8")
                _, remaining = strip_stacked_label_position(xml)
                counts["stacked_label_positions"] += remaining
    return counts


def inspect(pptx_path: Path) -> dict:
    """All defect counts of one PPTX. validate.py uses the same function so the judgments agree"""
    data = pptx_path.read_bytes()
    metrics = count_package_defects(data)
    metrics.update(count_xml_defects(data))
    return metrics


# Display names of check items. A nonzero value is a FAIL
FAILABLE_METRICS = {
    "dir_entries": "directory_entries",
    "content_types_misplaced": "content_types_not_first",
    "ghost_overrides": "ghost_overrides",
    "duplicate_id_slides": "duplicate_id_slides",
    "stacked_label_positions": "stacked_chart_label_positions",
    "opensymbol_bullets": "opensymbol_bullets",
    "line_break_unset": "line_break_unset_paragraphs",
    "slanted_lines": "slanted_lines",
}


def format_metrics(label: str, metrics: dict) -> str:
    items = " ".join(f"{name}={metrics[key]}" for key, name in FAILABLE_METRICS.items())
    return f"[finalize] {label}: parts={metrics['parts']} {items}"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------


# Base colors allowed as table cell fills (navy and mono theme colors, tints, grays, white). Table style accent colors added by re-serialization revert to white
# finalize() adds custom theme colors read from the palette in the build record
CELL_PALETTE = {"1F3864", "17294A", "6B8EC2", "A9B9D9", "D5DDEC", "E9EBF0", "F7F8FA", "F2F2F2",
                "C9CDD8", "FFFFFF", "BFBFBF", "A6A6A6", "595959", "333333", "2B2B2B", "4D4D4D",
                "808080", "D9D9D9", "C0392B", "8B93A7", "EBEBEB", "F8F8F8", "939393"}


TC_BLOCK = re.compile(r"<a:tc\b[^>]*>.*?</a:tc>", re.S)
TC_PR_OPEN = re.compile(r"<a:tcPr\b([^>]*?)(/?)>")
BODY_PR_OPEN = re.compile(r"<a:bodyPr\b([^>]*?)/?>")


def restore_cell_vertical_margins(xml: str) -> tuple[str, int]:
    """When soffice re-serialization moves the top and bottom cell margins (tcPr marT, marB) to bodyPr tIns, bIns,
    PowerPoint applies the tcPr default (0.05 inch), so rows grow taller than designed and the table spills below the body.
    Returning the bodyPr values to tcPr makes row heights match in both programs"""
    count = 0

    def fix_cell(m):
        nonlocal count
        block = m.group(0)
        pr = TC_PR_OPEN.search(block)
        if not pr or "marT=" in pr.group(1):
            return block
        bp = BODY_PR_OPEN.search(block)
        ins = dict(re.findall(r'\b([tb]Ins)="(\d+)"', bp.group(1))) if bp else {}
        if "tIns" not in ins or "bIns" not in ins:
            return block
        count += 1
        new_open = f'<a:tcPr{pr.group(1)} marT="{ins["tIns"]}" marB="{ins["bIns"]}"{pr.group(2)}>'
        return block[:pr.start()] + new_open + block[pr.end():]

    return TC_BLOCK.sub(fix_cell, xml), count


def fix_table_cell_fills(xml: str) -> tuple[str, int]:
    count = 0

    def rep(m):
        nonlocal count
        color = m.group(2).upper()
        if color in CELL_PALETTE:
            return m.group(0)
        count += 1
        return f'{m.group(1)}<a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>'

    xml = re.sub(r'(<a:tcPr[^>]*>(?:(?!</a:tcPr>).)*?)<a:solidFill><a:srgbClr val="([0-9a-fA-F]{6})"\s*/></a:solidFill>', rep, xml, flags=re.S)
    return xml, count


def capture_hole_sizes(data: bytes) -> dict:
    """Records the donut holeSize value per chart part"""
    out = {}
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        for name in zf.namelist():
            if name.startswith("ppt/charts/") and name.endswith(".xml"):
                m = re.search(r'<c:holeSize val="(\d+)"', zf.read(name).decode("utf-8", "replace"))
                if m:
                    out[name] = m.group(1)
    return out


def restore_hole_sizes(data: bytes, holes: dict) -> bytes:
    if not holes:
        return data
    entries = read_package(data)
    fixed = []
    for name, payload in entries:
        if name in holes:
            xml = payload.decode("utf-8", "replace")
            xml = re.sub(r'<c:holeSize val="\d+"', f'<c:holeSize val="{holes[name]}"', xml)
            payload = xml.encode("utf-8")
        fixed.append((name, payload))
    return write_package(fixed)


def theme_palette(pptx_path: Path) -> set:
    """Theme colors left in the build record (<file name>.build.json). Read so table cell fills in custom theme colors are not reverted to white"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return set()
    try:
        return {str(c).upper() for c in json.loads(record.read_text(encoding="utf-8")).get("palette") or []}
    except (OSError, ValueError):
        return set()


def record_language(pptx_path: Path) -> dict:
    """Language tags (meta.labels.language) in the build record (<file name>.build.json). Values that are not tags are ignored and the defaults stay"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return {}
    try:
        lang = json.loads(record.read_text(encoding="utf-8")).get("language") or {}
    except (OSError, ValueError):
        return {}
    out = {}
    for key in ("latin", "east_asia"):
        val = lang.get(key)
        if isinstance(val, str) and LANG_TAG_PATTERN.fullmatch(val):
            out[key] = val
        elif val is not None:
            print(f"[finalize] Language tag {key}={val!r} is malformed, keeping the default {RUN_LANGUAGE[key]}")
    return out


def record_line_break(pptx_path: Path) -> str:
    """Line break unit (meta.lineBreak) in the build record (<file name>.build.json). The default word applies when the record is missing or the value is undefined"""
    record = pptx_path.with_suffix(".build.json")
    if not record.is_file():
        return DEFAULT_LINE_BREAK
    try:
        mode = json.loads(record.read_text(encoding="utf-8")).get("lineBreak") or DEFAULT_LINE_BREAK
    except (OSError, ValueError):
        return DEFAULT_LINE_BREAK
    if not isinstance(mode, str) or mode not in LINE_BREAK_ATTRS:
        print(f"[finalize] Line break unit lineBreak={mode!r} is undefined, applying the default {DEFAULT_LINE_BREAK}")
        return DEFAULT_LINE_BREAK
    return mode


def finalize(pptx_path: Path, use_soffice: bool = True) -> dict:
    """Post-processes the input PPTX, overwrites it in place and returns the metrics before and after"""
    CELL_PALETTE.update(theme_palette(pptx_path))
    RUN_LANGUAGE.update(record_language(pptx_path))
    LINE_BREAK["mode"] = record_line_break(pptx_path)
    before = inspect(pptx_path)
    print(format_metrics("before", before))

    data = pptx_path.read_bytes()
    data, _ = normalize_package(data)
    data, _ = fix_package_xml(data)
    pptx_path.write_bytes(data)

    reserialized = False
    if use_soffice:
        holes = capture_hole_sizes(data)  # soffice re-serialization resets the donut hole size to 50, so keep it
        reserialized = reserialize_with_soffice(pptx_path)
        if reserialized:
            data = pptx_path.read_bytes()
            data, _ = normalize_package(data)
            data, _ = fix_package_xml(data)
            data = restore_hole_sizes(data, holes)
            entries = [(n, fix_table_cell_fills(p.decode("utf-8", "replace"))[0].encode("utf-8") if SHAPE_TREE_PART_PATTERN.match(n) else p) for n, p in read_package(data)]
            data = write_package(entries)
            pptx_path.write_bytes(data)
        else:
            print("[finalize] Re-serialization skipped because soffice is missing or conversion failed. "
                  "Opening in PowerPoint is not guaranteed")
    else:
        print("[finalize] Re-serialization skipped because --no-soffice was given")

    after = inspect(pptx_path)
    print(format_metrics("after", after))
    return {"before": before, "after": after, "reserialized": reserialized}


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-processes a PPTX so PowerPoint can open it")
    parser.add_argument("pptx", help="PPTX path to process. Overwritten in place")
    parser.add_argument("--no-soffice", action="store_true", help="Skip LibreOffice re-serialization")
    args = parser.parse_args()

    pptx_path = Path(args.pptx)
    if not pptx_path.is_file():
        print(f"[finalize] File not found: {pptx_path}")
        return 1

    result = finalize(pptx_path, use_soffice=not args.no_soffice)
    failed = [name for key, name in FAILABLE_METRICS.items() if result["after"][key]]
    if failed:
        print(f"[finalize] Remaining defects: {', '.join(failed)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
