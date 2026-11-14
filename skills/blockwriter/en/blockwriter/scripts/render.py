"""Review rendering (HWPX: rhwp or LibreOffice+H2Orestart, DOCX: LibreOffice) and substitute font setup.
Renderers and fonts are not bundled with the skill; installed ones are located and used."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from enum import Enum

import config as C
from config import msg


# ── Renderer lookup ────────────────────────────────────────────────────────
def find_rhwp() -> str | None:
    for cand in (os.path.join(C.SCRIPT_DIR, "rhwp", "rhwp"), os.path.join(C.SCRIPT_DIR, "rhwp", "rhwp.exe"),
                 shutil.which("rhwp"), os.path.expanduser("~/.local/bin/rhwp")):
        if cand and os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def rhwp_supports(rhwp: str, command: str, flag: str | None = None) -> bool:
    """Checks that a command and option exist from the help output. The CLI can change between versions."""
    res = subprocess.run([rhwp, command, "--help"], capture_output=True, text=True)
    text = res.stdout + res.stderr
    # some versions print the full usage even for unknown commands, so usage text alone cannot decide existence
    unknown = any(m in text.lower() for m in C.RHWP_UNKNOWN_COMMAND_MARKERS)
    if res.returncode != 0 and (unknown or ("Usage" not in text and "사용법" not in text)):
        return False
    return flag is None or flag in text


def find_soffice() -> str | None:
    for cand in (shutil.which("soffice"), shutil.which("libreoffice"),
                 r"C:\Program Files\LibreOffice\program\soffice.exe",
                 "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if cand and os.path.isfile(cand):
            return cand
    return None


def writable_dir(path: str) -> str:
    """Directory for outputs. If the source folder is read-only, uses the current working directory."""
    d = os.path.dirname(os.path.abspath(path))
    return d if os.access(d, os.W_OK) else os.getcwd()


def resolve_engine(engine: str, rhwp_opt: str | None, src: str = "") -> str:
    if src.lower().endswith(".docx"):
        return "soffice"
    if engine == "auto":
        return "rhwp" if (rhwp_opt or find_rhwp()) else ("soffice" if find_soffice() else "")
    return engine


def render_copy(src: str, strip_newnum: bool = False, dest_dir: str | None = None) -> str:
    """Review-only HWPX copy. Contains only substitutions that work around approximate renderer limits; the delivered file is not changed.
    - soft hyphen bullets become hyphens, in both the body and the bullet definitions
    - strip_newnum: remove number-restart controls in the middle of the body (H2Orestart fails on those outside the first paragraph)"""
    # ASCII file name (avoids the H2Orestart locale problem). A unique suffix per name so concurrent renders in one folder do not collide.
    # dest_dir is the folder for review files (render --outdir, or the build TOC check's temporary folder); without it, next to the source
    fd, work = tempfile.mkstemp(prefix="_render_copy_", suffix=".hwpx", dir=dest_dir or writable_dir(src))
    os.close(fd)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(work, "w", zipfile.ZIP_DEFLATED) as zout:
        for it in zin.infolist():
            d = zin.read(it.filename)
            # - the level symbol is in the header.xml bullet definition. Replacing only the body renders without the symbol
            if it.filename == "Contents/header.xml":
                d = re.sub(r'(<hh:bullet\b[^>]*\bchar=")\u00ad(")', rf'\g<1>{C.SOFT_HYPHEN_GLYPH}\g<2>',
                           d.decode("utf-8")).encode("utf-8")
            if it.filename.startswith("Contents/section") and it.filename.endswith(".xml"):
                t = d.decode("utf-8").replace("\u00ad", C.SOFT_HYPHEN_GLYPH)
                if strip_newnum:
                    t = re.sub(r'<hp:run charPrIDRef="\d+"><hp:ctrl><hp:newNum[^>]*/></hp:ctrl></hp:run>', "", t)
                d = t.encode("utf-8")
            if it.filename == "mimetype":
                zout.writestr(zipfile.ZipInfo("mimetype"), d, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(it.filename, d)
    return work


def plain_copy(src: str, dest_dir: str) -> str:
    """A review copy with unchanged content. LibreOffice creates a lock file next to the document it opens, so a copy outside the delivery folder is opened"""
    fd, work = tempfile.mkstemp(prefix="_render_copy_", suffix=os.path.splitext(src)[1], dir=dest_dir)
    os.close(fd)
    shutil.copyfile(src, work)
    return work


def _soffice_pdf(src: str, pdf: str) -> str:
    soffice = find_soffice()
    if not soffice:
        sys.exit(msg("err_no_soffice"))
    profile_dir = tempfile.mkdtemp(prefix="lo_profile_")   # a dedicated user profile per render, deleted afterwards
    try:
        return _soffice_convert(soffice, src, pdf, "file://" + profile_dir.replace(os.sep, "/"))
    finally:
        shutil.rmtree(profile_dir, ignore_errors=True)


def _soffice_convert(soffice: str, src: str, pdf: str, profile: str) -> str:
    """Convert to PDF with LibreOffice. LibreOffice recalculates the PAGEREF page references of a DOCX when it exports to PDF"""
    # a unique suffix per conversion folder so concurrent renders in one folder do not collide; made in the PDF folder so the delivery folder is left alone
    outdir = tempfile.mkdtemp(prefix="_lo_out_", dir=os.path.dirname(os.path.abspath(pdf)))
    try:
        env = {**os.environ, "LANG": os.environ.get("LANG") or "C.UTF-8"}
        cmd = [soffice, f"-env:UserInstallation={profile}", "--headless", "--convert-to", "pdf:writer_pdf_Export",
               "--outdir", outdir, src]
        res = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=C.LIBREOFFICE_TIMEOUT)
        made = os.path.join(outdir, os.path.splitext(os.path.basename(src))[0] + ".pdf")
        if not os.path.exists(made):
            sys.exit(msg("err_soffice_failed", detail=(res.stdout + res.stderr)[-300:]))
        shutil.move(made, pdf)
    finally:
        shutil.rmtree(outdir, ignore_errors=True)
    return "soffice"


def to_pdf(src: str, pdf: str, engine: str, rhwp_opt: str | None) -> str:
    """Document to PDF. Returns the engine name used."""
    engine = resolve_engine(engine, rhwp_opt, src)
    if engine == "rhwp":
        rhwp = rhwp_opt or find_rhwp()
        if not rhwp:
            sys.exit(msg("err_no_rhwp"))
        if not rhwp_supports(rhwp, C.RHWP_PDF_COMMAND):
            sys.exit(msg("err_rhwp_command", cmd=C.RHWP_PDF_COMMAND))
        cmd = [rhwp, C.RHWP_PDF_COMMAND, src, "-o", pdf]
        if os.path.isdir(C.USER_FONT_DIR) and rhwp_supports(rhwp, C.RHWP_PDF_COMMAND, C.RHWP_FONT_PATH_FLAG):
            cmd += [C.RHWP_FONT_PATH_FLAG, C.USER_FONT_DIR]
        if rhwp_supports(rhwp, C.RHWP_PDF_COMMAND, C.RHWP_PDF_OUTLINE_FLAG):
            cmd.append(C.RHWP_PDF_OUTLINE_FLAG)
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not os.path.exists(pdf):
            sys.exit(msg("err_rhwp_failed", detail=(res.stderr or res.stdout)[-400:]))
        return "rhwp"
    if engine == "soffice":
        _soffice_pdf(src, pdf)
        return "soffice" if src.lower().endswith(".docx") else "soffice(H2Orestart)"
    sys.exit(msg("err_no_renderer"))


def page_pngs(folder: str) -> list[str]:
    """Names of the page PNG files that render creates (p-N.png)"""
    return [f for f in os.listdir(folder) if re.fullmatch(r"p-\d+\.png", f)]


def render(src: str, outdir: str | None, dpi: int, engine: str, rhwp_opt: str | None, keep_soft_hyphen: bool):
    engine = resolve_engine(engine, rhwp_opt, src)
    is_hwpx = src.lower().endswith(".hwpx")
    base = os.path.splitext(os.path.basename(src))[0]
    stem = os.path.join(writable_dir(src), base)
    # with --outdir, the PDF and the review copy go in that folder too, so rendering a document in the delivery folder does not mix review files into it
    copy_dir = outdir
    pdf = os.path.join(outdir, base + ".pdf") if outdir else stem + ".pdf"
    outdir = outdir or stem + "_pages"
    os.makedirs(outdir, exist_ok=True)
    if is_hwpx and not keep_soft_hyphen:
        work = render_copy(src, strip_newnum=(engine == "soffice"), dest_dir=copy_dir)
    else:
        work = plain_copy(src, copy_dir) if copy_dir else src
    try:
        used = to_pdf(work, pdf, engine, rhwp_opt)
    finally:   # remove the review copy even when rendering fails
        if work != src and os.path.exists(work):
            os.remove(work)
    for f in page_pngs(outdir):   # remove only page PNGs from the previous render; the PDF and other files in the folder stay
        os.remove(os.path.join(outdir, f))
    if shutil.which("pdftoppm"):
        subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, os.path.join(outdir, "p")], check=True)
        print(msg("render_ok", engine=used, pdf=pdf, outdir=outdir, n=len(page_pngs(outdir))))
    else:
        print(msg("render_pdf_only", engine=used, pdf=pdf))


def rhwp_verify(path: str, expect: str) -> bool | None:
    """Expectation check. True if passed, False on a mismatch or unreadable output, None if not checked"""
    rhwp = find_rhwp()
    if not (rhwp and expect):
        return None
    if not rhwp_supports(rhwp, C.RHWP_VERIFY_COMMAND):
        print(msg("warn_verify_missing", cmd=C.RHWP_VERIFY_COMMAND))
        return None
    res = subprocess.run([rhwp, C.RHWP_VERIFY_COMMAND, path, "--json"] + shlex.split(expect), capture_output=True, text=True)
    try:
        d = json.loads(res.stdout)
        items = [(e["kind"], e.get("actual"), e["pass"]) for e in d["expectations"]]
    except (json.JSONDecodeError, KeyError):
        print(msg("verify_parse_fail", out=(res.stdout[:200], res.stderr[:200])))
        return False
    print(msg("verify_result", verdict=d.get("verdict"), items=items))
    return all(ok for _, _, ok in items)


# ── Fonts ──────────────────────────────────────────────────────────────────
def installed_families() -> set[str] | None:
    if not shutil.which("fc-list"):
        return None
    out = subprocess.run(["fc-list", ":", "family"], capture_output=True, text=True).stdout
    return {f.strip() for line in out.splitlines() for f in line.split(",")}


def ksx1001_hanja() -> list[int]:
    """Code points of the 4,620 unified ideographs among the KS X 1001 Hanja"""
    first, last = C.CJK_UNIFIED_RANGE
    code_points = set()
    for lead in C.KSX1001_HANJA_LEAD:
        for trail in C.KSX1001_HANJA_TRAIL:
            ch = bytes((lead, trail)).decode("euc_kr", errors="ignore")
            if ch and first <= ord(ch) <= last:
                code_points.add(ord(ch))
    return sorted(code_points)


class FontLookup(Enum):
    """How installed fonts are looked up"""
    FONTCONFIG = "fontconfig"   # systems with fontconfig, such as Linux
    FOLDERS = "folders"         # Windows and macOS without fontconfig: search the OS font folders by the name table
    NONE = "none"               # cannot look up (no fontTools, or an OS without folder information)


def font_lookup() -> FontLookup:
    if shutil.which("fc-match"):
        return FontLookup.FONTCONFIG
    if sys.platform in C.FONT_DIRS and importlib.util.find_spec("fontTools") is not None:
        return FontLookup.FOLDERS
    return FontLookup.NONE


def fontconfig_file(face: str) -> tuple[str, int] | None:
    """The file and font index fontconfig uses for face. fc-match returns a substitute even for a missing name, so the family name is compared."""
    escaped = re.sub(r"([\\\-:,])", r"\\\1", face)   # special characters of fontconfig patterns
    out = subprocess.run(["fc-match", "-f", "%{family}\n%{file}\n%{index}", escaped],
                         capture_output=True, text=True).stdout.split("\n")
    if len(out) < 3 or face not in (name.strip() for name in out[0].split(",")):
        return None
    return out[1], int(out[2] or 0)


def folder_file(face: str, dirs: list[str]) -> tuple[str, int] | None:
    """The file and font index whose family name is face in the font folders. The regular-weight file is preferred."""
    from fontTools.ttLib import TTCollection, TTFont, TTLibError
    found = []
    for folder in (os.path.expanduser(os.path.expandvars(d)) for d in dirs):
        if not os.path.isdir(folder):
            continue
        for name in sorted(os.listdir(folder)):
            if not name.lower().endswith(C.FONT_FILE_EXTS):
                continue
            path = os.path.join(folder, name)
            try:
                fonts = TTCollection(path, lazy=True).fonts if name.lower().endswith(".ttc") else [TTFont(path, lazy=True)]
                for index, font in enumerate(fonts):
                    families = {r.toUnicode(errors="ignore") for r in font["name"].names if r.nameID in (1, 16)}
                    if face in families:
                        found.append((font["OS/2"].usWeightClass != C.REGULAR_WEIGHT, path, index))
            except (OSError, TTLibError, KeyError):   # skip files that cannot be read or have no name table
                continue
    return min(found)[1:] if found else None


def has_ksx1001_hanja(path: str, index: int) -> bool | None:
    """Whether the font file has outlines for all KS X 1001 unified Hanja. None when fontTools is missing.
    Checking the character codes alone is not enough: the Google release of NanumGothic has no Hanja codes, and NanumSquare has the codes with empty glyphs."""
    try:
        from fontTools.pens.boundsPen import ControlBoundsPen
        from fontTools.ttLib import TTFont
    except ImportError:
        return None
    font = TTFont(path, fontNumber=index, lazy=True)
    cmap, glyphs = font.getBestCmap(), font.getGlyphSet()
    for cp in ksx1001_hanja():
        if cp not in cmap:
            return False
        pen = ControlBoundsPen(glyphs)
        glyphs[cmap[cp]].draw(pen)
        if pen.bounds is None:   # the code exists but the glyph is empty
            return False
    return True


def fonts_report(faces: list[str]):
    """Prints, for each form font, whether it is installed, Hanja coverage, the rendering substitute, and where to get it.
    It reports the computer where the command runs, so run it on the computer that opens the documents to learn that computer's state."""
    lookup = font_lookup()
    print(msg("fonts_header"))
    for face in faces:
        if lookup is FontLookup.NONE:
            located, state, hanja = None, "?", "?"
        else:
            located = fontconfig_file(face) if lookup is FontLookup.FONTCONFIG else folder_file(face, C.FONT_DIRS[sys.platform])
            state = msg("fonts_yes" if located else "fonts_no")
            found = has_ksx1001_hanja(*located) if located else None
            hanja = "-" if not located else "?" if found is None else msg("fonts_hanja_yes" if found else "fonts_hanja_no")
        sub = "-" if located else C.FONT_SUBSTITUTES.get(face, "-")   # same criterion as fonts_setup
        print(msg("fonts_row", face=face, installed=state, hanja=hanja, sub=sub,
                  source=msg(C.FONT_SOURCES[face]) if face in C.FONT_SOURCES else "-"))


def fonts_setup():
    """Downloads the form fonts (SIL OFL 1.1) available in the repository and writes fontconfig rules that map only the fonts not installed to substitutes."""
    fams = installed_families()
    if fams is None:
        print(msg("fonts_no_fc"))
        return
    os.makedirs(C.USER_FONT_DIR, exist_ok=True)
    for family, (folder, files) in C.FREE_FONTS.items():
        if family in fams:
            continue
        for name in files + [C.FREE_FONT_LICENSE_FILE]:
            url = f"{C.FREE_FONT_BASE}/{folder}/{name}"
            dest = os.path.join(C.USER_FONT_DIR, f"{family}-{name}" if name == C.FREE_FONT_LICENSE_FILE else name)
            print(msg("fonts_download", name=name, url=url))
            try:
                with urllib.request.urlopen(url, timeout=C.IMG_URL_TIMEOUT) as resp, open(dest, "wb") as fh:
                    fh.write(resp.read())
            except Exception as ex:
                print(msg("fonts_download_fail", name=name, err=ex))
                break
    rules = []
    for face, sub in C.FONT_SUBSTITUTES.items():
        if face in fams:   # installed fonts are not substituted
            continue
        family = sub.partition(" ExtraBold")[0]
        edit = f'<edit name="family" mode="assign" binding="same"><string>{family}</string></edit>'
        if sub.endswith("ExtraBold"):
            edit += '<edit name="weight" mode="assign" binding="same"><const>extrabold</const></edit>'
        rules.append(f'<match target="pattern"><test name="family"><string>{face}</string></test>{edit}</match>')
    os.makedirs(os.path.dirname(C.FONTCONFIG_FILE), exist_ok=True)
    with open(C.FONTCONFIG_FILE, "w", encoding="utf-8") as fh:
        fh.write('<?xml version="1.0"?>\n<!DOCTYPE fontconfig SYSTEM "fonts.dtd">\n<fontconfig>\n'
                 f"<dir>{C.USER_FONT_DIR}</dir>\n" + "\n".join(rules) + "\n</fontconfig>\n")
    subprocess.run(["fc-cache", "-f"], capture_output=True)
    print(msg("fonts_config", path=C.FONTCONFIG_FILE))
