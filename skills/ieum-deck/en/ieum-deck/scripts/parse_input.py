#!/usr/bin/env python3
"""parse_input.py: converts RFPs and manuscripts to Markdown
Usage: python3 parse_input.py <input file> [output.md] [--pdf]
Supported formats: hwpx, hwp, pdf, docx, pptx, xlsx, html, csv, json, xml, epub, md, txt
pdf appends pdfplumber tables to the markitdown body and falls back to pdftotext on failure
docx and pptx fall back to python-docx and python-pptx when markitdown fails
hwpx conversion order: python-hwpx export_markdown → HwpxDocument.text.markdown → direct extraction from body XML
--pdf also converts hwpx to PDF (rhwp on PATH first, otherwise LibreOffice H2Orestart. How to obtain them is in SKILL.md). Use it to check table and figure placement by eye

본 제품은 한글과컴퓨터의 한/글 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
(English) This product was developed with reference to the public documentation of the Hancom Hangul document file format (.hwp)
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# rhwp changes its command set often. If this name is missing in the current version, find the PDF output command in `rhwp --help` and replace it
RHWP_PDF_COMMAND = "export-pdf"  # checked on v0.8.6


def hwpx_to_md(path: Path) -> str:
    """python-hwpx first. On failure, extracts paragraphs and tables directly from the body XML"""
    try:
        from hwpx.tools.exporter import export_markdown
        return export_markdown(path.read_bytes(), include_tables=True)
    except Exception:
        pass
    try:
        from hwpx import HwpxDocument
        m = HwpxDocument.open(str(path)).text.markdown
        return m() if callable(m) else m
    except Exception:
        pass
    # Last resort: recover only the text from the OWPML body (tables are joined with cell separators)
    out = []
    with zipfile.ZipFile(path) as zf:
        for name in sorted(n for n in zf.namelist() if re.match(r"Contents/section\d+\.xml", n)):
            xml = zf.read(name).decode("utf-8", "replace")
            for para in re.findall(r"<hp:p\b.*?</hp:p>", xml, re.S):
                text = "".join(re.findall(r"<hp:t[^>]*>(.*?)</hp:t>", para, re.S))
                text = re.sub(r"<[^>]+>", "", text).strip()
                if text:
                    out.append(text)
    return "\n\n".join(out)


def hwpx_to_pdf(path: Path, out_dir: Path) -> Path:
    """Creates a PDF with rhwp on PATH first, otherwise LibreOffice (H2Orestart)"""
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / (path.stem + ".pdf")
    if shutil.which("rhwp"):
        r = subprocess.run(["rhwp", RHWP_PDF_COMMAND, str(path), "-o", str(pdf)], check=False, capture_output=True, text=True)
        if pdf.exists():
            return pdf
        print(f"WARN: rhwp {RHWP_PDF_COMMAND} failed. Find the PDF output command in `rhwp --help` and replace RHWP_PDF_COMMAND: "
              f"{(r.stderr or r.stdout)[-200:]}", file=sys.stderr)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(path)],
                       check=False, capture_output=True, timeout=300)
        if pdf.exists():
            return pdf
    raise SystemExit("PDF conversion failed. Install rhwp or LibreOffice (H2Orestart extension)")


def to_markdown(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in (".md", ".txt"):
        return path.read_text(encoding="utf-8", errors="replace")
    if ext == ".hwpx":
        return hwpx_to_md(path)
    if ext == ".hwp":
        try:
            from hwp5.dataio import ParseError  # noqa: F401
            r = subprocess.run(["hwp5txt", str(path)], capture_output=True, text=True, check=False)
            if r.returncode == 0 and r.stdout.strip():
                return r.stdout
        except Exception:
            pass
        raise SystemExit("hwp conversion failed. Install pyhwp and use hwp5txt, or save as hwpx and retry")
    if ext in (".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".csv", ".json", ".xml", ".epub"):
        try:
            from markitdown import MarkItDown
            body = MarkItDown(enable_plugins=False).convert(str(path)).text_content
        except Exception as e:
            body = fallback_text(path, e)
        if ext == ".pdf":
            alt = fallback_text(path, "comparison") if len(re.findall(r"[가-힣]", body)) == 0 else ""
            if alt and len(re.findall(r"[가-힣]", alt)) > 0:
                body = alt  # If body extraction loses the Hangul text, use the fallback result
            body += pdf_tables(path)
            warn_if_unextractable(path, body)
        return body
    raise SystemExit(f"Unsupported format {ext}. Only hwpx, hwp, pdf, docx, pptx, xlsx, html, csv, json, xml, epub, md, txt are supported")


def warn_if_unextractable(path: Path, body: str) -> None:
    """If no Hangul is recovered at all, treats the file as a scan or subset font and informs the user"""
    if re.search(r"[가-힣]", body):
        return
    print(f"[NOTICE] No Hangul text could be recovered from {path.name}. The file is a scan or its fonts lack a Unicode map, so OCR or the original file is needed")


def pdf_tables(path: Path) -> str:
    """Recovers tables with pdfplumber and appends them as markdown tables. Empty string if there are none"""
    try:
        import pdfplumber
    except Exception:
        return ""
    out = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for pno, page in enumerate(pdf.pages, 1):
                for t in (page.extract_tables() or []):
                    rows = [[(c or "").replace("\n", " ").strip() for c in r] for r in t if any(r)]
                    if len(rows) < 2:
                        continue
                    head, body = rows[0], rows[1:]
                    out.append(f"\n\n### [Table] p.{pno}\n\n| " + " | ".join(head) + " |\n|" + "---|" * len(head))
                    for r in body:
                        out.append("| " + " | ".join((r + [""] * len(head))[:len(head)]) + " |")
    except Exception:
        return ""
    return "\n".join(out)


def fallback_text(path: Path, err) -> str:
    """Fallback path per format when markitdown fails"""
    ext = path.suffix.lower()
    if ext == ".pdf":
        r = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=False)
        if r.returncode == 0:
            return r.stdout
    if ext == ".docx":
        try:
            import docx
            d = docx.Document(str(path))
            out = [p.text for p in d.paragraphs if p.text.strip()]
            for t in d.tables:  # Tables are recovered as markdown tables
                rows = [[c.text.replace("\n", " ").strip() for c in r.cells] for r in t.rows]
                if len(rows) < 2:
                    continue
                out.append("\n| " + " | ".join(rows[0]) + " |\n|" + "---|" * len(rows[0]))
                out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
            return "\n\n".join(out)
        except Exception:
            pass
    if ext == ".pptx":
        try:
            from pptx import Presentation
            return "\n\n".join(sh.text_frame.text for s in Presentation(str(path)).slides
                                 for sh in s.shapes if sh.has_text_frame and sh.text_frame.text.strip())
        except Exception:
            pass
    raise SystemExit(f"{path.name} conversion failed ({err}). Install dependencies with python3 scripts/setup_deps.py and retry")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    src = Path(args[0])
    dst = Path(args[1]) if len(args) > 1 else src.with_suffix(".md")
    md = to_markdown(src)
    dst.write_text(md, encoding="utf-8")
    print(f"{dst} chars={len(md)} lines={md.count(chr(10))}")
    if "--pdf" in sys.argv and src.suffix.lower() == ".hwpx":
        pdf = hwpx_to_pdf(src, dst.parent)
        print(f"{pdf} (for checking the original layout)")


if __name__ == "__main__":
    main()
