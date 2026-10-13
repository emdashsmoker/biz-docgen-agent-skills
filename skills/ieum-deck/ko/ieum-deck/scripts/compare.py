#!/usr/bin/env python3
"""compare.py: 원본 PDF 쪽과 재현본 PNG 를 좌우로 붙인 대조 이미지를 만들고 픽셀 차분 비율을 출력

WHY: 커스텀 슬라이드를 좌표 파일로 추출해 재생할 때 원본과 어긋난 슬라이드를 눈과 수치로 함께 찾기 위함.
     차분 비율은 두 이미지에서 밝기 차가 임계값을 넘는 픽셀의 비율이며 값이 클수록 어긋남이 큼

사용: python3 compare.py <원본.pdf> <재현 png 디렉터리> <출력 디렉터리> <쌍 목록> [dpi]
- 쌍 목록 형식: 재현번호:원본쪽,... (예: 1:1,2:2,3:4 는 재현본 s-01 과 원본 1쪽을 대조)
- 재현 png 는 render.sh 산출물(s-1.png, s-01.png, s-001.png 중 존재하는 이름)
- 출력: <출력 디렉터리>/cmp_{원본쪽:03d}.png 와 표준 출력 "원본쪽 재현번호 차분비율 경로"
"""
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageChops, ImageDraw

DEFAULT_DPI = 60
DIFF_THRESHOLD = 40   # 0-255 밝기 차 가운데 이 값을 넘는 픽셀만 차이로 셈 (안티에일리어싱 잡음 제외)
GAP_PX = 10           # 좌우 이미지 사이 여백
LABEL_H_PX = 24       # 상단 표기 줄 높이
PAD_WIDTHS = (1, 2, 3)


def render_pdf_page(pdf, page, dpi, out_stem):
    subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(page), "-l", str(page), "-png", "-singlefile", pdf, out_stem], check=True)
    return out_stem + ".png"


def find_repro(png_dir, n):
    for w in PAD_WIDTHS:
        p = os.path.join(png_dir, f"s-{n:0{w}d}.png")
        if os.path.exists(p):
            return p
    raise SystemExit(f"{png_dir} 에 재현본 {n}번 PNG 없음")


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
