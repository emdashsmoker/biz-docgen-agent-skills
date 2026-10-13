"""LibreOffice로 DOCX를 열어 목차와 필드를 갱신한 뒤 PDF로 저장한다.
LibreOffice 파이썬 연동(uno)이 있는 인터프리터에서 render.py가 실행한다.

사용: python lo_convert.py <soffice 경로> <입력 파일> <출력 PDF> <LibreOffice 사용자 프로필 URL>
"""
import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue

CONNECT_TRIES = 60          # 1초 간격으로 LibreOffice 기동을 기다리는 횟수
INDEX_UPDATE_PASSES = 2     # 목차가 채워지면 쪽이 밀릴 수 있어 한 번 더 갱신


def prop(name, value):
    p = PropertyValue()
    p.Name, p.Value = name, value
    return p


def main():
    soffice, src, pdf, profile = sys.argv[1:5]
    pipe = f"blockwriter_{os.getpid()}"
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
        for _ in range(INDEX_UPDATE_PASSES):
            indexes = doc.getDocumentIndexes()
            for i in range(indexes.getCount()):
                indexes.getByIndex(i).update()
        doc.storeToURL(uno.systemPathToFileUrl(pdf), (prop("FilterName", "writer_pdf_Export"),))
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
