#!/usr/bin/env python3
"""sheet.py: builds a contact sheet that joins several slide PNGs into one grid image

WHY: Viewing slides one at a time hides differences in spacing, alignment and font size between slides.
     Joining 3-6 slides in one image lets the review compare neighboring slides.

Input lookup order (for number n)
1. render.sh output s-{n}.png (1-3 digit padding all searched)
2. compare.py output cmp_{n:03d}.png

Usage: python3 sheet.py <png_dir> <out.png> <n1,n2,...> [--cols 2]
"""
import os
import sys

from PIL import Image, ImageDraw

DEFAULT_COLS = 2
GAP_PX = 12          # Gap between cells
LABEL_H_PX = 18      # Height of the number label above each cell
PAD_WIDTHS = (1, 2, 3)


def find_png(png_dir, n):
    for w in PAD_WIDTHS:
        p = os.path.join(png_dir, f"s-{n:0{w}d}.png")
        if os.path.exists(p):
            return p
    p = os.path.join(png_dir, f"cmp_{n:03d}.png")
    if os.path.exists(p):
        return p
    raise SystemExit(f"No PNG for number {n} in {png_dir} (s-{n}.png or cmp_{n:03d}.png)")


def build_sheet(paths, nums, cols):
    ims = [Image.open(p).convert("RGB") for p in paths]
    cw = max(i.size[0] for i in ims)
    ch = max(i.size[1] for i in ims) + LABEL_H_PX
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cw + (cols - 1) * GAP_PX, rows * ch + (rows - 1) * GAP_PX), "white")
    draw = ImageDraw.Draw(sheet)
    for k, (im, n) in enumerate(zip(ims, nums)):
        x = (k % cols) * (cw + GAP_PX)
        y = (k // cols) * (ch + GAP_PX)
        draw.text((x + 2, y + 2), f"#{n}", fill="black")
        sheet.paste(im, (x, y + LABEL_H_PX))
    return sheet


def main():
    args = sys.argv[1:]
    cols = DEFAULT_COLS
    if "--cols" in args:
        i = args.index("--cols")
        cols = int(args[i + 1])
        del args[i:i + 2]
    if len(args) != 3:
        raise SystemExit(__doc__)
    png_dir, out, spec = args
    nums = [int(x) for x in spec.split(",") if x.strip()]
    sheet = build_sheet([find_png(png_dir, n) for n in nums], nums, max(1, cols))
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
