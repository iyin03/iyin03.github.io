"""One-off: paint the home page's ink irises procedurally into static/img/art/iris.webp.

Needs numpy + Pillow:  python tools/make_iris.py

Xieyi-style composition: four blooms high on the sheet, sword leaves sweeping up
from the lower left. Everything is an ink-density field (0 = paper, 1 = black):
leaves are tapered dry-brush strokes, petals are wet washes that pool darker at
their edges, with fine veins. Seeded, so every run paints the same picture.
Output is ink on white, for `mix-blend-mode: multiply`.
"""
import math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
W, H, SS = 540, 1300, 2          # output size, supersampling for smooth shapes
rng = np.random.default_rng(1022)
ink = np.zeros((H * SS, W * SS))


def grain(sigma):
    """Smooth noise in floating point (FFT Gaussian), normalized to unit variance."""
    n = rng.standard_normal(ink.shape)
    fy = np.fft.fftfreq(ink.shape[0])[:, None]
    fx = np.fft.fftfreq(ink.shape[1])[None, :]
    g = np.exp(-2 * (math.pi * sigma) ** 2 * (fx ** 2 + fy ** 2))
    a = np.real(np.fft.ifft2(np.fft.fft2(n) * g))
    return (a - a.mean()) / (a.std() + 1e-9)


FINE, COARSE, BLOT = grain(1.6), grain(7), grain(22)


def lay(layer, density):
    """Wet ink over ink: densities combine like stacked transparent washes."""
    global ink
    ink = 1 - (1 - ink) * (1 - np.clip(layer * density, 0, 1))


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * p3)


def leaf(p0, p1, p2, p3, width, density, dry=0.55):
    """A sword leaf in one pressed stroke: thick in the middle, tapering to a hair at
    the tip. It is built from separate bristle lines, so it splits into dry streaks
    the way a loaded brush does, and breaks up toward the tail."""
    pts = bezier(*(np.array(p, float) * SS for p in (p0, p1, p2, p3)), 260)
    n = len(pts)
    prof = np.array([math.sin(math.pi * min(1, (k / (n - 1)) * 1.12)) ** 0.6 * (1 - k / (n - 1)) ** 0.3 + 0.03 for k in range(n)])
    tang = np.gradient(pts, axis=0)
    nrm = np.stack([-tang[:, 1], tang[:, 0]], 1) / (np.hypot(tang[:, 0], tang[:, 1])[:, None] + 1e-6)
    layer = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(layer)
    width *= 1.7
    bristles = 13
    for b in range(bristles):
        off = (b / (bristles - 1) - 0.5) * 0.92
        tone = 1.0 if b in (0, bristles - 1) and rng.random() < 0.6 else rng.uniform(0.2, 1.0)
        # each bristle runs out of ink at its own point near the tail
        stop = n - int(rng.uniform(0, dry) * n * 0.35)
        line = pts[:stop] + nrm[:stop] * (off * width * SS * prof[:stop, None])
        bw = max(1, int(width * SS / bristles * 1.05 * rng.uniform(0.7, 1.25)))
        # Flying white: a few breaks in the tail half, where the brush runs dry.
        gaps = []
        for _ in range(int(rng.integers(0, 4) * dry + 0.5)):
            g0 = int(rng.uniform(0.45, 0.95) * len(line))
            gaps.append((g0, g0 + int(rng.uniform(0.03, 0.1) * n)))
        for k in range(len(line) - 1):
            if any(g0 <= k < g1 for g0, g1 in gaps):
                continue
            v = int(255 * tone * (0.75 + 0.25 * prof[k] / prof.max()))
            d.line([tuple(line[k]), tuple(line[k + 1])], fill=v, width=bw)
    m = np.asarray(layer.filter(ImageFilter.GaussianBlur(0.45 * SS)), float) / 255
    lay(m, density * 1.15)


def petal(base, angle, length, width, density, ruffle=0.26, tone=(1.0, 0.38)):
    """A wet-wash petal: dark at the base, paling toward a ruffled tip, ink pooled at the edge,
    and fine veins fanning out from the throat."""
    bx, by = base[0] * SS, base[1] * SS
    L, Wd = length * SS, width * SS
    ca, sa = math.cos(angle), math.sin(angle)
    ph1, ph2 = rng.uniform(0, 6.3, 2)
    top, bot = [], []
    for k in range(80):
        u = k / 79
        half = Wd / 2 * (u ** 0.55) * ((1 - u) ** 0.3) * 1.9
        rf = 1 + ruffle * math.sin(5 * math.pi * u + ph1) * u + 0.045 * math.sin(11 * math.pi * u + ph2) * u ** 3
        top.append((u * L, half * rf))
        bot.append((u * L, -half * (1 + ruffle * math.sin(4 * math.pi * u + ph2) * u)))
    outline = top + bot[::-1]
    pts = [(bx + a * ca - s * sa, by + a * sa + s * ca) for a, s in outline]
    mask = Image.new("L", (W * SS, H * SS), 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.2 * SS)), float) / 255
    yy, xx = np.mgrid[0:H * SS, 0:W * SS]
    along = ((xx - bx) * ca + (yy - by) * sa) / L
    grad = tone[0] + (tone[1] - tone[0]) * np.clip(along, 0, 1)
    # Edge pooling: the wash dries darker at its boundary.
    soft = np.asarray(mask.filter(ImageFilter.GaussianBlur(5 * SS)), float) / 255
    edge = np.clip(m - soft, 0, 1) * 2.4 * np.clip(0.55 + 0.45 * BLOT, 0.15, 1.3)
    wash = m * grad * np.clip(0.88 + 0.3 * BLOT + 0.14 * COARSE + 0.03 * FINE, 0.35, 1.3) + edge * 0.55
    lay(wash, density)
    veins = Image.new("L", mask.size, 0)
    dv = ImageDraw.Draw(veins)
    for v in np.linspace(-0.3, 0.3, 6) + rng.uniform(-0.04, 0.04, 6):
        a2 = angle + v * width / length * 1.5
        r0, r1 = L * rng.uniform(0.1, 0.2), L * rng.uniform(0.45, 0.85)
        bend = rng.uniform(-0.12, 0.12)
        mid = (r0 + r1) / 2
        dv.line([(bx + r0 * math.cos(a2), by + r0 * math.sin(a2)),
                 (bx + mid * math.cos(a2 + bend), by + mid * math.sin(a2 + bend)),
                 (bx + r1 * math.cos(a2 + bend * 1.5), by + r1 * math.sin(a2 + bend * 1.5))],
                fill=int(rng.uniform(150, 255)), width=max(1, SS))
    vm = np.asarray(veins.filter(ImageFilter.GaussianBlur(0.6 * SS)), float) / 255 * m
    lay(vm, density * 0.5)


def bloom(cx, cy, size, tilt, density):
    """An iris: three broad falls drooping outward, three narrower standards rising,
    a dark throat with a few quick stamen marks."""
    for k, a in enumerate((-0.25, 1.35, 2.95)):
        petal((cx, cy), a + tilt, size * rng.uniform(0.95, 1.15), size * 0.95, density)
    for a in (-1.95, -1.25, -0.6):
        petal((cx, cy), a + tilt, size * rng.uniform(0.6, 0.75), size * 0.5, density, tone=(1.0, 0.55), ruffle=0.18)
    throat = Image.new("L", (W * SS, H * SS), 0)
    d = ImageDraw.Draw(throat)
    for _ in range(9):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(2, size * 0.28) * SS
        x, y = cx * SS + r * math.cos(a), cy * SS + r * math.sin(a)
        d.line([(cx * SS, cy * SS), (x, y)], fill=255, width=int(rng.uniform(1.5, 3.5) * SS))
    lay(np.asarray(throat.filter(ImageFilter.GaussianBlur(0.7 * SS)), float) / 255, 0.85)


# Leaves first, so the blooms' washes sit over them.
leaf((60, 1290), (90, 1000), (150, 760), (300, 470), 15, 0.62)
leaf((40, 1280), (60, 1080), (40, 860), (10, 700), 12, 0.55)
leaf((110, 1290), (170, 1080), (330, 900), (520, 760), 13, 0.58)
leaf((150, 1290), (210, 1120), (340, 1000), (520, 1000), 10, 0.45, dry=0.8)
leaf((200, 1280), (260, 1150), (320, 1030), (410, 870), 9, 0.4, dry=0.8)
leaf((300, 1290), (330, 1180), (380, 1120), (470, 1180), 10, 0.42)
leaf((150, 900), (250, 650), (380, 380), (520, 170), 9, 0.5)
leaf((230, 620), (320, 450), (420, 260), (530, 90), 8, 0.45, dry=0.8)
# Stems up to the blooms.
leaf((140, 1200), (170, 900), (230, 650), (285, 300), 6, 0.6)
leaf((120, 1150), (110, 950), (90, 820), (70, 720), 5, 0.55)

bloom(300, 250, 105, 0.15, 0.55)
bloom(240, 470, 130, -0.1, 0.6)
bloom(330, 640, 105, 0.3, 0.52)
bloom(70, 720, 95, -0.35, 0.5)

# Ink soaks a little into the fibres, then sits on the paper's grain.
img = Image.fromarray((np.clip(ink, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6 * SS))
dens = np.asarray(img, float) / 255
dens *= np.clip(1 + 0.03 * FINE, 0.92, 1.06)
INK = np.array([38, 39, 35], float)
rgb = 255 - dens[..., None] * (255 - INK)
out = Image.fromarray(rgb.astype(np.uint8)).resize((W, H), Image.LANCZOS)
dest = ROOT / "static/img/art/iris.webp"
out.save(dest, quality=82, method=6)
print(dest.name, out.size, dest.stat().st_size, "bytes")
