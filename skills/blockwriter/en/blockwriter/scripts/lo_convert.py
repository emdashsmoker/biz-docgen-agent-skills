"""Opens a DOCX with LibreOffice, updates the TOC and fields, then saves it as PDF.
render.py runs it with an interpreter that has the LibreOffice Python bridge (uno).

Usage: python lo_convert.py <soffice path> <input file> <output PDF> <LibreOffice user profile URL>
"""
import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue

CONNECT_TRIES = 60          # number of 1-second waits for LibreOffice to start
INDEX_UPDATE_PASSES = 2     # filling the TOC can push pages, so update once more


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
            pass   # losing the connection during the shutdown request is normal
    finally:
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
