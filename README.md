# GhostWeb

A dependency-free, static ghostwriting studio website. The editorial design
preserves the original page copy, writing demos, metadata, and structured data.

## Preview

From this directory, run:

```sh
python -m http.server 4173 --bind 127.0.0.1
```

Open <http://127.0.0.1:4173>. No build step is needed; deploy the repository's
static files together, including `index.html`, `design.css`, and `studio.js`.

## Design

- Warm ivory, sage, and forest green, with just two type families: Source Serif 4
  for all writing/headings, and the original Space Mono for the animated wordmark
  and interface controls. The original bracket/caret SVG and its blink are restored.
- Manuscript-folder tabs, rolling quality/live word counters, a seekable process
  player, an expandable reading index, reply-style FAQ, and a wide-screen minimap.
- Native CSS/JavaScript rather than React, WebGL, or animation dependencies.
- Keyboard navigation, reduced-motion support, and mobile layouts down to 320px.
- `index.html` retains the structural baseline; `design.css` owns the new theme.

Google Fonts is the only external visual resource; system font fallbacks remain
available when it cannot be reached. The RareUI interactions are original native
adaptations, not imported React components.

## Browser regression tests

```sh
python -m pip install playwright
python -m playwright install chromium
python -m unittest discover -s tests -v
```

The tests start their own local server. To use installed Chrome instead of
Playwright's Chromium, set `GHOSTWEB_BROWSER_CHANNEL=chrome`. Optionally set
`GHOSTWEB_SCREENSHOTS` to an output directory to save desktop and mobile previews.

Coverage includes service tabs, name propagation, SEO previews, tone controls,
FAQs, mobile navigation, the section minimap, form validation, reduced motion,
the typing animation, the restored logo, type consistency, number wheels, process
play/pause/seek, expandable chapter navigation, and ten viewport widths from
320px to 1920px.

### Interaction references

The native interactions adapt these [RareUI](https://www.rareui.com/) designs
for GhostWeb's existing static page, rather than importing their React code:

- [Folder](https://rareui.com/components/foldercomponent): lifted manuscript
  pages and file-tab transitions.
- [Scroll Progress](https://rareui.com/components/scrollprogressindicator): a
  reading-progress pill that expands into an accessible chapter index.
- [Animated Counter](https://rareui.com/components/animatedcounter): directional
  digit transitions on quality scores and the live word/sentence totals.
- [Step Player](https://rareui.com/components/stepplayer): seekable stages with
  play, pause, and replay. Playback is opt-in and pauses offscreen.
- [Proximity Sidebar](https://rareui.com/components/proximitysidebar) and
  [FAQ](https://rareui.com/components/faq): section tracking and reply bubbles.

## Existing form behavior

The sample-request form validates locally and displays a confirmation only.
It does **not** send email or save submissions. This existing behavior is
unchanged; a delivery endpoint must be connected separately before accepting
real requests.
