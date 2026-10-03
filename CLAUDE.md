# CLAUDE.md

Project page for **BRACE**, the named, de-anonymized version hosted under the Multiply Labs GitHub organization at https://multiplylabs.github.io/brace/. README.md covers layout, content slots and deployment; this file holds the rules for working here.

## Relationship to the anonymous site

A separate, anonymous copy of this page exists for double-blind review. **Never link to it, mention its URL or repository, or copy anything from this repo into it.** Changes that should appear on both sites are made independently in each repo. This repo may name authors, affiliations and the company; the anonymous one may not.

## Design system

A strict, flat house style. Match it rather than inventing new patterns.

- **Type:** Barlow only (Google Fonts), weights 400/500/600. Display sizes (h1–h5) are 400 with -1px tracking; SemiBold only at button/label size. Headlines are Title Case sentences ending in periods, with at most one accent word in blue (`.accent`).
- **Colour:** tokens are on `:root` in `assets/css/site.css`. `--blue-5` (#397FE7) is the only accent. Warm neutrals (`--neutral-*`) and slates (`--slate-*`) carry the structure. Secondary colours appear only inside data figures.
- **Structure:** modules are separated by 1px hairlines on a 40px grid (20px on phones). No shadows, gradients or glows. Corners are 4px on controls and 8px on media.
- **Section pattern (`.section`):** a left rail holding a 100px blue rule and a caps eyebrow, then a headline, hairline and body, then side notes (`.kv`). Media goes in a following `.band`, `.grid2`, `.grid3` or `.tiles` row.
- **Grounds:** white page. Use at most two `.dark` (Slate-01) bands plus the footer, never adjacent. `.panel` (Neutral-08) is for warm feature panels. Both bleed to the viewport edge. No dark-mode override.
- **Layout:** it must work at 390px with no horizontal page scroll.

## Placeholders

Driven by `assets/js/site.js`:

- `a[data-soon][data-probe]`: disabled ("Soon") until its href exists. The **Read paper** button is one: it switches on by itself once `assets/paper.pdf` is committed.
- `a[data-soon]`: disabled until the attribute is removed by hand (the code link).
- `[data-video="name"]`: becomes a `<video>` once `assets/video/name.mp4` exists; `name.jpg` is its poster. Players are created as their slot comes within a screen of the viewport, with the clip fetched only when it is in view. `data-autoplay` makes it a muted loop that plays while on screen.

## Verifying changes

1. `python3 scripts/serve.py 8000` in the repo root, then check the page in a browser at desktop width and at 390px. Placeholders need http, not `file://`, and the videos need byte ranges, which `python3 -m http.server` does not serve.
2. After pushing, `gh run watch` the "Deploy site" workflow and load the live URL.
