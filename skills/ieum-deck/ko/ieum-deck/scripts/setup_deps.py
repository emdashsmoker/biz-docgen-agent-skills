#!/usr/bin/env python3
"""setup_deps.py: 의존성 설치와 확인 (네트워크 가능 환경 기준. 오프라인 번들 없음)
사용: python3 setup_deps.py          설치 후 확인
      python3 setup_deps.py --check  확인만 (종료 코드 0 이면 통과)
설치 대상: pptxgenjs 3.12.0(npm), python-pptx, pypdf 6.19 이상, python-hwpx, pyhwp, markitdown(pip), fonts-nanum(apt), soffice, pdftoppm
hwpx 를 PDF 로 볼 때는 rhwp(https://github.com/edwardkim/rhwp) 또는 LibreOffice H2Orestart 확장이 추가로 필요
"""
import os
import re
import shutil
import subprocess
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPDF_MIN = "6.19"  # PDF 이미지 추출(decode_as_image)을 검증한 최저 버전. 3.x 는 이미지 디코딩 실패가 잦음
PIP_PKGS = ["python-pptx", f"pypdf>={PYPDF_MIN}", "python-hwpx", "pyhwp", "markitdown[all]", "pdfplumber", "pillow", "numpy", "lxml"]
NPM_PKG = "pptxgenjs@3.12.0"


def run(cmd, check=False):
    print("$", " ".join(cmd))
    return subprocess.run(cmd, check=check).returncode


def install():
    pip_flags = ["--break-system-packages"] if os.environ.get("PIP_BREAK", "1") == "1" else []
    # 패키지별로 설치하여 한 패키지의 빌드 실패(예: 구형 setup.py 를 쓰는 pyhwp)가 나머지 설치를 막지 않게 함
    failed = [pkg for pkg in PIP_PKGS if run([sys.executable, "-m", "pip", "install", "-q", *pip_flags, pkg]) != 0]
    if failed:
        print(f"pip 설치 실패: {', '.join(failed)} (각 패키지의 오류 로그 확인. 나머지 패키지는 설치됨)")
    if not (ROOT / "package.json").exists():
        run(["npm", "init", "-y"], check=False)
    run(["npm", "install", "--silent", "--save-exact", NPM_PKG], check=False)
    if shutil.which("apt-get") and not font_ok():
        # 패키지 목록이 비어 있는 새 환경은 목록을 갱신한 뒤 다시 설치
        if run(["apt-get", "install", "-y", "fonts-nanum"]) != 0:
            run(["apt-get", "update"])
            run(["apt-get", "install", "-y", "fonts-nanum"])
        run(["fc-cache", "-f"])
    if not font_ok():
        print("나눔고딕 미탐지. 수동 설치: https://hangeul.naver.com (NanumGothic, NanumGothic Bold)")


def version_tuple(text):
    """"6.19.0" 형식 버전 문자열을 비교 가능한 숫자 튜플로 변환"""
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
        pypdf_ver, pypdf_ok = "미설치", False
    print(f"[{'OK' if pypdf_ok else 'FAIL'}] python pypdf {pypdf_ver} ({PYPDF_MIN} 이상 필요)")
    ok &= pypdf_ok
    node_ok = subprocess.run(["node", "-e", "require('pptxgenjs')"], cwd=ROOT, capture_output=True).returncode == 0
    print("[OK] pptxgenjs" if node_ok else "[FAIL] pptxgenjs (npm install pptxgenjs@3.12.0 in skill root)")
    ok &= node_ok
    for tool in ("node", "soffice", "pdftoppm"):
        found = shutil.which(tool)
        print(f"[{'OK' if found else 'FAIL'}] {tool}")
        ok &= bool(found)
    f = font_ok()
    print("[OK] NanumGothic" if f else "[FAIL] NanumGothic 서체")
    ok &= f
    # hwpx 의 배치 확인용 PDF(parse_input.py --pdf)에만 쓰는 선택 의존성. 통과 판정에는 넣지 않음
    rhwp = shutil.which("rhwp")
    print("[INFO] hwpx PDF 변환: rhwp " + ("있음" if rhwp else "없음. LibreOffice H2Orestart 확장이 없으면 --pdf 변환 불가 (확장 설치 여부는 확인하지 않음)"))
    return 0 if ok else 1


if __name__ == "__main__":
    if "--check" not in sys.argv:
        install()
    sys.exit(check())
