"""One-off: extract the hero/seal glyph outlines from Ma Shan Zheng into src/glyphs.json.

Needs fontTools and the font file (not committed):
  python tools/extract_glyphs.py path/to/MaShanZheng-Regular.ttf

Glyph paths are emitted in a y-down frame: x 0..1000, y 0..1000 (ascender at 0).
The outlines are flattened and their edges gently displaced, so the ink looks
like it soaked into the paper. This is baked in here rather than done with SVG
filters at runtime, which were slow to paint.

tools/strokes.json holds hand-traced stroke centerlines (in stroke order) in the
same frame; they drive the brush-reveal mask.
"""
import json, math, random, sys
from pathlib import Path
from fontTools.pens.basePen import BasePen
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
STEP = 7  # font units between points on the flattened outline

font = TTFont(sys.argv[1])
glyphs, cmap = font.getGlyphSet(), font.getBestCmap()
ascent = font["hhea"].ascent
strokes = json.loads((ROOT / "tools/strokes.json").read_text(encoding="utf-8"))

rng = random.Random(11)
WAVES = [  # (amplitude, frequency) pairs: a slow wobble plus a fine feathered edge
    (rng.uniform(0.8, 1.2) * a, f, rng.uniform(0, math.tau), rng.uniform(0, math.tau))
    for a, f in [(3.2, 1 / 55), (2.4, 1 / 23), (1.3, 1 / 9)]
]


def wobble(x, y):
    dx = sum(a * math.sin(x * f + p + y * f * 0.7) for a, f, p, _ in WAVES)
    dy = sum(a * math.sin(y * f + q - x * f * 0.6) for a, f, _, q in WAVES)
    return x + dx, y + dy


class FlattenPen(BasePen):
    def __init__(self, glyphset):
        super().__init__(glyphset)
        self.contours, self.cur = [], None

    def _moveTo(self, p):
        self.cur = [p]
        self.contours.append(self.cur)

    def _lineTo(self, p):
        a = self.cur[-1]
        n = max(1, int(math.dist(a, p) / STEP))
        self.cur += [(a[0] + (p[0] - a[0]) * t / n, a[1] + (p[1] - a[1]) * t / n) for t in range(1, n + 1)]

    def _qCurveToOne(self, c, p):
        a = self.cur[-1]
        n = max(2, int((math.dist(a, c) + math.dist(c, p)) / STEP))
        for i in range(1, n + 1):
            t = i / n
            self.cur.append(tuple((1 - t) ** 2 * a[k] + 2 * (1 - t) * t * c[k] + t * t * p[k] for k in (0, 1)))

    def _curveToOne(self, c1, c2, p):
        a = self.cur[-1]
        n = max(3, int((math.dist(a, c1) + math.dist(c1, c2) + math.dist(c2, p)) / STEP))
        for i in range(1, n + 1):
            t = i / n
            self.cur.append(tuple(
                (1 - t) ** 3 * a[k] + 3 * (1 - t) ** 2 * t * c1[k] + 3 * (1 - t) * t * t * c2[k] + t ** 3 * p[k]
                for k in (0, 1)))

    def _closePath(self):
        pass


def outline(ch):
    pen = FlattenPen(glyphs)
    glyphs[cmap[ord(ch)]].draw(pen)
    parts = []
    for contour in pen.contours:
        pts = [wobble(x, ascent - y) for x, y in contour]
        parts.append("M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in pts) + "Z")
    return "".join(parts)


def length(pts):
    return round(sum(math.dist(a, b) for a, b in zip(pts, pts[1:])))


out = {}
for ch in "尹紫鸢":
    out[ch] = {
        "path": outline(ch),
        "strokes": [{"points": s, "length": length(s)} for s in strokes[ch]],
    }
(ROOT / "src/glyphs.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
print({k: len(v["path"]) for k, v in out.items()})
