"""One-off: generate the tileable xuan-paper texture at static/img/paper.webp.

Needs numpy + Pillow. Low-frequency cloudiness (FFT-filtered, so it tiles) plus
sparse long fibers, kept within about +/-3% luminance of the paper tone so text
contrast holds anywhere on the page.
"""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

N = 512
QUALITY = 95  # lower settings macroblock the fibers away; 95 is ~20 KB
PAPER = np.array([0xDA, 0xD9, 0xCD], dtype=float)
rng = np.random.default_rng(7)


def periodic_noise(falloff):
    f = np.fft.fftfreq(N)
    r = np.sqrt(f[:, None] ** 2 + f[None, :] ** 2)
    r[0, 0] = 1
    spec = np.fft.fft2(rng.standard_normal((N, N))) / r ** falloff
    n = np.real(np.fft.ifft2(spec))
    return (n - n.mean()) / n.std()


cloud = periodic_noise(1.6) * 0.012 + periodic_noise(0.6) * 0.006

# Fibers: drawn on a 3x3 tiled canvas, then the centre tile is kept, so they wrap.
fib = Image.new("L", (N * 3, N * 3), 0)
d = ImageDraw.Draw(fib)
for _ in range(260):
    x, y = rng.uniform(N, 2 * N, 2)
    a = rng.uniform(0, np.pi)
    pts = []
    for _ in range(int(rng.uniform(8, 30))):
        pts.append((x, y))
        a += rng.normal(0, 0.25)
        x += np.cos(a) * 4
        y += np.sin(a) * 4
    shade = int(rng.uniform(90, 255))
    for ox in (-N, 0, N):
        for oy in (-N, 0, N):
            d.line([(px + ox, py + oy) for px, py in pts], fill=shade, width=1)
fib = fib.filter(ImageFilter.GaussianBlur(0.6)).crop((N, N, 2 * N, 2 * N))
fibers = np.asarray(fib, dtype=float) / 255

lum = 1 + cloud - fibers * 0.035 + rng.standard_normal((N, N)) * 0.004
rgb = np.clip(PAPER[None, None, :] * lum[..., None], 0, 255).astype(np.uint8)
out = Path(__file__).resolve().parent.parent / "static/img/paper.webp"
Image.fromarray(rgb).save(out, quality=QUALITY, method=6)
print(out.stat().st_size, "bytes; lum range", lum.min().round(3), lum.max().round(3))
