"""One-off: generate the 1200x630 link-preview image at static/og.png.

Needs Pillow and three font files (not committed):
  python tools/make_og.py MaShanZheng-Regular.ttf AlegreyaSans-Medium.ttf AlegreyaSans-Regular.ttf

Composed from the site's own parts: the paper texture, the brush name in a
vertical column, the carved seal, and the English name.
"""
import json
import random
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
brush_ttf, medium_ttf, regular_ttf = sys.argv[1:4]
site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))

W, H = 1200, 630
INK, BODY, GREY, SEAL = (22, 23, 20), (43, 45, 40), (79, 82, 73), (179, 54, 43)

img = Image.new("RGB", (W, H))
paper = Image.open(ROOT / "static/img/paper.webp").convert("RGB")
for x in range(0, W, paper.width):
    for y in range(0, H, paper.height):
        img.paste(paper, (x, y))
d = ImageDraw.Draw(img)

# Brush column, right of centre.
brush = ImageFont.truetype(brush_ttf, 150)
cx, y = 905, 40
for ch in site["name_zh"]:
    d.text((cx, y), ch, font=brush, fill=INK, anchor="ma")
    y += 165

# Seal: the surname carved out of a vermilion square, with a slightly uneven edge.
rng = random.Random(3)
seal = Image.new("RGBA", (78, 78), (0, 0, 0, 0))
sd = ImageDraw.Draw(seal)
edge = [(rng.uniform(1, 4), rng.uniform(1, 4)), (rng.uniform(74, 77), rng.uniform(1, 4)),
        (rng.uniform(74, 77), rng.uniform(74, 77)), (rng.uniform(1, 4), rng.uniform(74, 77))]
sd.polygon(edge, fill=SEAL + (255,))
sd.text((39, 39), site["name_zh"][0], font=ImageFont.truetype(brush_ttf, 56), fill=(0, 0, 0, 0), anchor="mm")
img.paste(seal, (800, 528), seal)

# English, left.
d.text((96, 236), site["name"], font=ImageFont.truetype(medium_ttf, 92), fill=INK)
tag = ImageFont.truetype(regular_ttf, 34)
d.text((98, 352), "Statistics & Machine Learning", font=tag, fill=BODY)
d.text((98, 396), "Carnegie Mellon University", font=tag, fill=BODY)
d.text((98, 536), site["url"].replace("https://", ""), font=ImageFont.truetype(regular_ttf, 26), fill=GREY)

out = ROOT / "static/og.png"
img.save(out, optimize=True)
print(out, out.stat().st_size, "bytes")
