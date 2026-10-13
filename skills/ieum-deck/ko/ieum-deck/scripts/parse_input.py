#!/usr/bin/env python3
"""parse_input.py: RFP 와 원고를 Markdown 으로 변환
사용: python3 parse_input.py <입력 파일> [출력.md] [--pdf]
지원 형식: hwpx, hwp, pdf, docx, pptx, xlsx, html, csv, json, xml, epub, md, txt
pdf 는 markitdown 본문에 pdfplumber 표를 덧붙이고 실패 시 pdftotext 로 대체
docx 와 pptx 는 markitdown 실패 시 python-docx 와 python-pptx 로 대체
hwpx 변환 순서: python-hwpx export_markdown → HwpxDocument.text.markdown → 본문 XML 직접 추출
--pdf 는 hwpx 를 PDF 로도 변환 (PATH 의 rhwp 우선, 없으면 LibreOffice H2Orestart. 확보 순서는 SKILL.md). 표와 그림 배치를 눈으로 확인할 때 사용

본 제품은 한글과컴퓨터의 한/글 문서 파일(.hwp) 공개 문서를 참고하여 개발하였습니다.
"""
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

# rhwp 는 명령 체계가 자주 바뀜. 이 이름이 현 버전에 없으면 `rhwp --help` 에서 PDF 출력 기능의 명령을 찾아 교체
RHWP_PDF_COMMAND = "export-pdf"  # v0.8.6 확인


def hwpx_to_md(path: Path) -> str:
    """python-hwpx 우선, 실패 시 본문 XML 에서 문단과 표를 직접 추출"""
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
    # 최후 수단: OWPML 본문에서 텍스트만 회수 (표는 셀 구분자로 이어 붙임)
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
    """PATH 의 rhwp 우선, 없으면 LibreOffice(H2Orestart)로 PDF 생성"""
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / (path.stem + ".pdf")
    if shutil.which("rhwp"):
        r = subprocess.run(["rhwp", RHWP_PDF_COMMAND, str(path), "-o", str(pdf)], check=False, capture_output=True, text=True)
        if pdf.exists():
            return pdf
        print(f"WARN: rhwp {RHWP_PDF_COMMAND} 실패. `rhwp --help` 에서 PDF 출력 기능의 명령을 찾아 RHWP_PDF_COMMAND 를 교체: "
              f"{(r.stderr or r.stdout)[-200:]}", file=sys.stderr)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if soffice:
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(path)],
                       check=False, capture_output=True, timeout=300)
        if pdf.exists():
            return pdf
    raise SystemExit("PDF 변환 실패. rhwp 또는 LibreOffice(H2Orestart 확장) 설치 필요")


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
        raise SystemExit("hwp 변환 실패. pyhwp 설치 후 hwp5txt 사용 또는 hwpx 로 저장하여 재시도")
    if ext in (".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm", ".csv", ".json", ".xml", ".epub"):
        try:
            from markitdown import MarkItDown
            body = MarkItDown(enable_plugins=False).convert(str(path)).text_content
        except Exception as e:
            body = fallback_text(path, e)
        if ext == ".pdf":
            alt = fallback_text(path, "비교") if len(re.findall(r"[가-힣]", body)) == 0 else ""
            if alt and len(re.findall(r"[가-힣]", alt)) > 0:
                body = alt  # 본문 추출이 한글을 잃으면 대체 경로 결과를 사용
            body += pdf_tables(path)
            warn_if_unextractable(path, body)
        return body
    raise SystemExit(f"미지원 형식 {ext}. hwpx, hwp, pdf, docx, pptx, xlsx, html, csv, json, xml, epub, md, txt 만 지원")


def warn_if_unextractable(path: Path, body: str) -> None:
    """한글이 전혀 회수되지 않으면 스캔본이나 서브셋 글꼴로 보고 안내"""
    if re.search(r"[가-힣]", body):
        return
    print(f"[안내] {path.name} 에서 한글 텍스트를 회수하지 못했습니다. 스캔본이거나 글꼴이 유니코드 표를 포함하지 않는 경우이며 OCR 또는 원본 파일이 필요합니다")


def pdf_tables(path: Path) -> str:
    """pdfplumber 로 표를 회수하여 마크다운 표로 덧붙임. 표가 없으면 빈 문자열"""
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
                    out.append(f"\n\n### [표] p.{pno}\n\n| " + " | ".join(head) + " |\n|" + "---|" * len(head))
                    for r in body:
                        out.append("| " + " | ".join((r + [""] * len(head))[:len(head)]) + " |")
    except Exception:
        return ""
    return "\n".join(out)


def fallback_text(path: Path, err) -> str:
    """markitdown 실패 시 형식별 대체 경로"""
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
            for t in d.tables:  # 표는 마크다운 표로 회수
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
    raise SystemExit(f"{path.name} 변환 실패 ({err}). python3 scripts/setup_deps.py 로 의존성을 설치한 뒤 재시도")


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
        print(f"{pdf} (원본 배치 확인용)")


if __name__ == "__main__":
    main()
