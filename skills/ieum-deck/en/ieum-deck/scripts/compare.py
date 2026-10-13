#!/usr/bin/env python3
"""compare.py: builds contrast images with a source PDF page and a reproduction PNG side by side and prints the pixel difference ratio

WHY: When custom slides are extracted to a coordinate file and played back, this finds slides that drift from the source both by eye and by number.
     The difference ratio is the share of pixels whose brightness difference between the two images exceeds a threshold. A larger value means more drift

Usage: python3 compare.py <source.pdf> <reproduction png dir> <output dir> <pair list> [dpi]
- Pair list format: reproNumber:sourcePage,... (e.g. 1:1,2:2,3:4 contrasts reproduction s-01 with source page 1)
- Reproduction PNGs are render.sh outputs (whichever of s-1.png, s-01.png, s-001.png exists)
- Output: <output dir>/cmp_{sourcePage:03d}.png and stdout lines "sourcePage reproNumber diffRatio path"
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw

DEFAULT_DPI = 60
DIFF_THRESHOLD = 40   # Only pixels whose 0-255 brightness difference exceeds this count as different (ignores antialiasing noise)
GAP_PX = 10           # Gap between the left and right images
LABEL_H_PX = 24       # Height of the label line at the top
PAD_WIDTHS = (1, 2, 3)


def render_pdf_page(pdf, page, dpi, out_stem):
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png", "-singlefile", pdf, out_stem], check=True)
    return out_stem + ".png"


def find_repro(png_dir, n):
    for w in PAD_WIDTHS:
        p = os.path.join(png_dir, f"s-{n:0{w}d}.png")
        if os.path.exists(p):
            return p
    raise SystemExit(f"No reproduction PNG for number {n} in {png_dir}")


def diff_ratio(a, b):
    diff = ImageChops.difference(a, b).convert("L")
    return float((np.asarray(diff) > DIFF_THRESHOLD).mean())


def side_by_side(a, b, left_label, right_label):
    sheet = Image.new("RGB", (a.size[0] * 2 + GAP_PX, a.size[1] + LABEL_H_PX), "white")
    sheet.paste(a, (0, LABEL_H_PX))
    sheet.paste(b, (a.size[0] + GAP_PX, LABEL_H_PX))
    d = ImageDraw.Draw(sheet)
    d.text((4, 4), left_label, fill="black")
    d.text((a.size[0] + GAP_PX + 4, 4), right_label, fill="black")
    return sheet


def main():
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    pdf, png_dir, out_dir, pairs = sys.argv[1:5]
    dpi = int(sys.argv[5]) if len(sys.argv) > 5 else DEFAULT_DPI
    os.makedirs(out_dir, exist_ok=True)
    for pair in pairs.split(","):
        ri, op = (int(x) for x in pair.split(":"))
        orig_png = render_pdf_page(pdf, op, dpi, os.path.join(out_dir, f"orig_{op:03d}"))
        a = Image.open(orig_png).convert("RGB")
        b = Image.open(find_repro(png_dir, ri)).convert("RGB").resize(a.size)
        ratio = diff_ratio(a, b)
        out = os.path.join(out_dir, f"cmp_{op:03d}.png")
        side_by_side(a, b, f"orig p{op}", f"repro s{ri}  diff={ratio:.3f}").save(out)
        os.remove(orig_png)
        print(f"{op}\t{ri}\t{ratio:.3f}\t{out}")


if __name__ == "__main__":
    main()
