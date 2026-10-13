#!/usr/bin/env python3
"""setup_deps.py: installs and checks dependencies (assumes network access. No offline bundle)
Usage: python3 setup_deps.py          install, then check
       python3 setup_deps.py --check  check only (exit code 0 means pass)
Installs: pptxgenjs 3.12.0(npm), python-pptx, pypdf 6.19 or later, python-hwpx, pyhwp, markitdown(pip), fonts-nanum(apt), soffice, pdftoppm
Viewing hwpx as PDF additionally needs rhwp(https://github.com/edwardkim/rhwp) or the LibreOffice H2Orestart extension
"""
import os
import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPDF_MIN = "6.19"  # Lowest version verified for PDF image extraction (decode_as_image). 3.x often fails to decode images
PIP_PKGS = ["python-pptx", f"pypdf>={PYPDF_MIN}", "python-hwpx", "pyhwp", "markitdown[all]", "pdfplumber", "pillow", "numpy", "lxml"]
NPM_PKG = "pptxgenjs@3.12.0"


def run(cmd, check=False):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=check).returncode


def install():
    pip_flags = ["--break-system-packages"] if os.environ.get("PIP_BREAK", "1") == "1" else []
    # Install package by package so a build failure in one package (e.g. pyhwp with its old setup.py) does not block the rest
    failed = [pkg for pkg in PIP_PKGS if run([sys.executable, "-m", "pip", "install", "-q", *pip_flags, pkg]) != 0]
    if failed:
        print(f"pip install failed: {', '.join(failed)} (check the error log of each package. The other packages are installed)")
    if not (ROOT / "package.json").exists():
        run(["npm", "init", "-y"], check=False)
    run(["npm", "install", "--silent", "--save-exact", NPM_PKG], check=False)
    if shutil.which("apt-get") and not font_ok():
        # A fresh environment with an empty package list updates the list and installs again
        if run(["apt-get", "install", "-y", "fonts-nanum"]) != 0:
            run(["apt-get", "update"])
            run(["apt-get", "install", "-y", "fonts-nanum"])
        run(["fc-cache", "-f"])
    if not font_ok():
        print("NanumGothic not found. Install manually: https://hangeul.naver.com (NanumGothic, NanumGothic Bold)")


def version_tuple(text):
    """Converts a version string like "6.19.0" into a comparable tuple of numbers"""
    return tuple(int(p) for p in re.findall(r"\d+", text)[:3])


def font_ok():
    try:
        out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
        return "NanumGothic" in out
    except Exception:
        return False


def check():
    ok = True
    for mod in ("pptx", "hwpx", "markitdown", "pdfplumber", "PIL", "numpy", "lxml"):
        try:
            __import__(mod)
            print(f"[OK] python {mod}")
        except Exception as e:
            ok = False
            print(f"[FAIL] python {mod}: {e}")
    try:
        pypdf_ver = version("pypdf")
        pypdf_ok = version_tuple(pypdf_ver) >= version_tuple(PYPDF_MIN)
    except PackageNotFoundError:
        pypdf_ver, pypdf_ok = "not installed", False
    print(f"[{'OK' if pypdf_ok else 'FAIL'}] python pypdf {pypdf_ver} ({PYPDF_MIN} or later required)")
    ok &= pypdf_ok
    node_ok = subprocess.run(["node", "-e", "require('pptxgenjs')"], cwd=ROOT, capture_output=True).returncode == 0
    print("[OK] pptxgenjs" if node_ok else "[FAIL] pptxgenjs (npm install pptxgenjs@3.12.0 in skill root)")
    ok &= node_ok
    for tool in ("node", "soffice", "pdftoppm"):
        found = shutil.which(tool)
        print(f"[{'OK' if found else 'FAIL'}] {tool}")
        ok &= bool(found)
    f = font_ok()
    print("[OK] NanumGothic" if f else "[FAIL] NanumGothic font")
    ok &= f
    # Optional dependency used only for the hwpx layout-check PDF (parse_input.py --pdf). Not part of the pass verdict
    rhwp = shutil.which("rhwp")
    print("[INFO] hwpx PDF conversion: rhwp " + ("found" if rhwp else "not found. Without the LibreOffice H2Orestart extension, --pdf conversion is not possible (the extension is not checked)"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--check" not in sys.argv:
        install()
    sys.exit(check())
