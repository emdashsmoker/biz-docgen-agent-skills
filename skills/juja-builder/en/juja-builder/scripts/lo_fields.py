"""Opens a DOCX with LibreOffice, updates its fields and saves a DOCX copy.
docx_report.py runs this in an interpreter that has the LibreOffice Python bridge (uno).
Why uno: `soffice --convert-to docx` writes the stored PAGEREF values as they are without recalculating them. The page numbers are written only when the field update is called directly
The copy is used only to look up page numbers. LibreOffice rewrites the formatting on save, so the copy is not used as output

Usage: python lo_fields.py <soffice path> <input DOCX> <output DOCX> <LibreOffice user profile URL>
"""
import os
import subprocess
import sys
import time

import uno
from com.sun.star.beans import PropertyValue

CONNECT_TRIES = 60                    # number of 1-second waits for LibreOffice to start
DOCX_FILTER = "MS Word 2007 XML"      # name of the LibreOffice DOCX export filter


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
            pass   # the connection dropping during the terminate request is normal
    finally:
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
