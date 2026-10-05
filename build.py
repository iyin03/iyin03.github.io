"""Build the static site into dist/.

    python build.py            # production build (draft projects skipped)
    python build.py --drafts   # include projects marked "draft": true

Standard library only. Content lives in content/*.json; the hero glyph outlines
and stroke data in src/glyphs.json (see tools/extract_glyphs.py).
"""
import json
import shutil
import sys
from html import escape
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
SHOW_DRAFTS = "--drafts" in sys.argv

site = json.loads((ROOT / "content/site.json").read_text(encoding="utf-8"))
projects = [
    p
    for p in json.loads((ROOT / "content/projects.json").read_text(encoding="utf-8"))
    if SHOW_DRAFTS or not p.get("draft")
]
glyphs = json.loads((ROOT / "src/glyphs.json").read_text(encoding="utf-8"))
art = json.loads((ROOT / "content/art.json").read_text(encoding="utf-8"))

# Section markers are display-only; the brush font is subset to exactly these.
MARKERS = {"work": "作品", "projects": "项目", "about": "关于", "resume": "履历", "contact": "联系"}
SECTION_NAMES = {"work": "Work", "projects": "Projects"}
BRUSH_TEXT = "".join(sorted(set("".join(MARKERS.values()))))
FONTS = [
    "https://fonts.googleapis.com/css2?family=Alegreya+Sans:ital,wght@0,400;0,500;0,700;1,400&display=swap",
    "https://fonts.googleapis.com/css2?family=Ma+Shan+Zheng&display=swap&text=" + quote(BRUSH_TEXT),
]

e = lambda s: escape(str(s), quote=True)


# ---------------------------------------------------------------- brush & seal

GLYPH_STEP = 960  # vertical advance between characters, in font units
STROKE_WIDTH = 130  # mask brush width; wide enough to cover each traced stroke


def brush_column():
    """The name, one vertical column, each glyph revealed through a stroke-order mask."""
    chars = site["name_zh"]
    height = GLYPH_STEP * (len(chars) - 1) + 1000
    defs, body = [], []
    for i, ch in enumerate(chars):
        g = glyphs[ch]
        defs.append(f'<path id="g{i}" d="{g["path"]}"/>')
        strokes = "".join(
            f'<polyline class="stroke" pathLength="1" data-len="{s["length"]}" '
            f'points="{" ".join(f"{x},{y}" for x, y in s["points"])}"/>'
            for s in g["strokes"]
        )
        defs.append(
            f'<mask id="m{i}" maskUnits="userSpaceOnUse" x="-100" y="-100" width="1200" height="1200">'
            f"{strokes}</mask>"
        )
        body.append(
            f'<g class="char" transform="translate(0 {i * GLYPH_STEP})">'
            f'<use href="#g{i}" class="bleed" data-mask="url(#m{i})"/>'
            f'<use href="#g{i}" class="ink" data-mask="url(#m{i})"/>'
            f'<use href="#g{i}" class="settle"/>'
            "</g>"
        )
    return (
        f'<svg class="brush-svg" viewBox="-20 -20 1040 {height + 40}" aria-hidden="true" focusable="false">'
        "<defs>"
        + "".join(defs)
        + "</defs>"
        + "".join(body)
        + "</svg>"
    )


def seal_svg(cls="seal", standalone=False):
    """白文印: the surname carved out of a vermilion square, so the paper shows through.

    The uneven edge and the specks where ink didn't take are generated here
    (seeded, so every build matches) instead of with runtime SVG filters.
    """
    import math
    import random

    rng = random.Random(3)
    g = glyphs[site["name_zh"][0]]["path"]
    mask_id = "carve-fav" if standalone else "carve"
    edge = []
    for side in range(4):
        for k in range(12):
            t = k / 12
            x, y = [(40 + 920 * t, 40), (960, 40 + 920 * t), (960 - 920 * t, 960), (40, 960 - 920 * t)][side]
            j = rng.uniform(-9, 9)
            edge.append((x + (j if side % 2 else 0), y + (0 if side % 2 else j)))
    rim = "M" + "L".join(f"{x:.0f} {y:.0f}" for x, y in edge) + "Z"
    specks = "".join(
        f'<circle cx="{rng.uniform(60, 940):.0f}" cy="{rng.uniform(60, 940):.0f}" r="{rng.uniform(4, 15):.0f}"/>'
        for _ in range(28)
    )
    ns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ' aria-hidden="true" focusable="false"'
    return (
        f'<svg class="{cls}" viewBox="0 0 1000 1000"{ns}>'
        f'<defs><mask id="{mask_id}">'
        '<rect width="1000" height="1000" fill="#fff"/>'
        f'<g fill="#000"><path d="{g}" transform="translate(150 140) scale(.72)"/>{"" if standalone else specks}</g>'
        "</mask></defs>"
        f'<path d="{rim}" fill="#B3362B" mask="url(#{mask_id})"/></svg>'
    )


# ---------------------------------------------------------------- page shell

NAV = [("work", "Work"), ("projects", "Projects"), ("about", "About"), ("resume", "Resume"), ("contact", "Contact")]


def page(title, description, body, path="/", current=None, write=False, home=False, credit=""):
    canonical = site["url"].rstrip("/") + path
    nav = "".join(
        f'<li><a href="/{k}/"{CURRENT if k == current else ""}>{label}</a></li>' for k, label in NAV
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(description)}">
<link rel="canonical" href="{e(canonical)}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(description)}">
<meta property="og:url" content="{e(canonical)}">
<meta property="og:type" content="website">
<meta property="og:image" content="{e(site["url"].rstrip("/"))}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{e(site["name"])}, with her Chinese name {e(site["name_zh"])} in brush calligraphy">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#DAD9CD">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
{"".join(f'<link rel="stylesheet" href="{e(u)}">' for u in FONTS)}
<link rel="stylesheet" href="/vendor/lenis.css">
<link rel="stylesheet" href="/styles.css">
<script src="/site.js" defer></script>
<script src="/vendor/lenis.min.js" defer></script>
<script src="/vendor/gsap.min.js" defer></script>
<script src="/vendor/ScrollTrigger.min.js" defer></script>
<script src="/motion.js" defer></script>
<script>document.documentElement.classList.add('js')</script>
</head>
<body{' class="home"' if home else ""}>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header{" site-header-home" if home else ""}">
  {"" if home else '<a class="wordmark" href="/">Home</a>'}
  <nav aria-label="Main">
    <ul>{nav}</ul>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="site-footer">
  <p>{e(site["name"])}, 2026. Brush lettering set in Ma Shan Zheng.{credit}</p>
</footer>
{"<script>" + (ROOT / "src/write.js").read_text(encoding="utf-8") + "</script>" if write else ""}
</body>
</html>
"""


CURRENT = ' aria-current="page"'


def marker(key):
    chars = "".join(f'<span class="mk">{c}</span>' for c in MARKERS[key])
    return f'<p class="marker" lang="zh-Hans" aria-hidden="true">{chars}</p>'


def project_url(p):
    return f'/{p.get("section", "work")}/{p["slug"]}/'


def section_page(key, title, description, inner, prose=True):
    """One section as its own page: the vertical marker in the rail, a page title, then content."""
    body = f"""
<section class="section page-section" aria-labelledby="{key}-h">
  {marker(key)}
  <div class="section-body{" prose" if prose else ""}">
    <h1 id="{key}-h" class="page-title">{e(title)}</h1>
    {inner}
  </div>
  {page_art(key)}
</section>"""
    return page(f'{title}: {site["name"]}', description, body, path=f"/{key}/", current=key, credit=art_credit(key))


def art_credit(key):
    a = art.get(key)
    if not a:
        return ""
    return (f' Painting: {e(a["artist"])}, <a href="{e(a["url"])}"><i>{e(a["title"])}</i></a>, '
            f'{e(a["date"])}, Cleveland Museum of Art, public domain.')


def page_art(key):
    """A public-domain ink painting beside each section page, credited to its museum page."""
    a = art.get(key)
    if not a:
        return ""
    return f"""<img class="page-art" src="{e(a["src"])}" alt="" width="{a["width"]}" height="{a["height"]}" decoding="async">"""


# ---------------------------------------------------------------- home


def home():
    s = site
    body = f"""
<section class="hero" aria-labelledby="hero-name">
  <div class="ink-fog" aria-hidden="true"></div>
  <img class="hero-art" src="/img/art/iris.webp" alt="" width="540" height="1300" decoding="async">
  <h1 id="hero-name" class="hero-name">{e(s["name"])}</h1>
  <p class="hero-tagline">{e(s["tagline"])}</p>
  <div class="hero-rest">
    <p class="hero-intro">{e(s["intro"])}</p>
    <ul class="actions">
      <li><a class="button" href="{e(s["resume"])}" download>Download resume (PDF)</a></li>
      <li><a href="mailto:{e(s["email"])}">{e(s["email"])}</a></li>
      <li><a href="{e(s["github"])}">GitHub</a></li>
      <li><a href="{e(s["linkedin"])}">LinkedIn</a></li>
    </ul>
  </div>
  <figure class="brush">
    {brush_column()}
    <div class="signature">
      {seal_svg()}
      <figcaption class="gloss"><span lang="zh-Hans">{e(s["name_zh"])}</span>, <i lang="zh-Latn-pinyin">{e(s["name_zh_pinyin"])}</i>. {e(s["name_zh_gloss"])}</figcaption>
    </div>
  </figure>
</section>
"""
    return page(
        f'{s["name"]}: Statistics & Machine Learning at Carnegie Mellon',
        s["description"],
        body,
        write=True,
        home=True,
    )


# ---------------------------------------------------------------- section pages


def project_entry(p):
    return f"""
      <article class="entry">
        <div class="entry-main">
          <h2 class="entry-name"><a href="{project_url(p)}">{e(p["title"])}</a></h2>
          <p class="entry-outcome">{e(p["outcome"])}</p>
          <p class="entry-summary">{e(p["summary"])}</p>
          <dl class="facts">
            <dt>Role</dt><dd>{e(p["role"])}</dd>
            <dt>Methods</dt><dd>{e(p["methods"])}</dd>
            <dt>Stack</dt><dd>{e(p["stack"])}</dd>
          </dl>
        </div>
        <p class="entry-meta">
          <span class="entry-org">{e(p["org"])}</span>
          <span class="quiet">{e(p["kind"])}, {e(p["dates"])}</span>
        </p>
      </article>"""


def entries_page(key, description):
    items = [p for p in projects if p.get("section", "work") == key]
    inner = f'<div class="entries">{"".join(project_entry(p) for p in items)}\n    </div>'
    return section_page(key, SECTION_NAMES[key], description, inner, prose=False)


def about_page():
    s = site
    skills = "".join(f"<dt>{e(k['label'])}</dt><dd>{e(k['items'])}</dd>" for k in s["skills"])
    inner = f"""
    {"".join(f"<p>{e(t)}</p>" for t in s["about"])}
    <h2 class="sub">Tools I use</h2>
    <dl class="facts facts-wide">{skills}</dl>
    <h2 class="sub">Relevant coursework</h2>
    <p>{e(s["coursework"])}</p>"""
    return section_page("about", "About", s["description"], inner)


def resume_page():
    s = site
    inner = f"""
    <p>One page, last updated {e(s["resume_updated"])}.</p>
    <ul class="actions">
      <li><a class="button" href="{e(s["resume"])}" download>Download resume (PDF)</a></li>
      <li><a href="{e(s["resume"])}" target="_blank" rel="noopener">Open it in a new tab</a></li>
    </ul>
    <object class="resume-preview" data="{e(s["resume"])}#view=FitH" type="application/pdf" aria-label="Preview of the resume">
      <p>This browser can’t show the PDF here. <a href="{e(s["resume"])}">Open the resume</a>.</p>
    </object>"""
    return section_page("resume", "Resume", f'{s["name"]}’s one-page resume, as a PDF.', inner)


def contact_page():
    s = site
    inner = f"""
    <p>Email is the fastest way to reach me.</p>
    <p class="contact-email">
      <a href="mailto:{e(s["email"])}">{e(s["email"])}</a>
      <button type="button" class="copy" data-copy="{e(s["email"])}" hidden>Copy email</button>
      <span class="copy-status" role="status"></span>
    </p>
    <p class="quiet">Or my personal address, <a href="mailto:{e(s["email_personal"])}">{e(s["email_personal"])}</a>.</p>
    <ul class="links">
      <li><a href="{e(s["github"])}">GitHub</a></li>
      <li><a href="{e(s["linkedin"])}">LinkedIn</a></li>
    </ul>"""
    return section_page("contact", "Contact", f'How to reach {s["name"]}.', inner)


# ---------------------------------------------------------------- project pages


def figure(f):
    """A real artifact (chart, screenshot). Click opens the full-size image."""
    return f"""
    <figure class="artifact{f" artifact-{f['kind']}" if f.get("kind") else ""}">
      <a href="{e(f["src"])}"><img src="{e(f["src"])}" alt="{e(f["alt"])}" width="{f["width"]}" height="{f["height"]}" loading="lazy" decoding="async"></a>
      <figcaption>{e(f["caption"])}</figcaption>
    </figure>"""


def next_project(p):
    """The next project in the same section, wrapping round, as a large link."""
    same = [q for q in projects if q.get("section", "work") == p.get("section", "work")]
    if len(same) < 2:
        return ""
    nxt = same[(same.index(p) + 1) % len(same)]
    return f"""
    <nav class="next" aria-label="Next project">
      <p class="next-label">Next project</p>
      <p class="next-name"><a href="{project_url(nxt)}">{e(nxt["title"])}</a></p>
      <p class="next-result">{e(nxt["outcome"])}</p>
    </nav>"""


def detail(p):
    key = p.get("section", "work")
    sections = "".join(
        f'<h2>{e(sec["heading"])}</h2>'
        + "".join(f"<p>{e(t)}</p>" for t in sec["paragraphs"])
        + "".join(figure(f) for f in sec.get("figures", []))
        for sec in p.get("sections", [])
    )
    website = p.get("website")
    website_row = (
        f'<dt>Website</dt><dd><a href="{e(website["url"])}">{e(website["label"])}</a></dd>' if website else ""
    )
    links = (
        '<ul class="links">'
        + "".join(f'<li><a href="{e(l["url"])}">{e(l["label"])}</a></li>' for l in p["links"])
        + "</ul>"
        if p.get("links")
        else ""
    )
    body = f"""
<article class="section detail" aria-labelledby="detail-h">
  {marker(key)}
  <div class="section-body prose">
    <p class="back"><a href="/{key}/">All {SECTION_NAMES[key].lower()}</a></p>
    <h1 id="detail-h" class="detail-name">{e(p["title"])}</h1>
    <p class="detail-result">{e(p["outcome"])}</p>
    <p class="lede">{e(p["summary"])}</p>
    <dl class="facts facts-wide">
      <dt>Where</dt><dd>{e(p["org"])}</dd>
      {website_row}
      <dt>Role</dt><dd>{e(p["role"])}</dd>
      <dt>When</dt><dd>{e(p["dates"])}</dd>
      <dt>Methods</dt><dd>{e(p["methods"])}</dd>
      <dt>Stack</dt><dd>{e(p["stack"])}</dd>
    </dl>
    {links}
    {sections}
    {next_project(p)}
    <p class="detail-contact">To ask about this project, email <a href="mailto:{e(site["email"])}">{e(site["email"])}</a>.</p>
  </div>
</article>
"""
    return page(
        f'{p["title"]}: {site["name"]}',
        f'{p["outcome"]}. {p["summary"]}',
        body,
        path=project_url(p),
        current=key,
    )


def not_found():
    body = f"""
<section class="section page-section" aria-labelledby="nf-h">
  {marker("work")}
  <div class="section-body prose">
    <h1 id="nf-h" class="page-title">There’s no page at this address</h1>
    <p>The page may have moved. Try <a href="/work/">work</a>, <a href="/projects/">projects</a> or the <a href="/">home page</a>.</p>
  </div>
</section>"""
    return page(f'Page not found: {site["name"]}', site["description"], body, path="/404.html")


# ---------------------------------------------------------------- write out


def write(path, html):
    out = DIST / path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")


def build():
    # Empty dist/ rather than delete it: Windows refuses to remove a folder a
    # running preview server or shell is sitting in.
    DIST.mkdir(exist_ok=True)
    for child in DIST.iterdir():
        shutil.rmtree(child) if child.is_dir() else child.unlink()
    shutil.copytree(ROOT / "static", DIST, dirs_exist_ok=True)
    shutil.copy(ROOT / "src/styles.css", DIST / "styles.css")
    (DIST / "favicon.svg").write_text(seal_svg("fav", standalone=True), encoding="utf-8")
    write("index.html", home())
    write("work/index.html", entries_page("work", f'{site["name"]}: internships and research.'))
    write("projects/index.html", entries_page("projects", f'{site["name"]}: personal, class and hackathon projects.'))
    write("about/index.html", about_page())
    write("resume/index.html", resume_page())
    write("contact/index.html", contact_page())
    write("404.html", not_found())
    for p in projects:
        write(project_url(p).strip("/") + "/index.html", detail(p))
    (DIST / ".nojekyll").write_text("")
    print(f"Built home, 5 section pages and {len(projects)} project pages into {DIST.relative_to(ROOT)}/")


if __name__ == "__main__":
    build()
