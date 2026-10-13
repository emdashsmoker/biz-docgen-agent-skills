#!/usr/bin/env python3
"""sheet.py: 슬라이드 PNG 여러 장을 격자 1장으로 묶는 열람용 시트 생성

WHY: 슬라이드를 1장씩 열람하면 장 사이의 간격, 정렬, 서체 크기 편차가 보이지 않는다.
     3-6장을 한 이미지에 묶어야 인접 슬라이드와 비교하며 검수할 수 있다.

입력 파일 탐색 순서 (번호 n 기준)
1. render.sh 산출물 s-{n}.png (자릿수 1-3 자리 모두 탐색)
2. compare.py 산출물 cmp_{n:03d}.png

사용: python3 sheet.py <png_dir> <out.png> <n1,n2,...> [--cols 2]
"""
import os
import sys

from PIL import Image, ImageDraw

DEFAULT_COLS = 2
GAP_PX = 12          # 칸 사이 여백
LABEL_H_PX = 18      # 칸 위 번호 표기 높이
PAD_WIDTHS = (1, 2, 3)


def find_png(png_dir, n):
    for w in PAD_WIDTHS:
        p = os.path.join(png_dir, f"s-{n:0{w}d}.png")
        if os.path.exists(p):
            return p
    p = os.path.join(png_dir, f"cmp_{n:03d}.png")
    if os.path.exists(p):
        return p
    raise SystemExit(f"{png_dir} 에 {n}번 PNG 없음 (s-{n}.png 또는 cmp_{n:03d}.png)")


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
