"""LibreOffice로 DOCX를 열어 필드를 갱신한 뒤 DOCX 사본으로 저장한다.
LibreOffice 파이썬 연동(uno)이 있는 인터프리터에서 docx_report.py가 실행한다.
Why uno: `soffice --convert-to docx`는 PAGEREF 저장값을 다시 계산하지 않고 그대로 기록함. 필드 갱신을 직접 호출해야 쪽번호가 기록됨
사본은 쪽번호 조회에만 쓴다. LibreOffice가 서식을 바꿔 저장하므로 산출물로 쓰지 않는다

사용: python lo_fields.py <soffice 경로> <입력 DOCX> <출력 DOCX> <LibreOffice 사용자 프로필 URL>
"""
import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue

CONNECT_TRIES = 60                    # 1초 간격으로 LibreOffice 기동을 기다리는 횟수
DOCX_FILTER = "MS Word 2007 XML"      # LibreOffice의 DOCX 저장 필터 이름


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def main():
    soffice, src, out, profile = sys.argv[1:5]
    pipe = f"toc_fields_{os.getpid()}"
    proc = subprocess.Popen([soffice, f"-env:UserInstallation={profile}", "--headless", "--invisible", "--norestore",
                             f"--accept=pipe,name={pipe};urp;StarOffice.ComponentContext"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
        ctx = None
        for _ in range(CONNECT_TRIES):
            try:
                ctx = resolver.resolve(f"uno:pipe,name={pipe};urp;StarOffice.ComponentContext")
                break
            except Exception:
                time.sleep(1)
        if ctx is None:
            sys.exit("LibreOffice connection failed")
        desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
        doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(src), "_blank", 0, (prop("Hidden", True),))
        doc.getTextFields().refresh()
        doc.storeToURL(uno.systemPathToFileUrl(out), (prop("FilterName", DOCX_FILTER),))
        doc.close(True)
        try:
            desktop.terminate()
        except Exception:
            pass   # 종료 요청 중 연결이 끊기는 것은 정상
    finally:
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
