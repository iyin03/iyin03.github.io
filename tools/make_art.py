"""One-off: turn scans of ink paintings into page art at static/img/art/<name>.webp.

Needs numpy + Pillow:
  python tools/make_art.py <source image> <name> [left top right bottom]

The optional crop is in fractions of the image (e.g. 0.06 0.02 0.94 0.98) to
trim mounting silk. The paper is then flattened to white (a max filter finds
the bare paper, which is divided out), and the result is stored as ink with
real transparency: over the site's light paper it matches a multiply blend, but
needs no blend mode, so the browser can scroll it as a plain GPU layer. The soft
fade toward the top-left (where the page text is) is baked into the alpha too.
Output is 1100px tall, RGBA WebP.
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parent.parent

src, name = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB")
if len(sys.argv) == 7:
    l, t, r, b = (float(v) for v in sys.argv[3:7])
    im = im.crop((int(im.width * l), int(im.height * t), int(im.width * r), int(im.height * b)))
im = im.resize((int(im.width * 1100 / im.height), 1100), Image.LANCZOS)

small = im.resize((max(1, im.width // 4), max(1, im.height // 4)))
paper = small.filter(ImageFilter.MaxFilter(15)).filter(ImageFilter.GaussianBlur(12)).resize(im.size, Image.BICUBIC)
a = np.asarray(im, dtype=float)
p = np.asarray(paper, dtype=float)
out = np.clip(a / np.maximum(p, 1) * 1.04, 0, 1)
out = np.where(out.mean(2, keepdims=True) > 0.93, 1.0, out)

# Ink as alpha: the darkest channel decides coverage; the colour is solved so that
# over white it reproduces the scan exactly (seals keep their red).
alpha = 1 - out.min(2)
color = np.where(alpha[..., None] > 1e-3, (out - (1 - alpha[..., None])) / np.maximum(alpha[..., None], 1e-3), 0)
color = np.clip(color, 0, 1)

# Baked fade: an ellipse centred low and right, solid in the middle, gone by the
# top-left edges, so the painting dissolves into the paper toward the content.
h, w = alpha.shape
yy, xx = np.mgrid[0:h, 0:w]
t = np.hypot((xx - 0.72 * w) / (0.80 * w), (yy - 0.70 * h) / (0.85 * h))
fade = np.clip((0.78 - t) / (0.78 - 0.38), 0, 1)
fade = fade * fade * (3 - 2 * fade)          # smoothstep
alpha *= fade

# Where the ink is almost gone, a flat colour compresses far better than noise.
color = np.where(alpha[..., None] < 0.02, 0.15, color)
rgba = np.dstack([color, alpha])
dest = ROOT / "static/img/art" / f"{name}.webp"
dest.parent.mkdir(parents=True, exist_ok=True)
Image.fromarray((rgba * 255).astype(np.uint8), "RGBA").save(dest, quality=80, alpha_quality=70, method=6)
print(dest.name, im.size, dest.stat().st_size, "bytes")
