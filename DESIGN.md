# Design plan: Iris — portfolio (书法 / xuan paper)

Status: approved and built (October 2026).

## Changes made during the build
- **Hero is her name, 尹紫鸢**, not 见微知著. 紫鸢 means "purple iris", so the Chinese and English names match. The seal carves 尹.
- **Stack: plain HTML/CSS plus a Python build script** instead of Astro. Node isn't installed on the dev machine, and Python (stdlib only) keeps the toolchain to one language she already uses. Content stays in `content/projects.json`.
- **`--ink-grey` darkened to `#4F5249`.** `#575A50` fell to 4.2:1 on the darkest paper fibers. The new value stays at 4.5:1 or above everywhere on the texture.
- **The wet-ink edge is baked into the glyph outlines** at extraction time. Runtime SVG filters (turbulence and displacement) made the hero slow to paint and invisible in some renders. The ink bleed is a faint 9-unit stroke, not a blur.
- **Reveal masks are attached only while writing**, then removed, so scrolling past the hero stays cheap.
- **The bamboo layer moved behind and to the right of the column** at 55% opacity. Full-size, it competed with the name.
- **Scroll motion added at Iris's request** (Lenis + GSAP ScrollTrigger, vendored in `static/vendor/`, wired in `static/motion.js`). She chose three effects, including fade-ups, which the original brief had ruled out:
  - Section markers brush on once, character by character, in reading direction.
  - Layered-paper parallax on desktop: the column trails the page by 12% of hero height and the bamboo by 32%. Scrubbed to scroll.
  - Content blocks below the hero fade up once (16px, 0.6s). The hero never fades, so the 10-second read isn't delayed.
  - All of this is off for reduced motion, and content is never hidden before the script starts.
- **Vanta fog as an ink wash behind the hero, at Iris's request.** It is constant ambient motion, which the original brief ruled out, so it's constrained:
  - Paper and ink colors only, multiplied onto the paper, and masked to fade out over the text side.
  - Starts after the name is written, on wide screens only, never with reduced motion or data saver.
  - Costs about 150 KB gzipped for three.js, loaded lazily.
  - The hero gloss moved to full ink (5.6:1 under the darkest fog), because lighter inks fall below 4.5:1 there.
- **Smoother scrolling (October 2026):** Lenis is back, on GSAP's ticker with a 1.1s exponential ease, so reversing at the bottom of a page retargets smoothly. The real stutter came from the fixed background paintings using a multiply blend and a CSS mask, which repainted every frame; transparency and the fade are now baked into the images, and the layer is GPU-composited.
- **Ink paintings (October 2026):** the bamboo sprig was replaced by an ink-wash iris painting behind the brush name, painted procedurally by `tools/make_iris.py` after the composition of one of Iris's own paintings (hers is not published). Each section page has a public-domain Yangzhou-school ink painting as part of the background: fixed to the bottom-right corner, bleeding off the edges and fading into the paper through a radial mask, behind an empty third column so it never sits under text on wide screens. Below 1200px it stays fixed but drops to 25% opacity (22% on phones), and small grey labels switch to body ink so text keeps 4.5:1 or better over it. Credits are in the footer. The paintings are from the Cleveland Museum of Art: Min Zhen (Work, Projects), Zheng Xie (About), Wang Shishen (Resume) and Huang Shen (Contact). Scans are whitened so they multiply onto the paper as ink.
- **Separate pages (October 2026):** the home page is now one screen, just the name and links. Work, Projects, About, Resume and Contact are their own pages, each opening with its brush marker, and the nav marks the current page. The parallax was removed, since the home page no longer scrolls.
- **Design review pass (October 2026):**
  - Hero shortened so the first project shows on a 1440×900 screen.
  - Header name hidden on the home page, since the hero already says it.
  - Lenis smooth scrolling and fade-ups removed: they delayed skimming and were the most template-like effects. The remaining motion is the brush, the markers, the parallax and the fog.
  - Project names get a dry-brush underline that strokes in on hover.
  - Project pages are titled by name, with the result beneath, and end with a "Next project" link.
  - Also added: a Copy email button, a nav highlight for the current section, a link-preview image and larger tap targets.
- **The brush column sits beside the text**, not at the far edge, so the vertical heading and horizontal text read as one composition, as in the Song deck.

## Subject, audience, job
- Subject: a Statistics & ML student who also does HCI research. The work spans speech models, user studies and tools.
- Audience: recruiters and hiring managers for data science and AI/ML internships (summer 2027).
- Job: within 10 seconds they should see who she is, what she built and what it achieved, and where the resume and email are.

## Color tokens
| Token | Hex | Role | Contrast on paper |
|---|---|---|---|
| `--paper` 宣 | `#DAD9CD` | Page ground. A grey-green stone that sits between the bamboo sheet (#2) and the Song deck (#4). Not cream. | n/a |
| `--paper-ghost` 竹 | `#C5CAB8` | The faint second layer: one bamboo sprig in the hero only | decorative |
| `--ink` 浓墨 | `#161714` | Brush calligraphy and the English name | 12.7:1 |
| `--ink-body` 淡墨 | `#2B2D28` | All body text | 9.8:1 |
| `--ink-grey` 灰墨 | `#4F5249` | Secondary text (role, dates, stack) | ≥4.5:1 on darkest texture |
| `--seal` 朱砂 | `#B3362B` | Seal stamp only. Nothing else is red. | 4.25:1 (paper-colored carving on red, large glyphs) |

Paper texture: one tileable 512px grayscale fiber texture in WebP (≤25 KB), blended with multiply at ±3% luminance so the contrast numbers above still hold. No dark mode. The paper is the concept.

## Type
- **Display: Ma Shan Zheng** (马善政). Regular-script brush with real press-and-lift weight contrast and wet-looking terminals. Loaded via Google Fonts `text=` with only the characters used (~12 glyphs, a few KB).
  - Rejected: Zhi Mang Xing (strokes too even, fails "varied stroke weight"); Long Cang (reads as pen handwriting); Liu Jian Mao Cao (beautiful wild cursive like the background sheets in #1, but illegible even to Chinese readers; kept as the risky alternate for the hero only).
- **Text: Alegreya Sans** 400 / 500, plus 400 italic. A humanist sans built on calligraphic (broad-nib) skeletons, so it is related to the brush without competing with it, and it stays readable at small sizes for skimming.
- Scale (classical): 14 / 16 / 18 / 21 / 24 / 36 / 48 px. Body 18/1.6, measure ≤ 64ch. Brush hero is `clamp(72px, 11vw, 148px)` per glyph. Section markers are 30px brush in `--ink-grey`.
- Sentence case everywhere. No all-caps labels, no single-word color or italic accents, no middle-dot meta strings, no "→" on links.

## Chinese text (display only, aria-hidden or glossed)
- Hero: **见微知著**, "from small signs, see the whole." That is statistical inference stated as a classical idiom, so it connects the theme to her field.
- Seal: her Chinese name or a surname character (needs her input).
- Section markers: 作品 Work · 关于 About · 履历 Resume · 联系 Contact. Each sits beside a real English `<h2>`.

## Layout
Asymmetric, right-weighted. The brush column(s) sit at the right edge because vertical text reads right-to-left. English text is left-aligned (ragged right) and set small, as in the Song deck: a large vertical heading next to small horizontal text.

Desktop home (≥1024):
```
┌──────────────────────────────────────────────────────────────────────┐
│ Iris [Surname]                         Work   About   Resume   Contact │
│                                                                        │
│                                                        ╲ ╱  见   bamboo │
│  Iris [Surname]                    (48, ink)            ╲   微   ghost  │
│  Statistics & Machine Learning at Carnegie Mellon,          知   layer  │
│  minor in HCI. I fine-tune speech models and study           著   (hero │
│  how people use the tools I build. Looking for              [印]  only) │
│  summer 2027 data science and ML internships.                          │
│                                                     jiàn wēi zhī zhù:   │
│  Download resume (PDF)   Email   GitHub   LinkedIn  from small signs,   │
│                                                     see the whole.      │
├──────────────────────────────────────────────────────────────────────┤
│ 作 │  Work                                                             │
│ 品 │                                                                   │
│    │  Cut Hindi word error rate from [X]% to [Y]% by    Poseidon AI     │
│    │  fine-tuning Whisper-medium                         ML intern       │
│    │  Role  ...   Methods  ...   Stack  ...              [dates]         │
│    │  Read the case study                                                │
│    │                                                                   │
│    │  Made cybersecurity advice feel like everyday        CMU HCII, SURA │
│    │  "adulting": iOS app + interview study with [n]       ...           │
│    │  ...                                                              │
└──────────────────────────────────────────────────────────────────────┘
```
- Project entries are separated by whitespace, not cards, borders or shadows, and are not numbered. The first line is the outcome (24px, ink). Name and role go in the right margin in grey. Role/Methods/Stack form a small `<dl>`.
- About / Resume / Contact use the same pattern: a vertical brush marker in a narrow left rail, then English content offset to the text column.

Project detail (`/work/[slug]`):
```
┌──────────────────────────────────────────────────────────────┐
│ 作 │ ‹ All work                                               │
│ 品 │ Cut Hindi WER from [X]% to [Y]%       (36)               │
│    │ Poseidon AI, ML engineering intern, [dates]               │
│    │ ┌ Outcome ┐ 2–3 sentences, metric first                  │
│    │ What it is · My role · Methods · What I'd do next (h3s)  │
│    │ [figure: WER chart or app screenshots, real alt text]    │
└──────────────────────────────────────────────────────────────┘
```

Mobile (≤600):
```
┌─────────────────────────┐
│ Iris [S]           Menu │
│                      见 │  brush column stays vertical,
│ Iris [Surname]       微 │  ~56px glyphs, top-right
│ Stats & ML at CMU,   知 │
│ HCI minor.           著 │
│                     [印]│
│ Intro paragraph full    │
│ width below the column. │
│ [Download resume (PDF)] │
│ 作品 Work               │  section markers turn horizontal,
│ outcome line …          │  inline before the h2
└─────────────────────────┘
```
16px gutters, no horizontal scroll. Bamboo ghost is dropped below 600px.

## Principles
1. **One brush moment.** The hero idiom is the only large black calligraphy. Everything else is small and quiet in grey ink (留白).
2. **Outcome first, always.** Every project leads with what changed and the number. Names and stacks come second.
3. **Seal once.** A vermilion 印章 appears as the signature under the hero column (and as the favicon). Nowhere else.
4. **One orchestrated motion.** On load, the four characters are "written": an SVG mask of thick brush paths reveals each glyph in stroke order, column top-to-bottom, ~2.2s total, then the seal is pressed (opacity plus scale 1.04→1, no bounce). It waits for the font to load. With reduced motion the final state shows immediately. No scroll animations, no hover choreography.
5. **Wet ink, dry paper.** A static SVG displacement filter gives brush edges a slight bleed. The paper stays matte and barely textured.
6. **Chinese is image, English is content.** Every Chinese glyph is aria-hidden or carries an English gloss. Nothing important lives only in Chinese.

## Review against the brief: what I revised
| First instinct | Why it was generic / off-brief | Revised to |
|---|---|---|
| Warm cream `#F2EDE3` paper + vermilion | The #1 AI-default look; the brief rules out cream | Grey-green stone `#DAD9CD` from refs #2/#4 |
| Large brush heading for every section | Spends boldness everywhere | 30px grey section markers; only the hero is big and black |
| Ghost cursive or bamboo texture across the whole page | Brief: "not a texture behind everything" | One bamboo sprig, hero only, hidden on mobile |
| Hero = her name transliterated (艾瑞斯) | Phonetic transliteration is weak calligraphy and says nothing about her | 见微知著, an idiom for inference; her name goes in the seal |
| Project cards with thumbnails and meta lines "Python · PyTorch" | SaaS-card kit and middle-dot meta strings | Whitespace-separated entries with a labeled `<dl>` |
| Fade-up per section | Brief forbids it | One load sequence only |
| Zhi Mang Xing for the "running script" look | Even stroke weight | Ma Shan Zheng |

## Build
- **Astro** (static output, zero JS by default; the only script is the hero reveal) deployed to **GitHub Pages** via GitHub Actions. Vercel works the same if preferred.
- Content: `src/content/projects/*.md`, one Markdown file per project with schema-checked frontmatter (`title`, `outcome`, `org`, `role`, `dates`, `methods[]`, `stack[]`, `links`, `order`, `draft`) plus a prose body for the detail page. A missing field fails the build. (Brief said "one data file". Per-project Markdown is recommended because detail pages need prose; one `projects.yaml` is possible if preferred.)
- Resume: `public/resume.pdf`, linked from the header, the hero and the Resume section.
- QA: screenshots at 1440 / 768 / 375, keyboard tab-through, reduced-motion check, contrast verification, then critique and fix.
