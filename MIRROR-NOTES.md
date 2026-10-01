# clarkecrypto.com — static mirror notes

Source: Wix site https://www.clarkecrypto.com. Captured 2026-10-01 with Playwright (headless Chromium, 1440px viewport).
Rebuild with `/home/rich/clawd/integrations/fmls/.venv/bin/python tools/build.py`, check with `tools/verify.py`.

## Page inventory

| URL | Local file | Notes |
|---|---|---|
| https://www.clarkecrypto.com/ | `mirror/index.html` | The only page. The sitemap lists only the homepage, and every internal link in the rendered DOM is an in-page `#anchor`. |
| (favicon) | `mirror/favicon.ico` | Wix's generic default favicon. The site never set its own. |
| — | `mirror/robots.txt` | Added: allow all. |

Assets: `mirror/assets/img/` (13 images), `mirror/assets/fonts/` (37 woff2: Roboto, Helvetica, and Proxima Nova from the Wix CDN).
**Total size: about 1.1 MB (1,140,525 bytes), 53 files.** No build step is needed. Upload `mirror/` as-is to GitHub Pages or Vercel.

## What was stripped and why

- **All `<script>` tags** (the Wix "Thunderbolt" runtime, about 64 scripts) and `<noscript>`. The rendered DOM is already final, and the runtime would try to re-hydrate from Wix servers and throw errors when offline. Verified result: 0 console errors.
- `prefetch`/`preload`/`preconnect`/`dns-prefetch` links to `siteassets.parastorage.com`, the Wix `http-equiv` meta tags and the generator tag, all HTML comments, and the `data-url`/`data-href` and `sourceMappingURL` references in the inlined `<style>` blocks.
- `srcset`/`sizes`/`loading=lazy` on images. Each image is pinned to the variant the browser picked at 1440px. Images were fetched without `enc_avif`, so they are plain PNG/JPG.
- No cookie banner, chat widget, login bar, or Wix ads banner was present (premium site), so nothing like that was removed.
- All CSS is inline `<style>` in `index.html`, the same as Wix serves it. No CSS was dropped.

## Interactive elements: what changed or no longer works

- **Contact form** (Name/Email/Subject/Message): Wix's backend is gone. I rewired it to `action="mailto:rich@clarkecrypto.com" enctype="text/plain"`, which opens the visitor's mail client. Mail-client support for this is uneven. **Recommendation:** replace the form with a plain `mailto:` button, or use a free form backend (Formspree, Netlify/Vercel forms, Google Form).
- **Testimonial slideshow** (teal strip): only the first slide ("Rich was instrumental…" — Shiv Madan) shows. The prev/next arrows and dots do nothing without JS. A second slide existed but is not in the static DOM.
- **YouTube embeds** ("How Bitcoin Works Under the Hood", "Bitcoin Q&A: How Do I Secure My Bitcoin?"): still external iframes, now pointing at `youtube-nocookie.com/embed/<id>`. They need internet to play. Offline they show as blank areas. They also looked blank in the original headless screenshot, so the screenshots match.
- **Nav "FAQ"** links to `#comp-jin32lwq`, which doesn't exist on the live site either, so it was already dead. Home/Services/Contact/Subscribe anchors work.
- Smooth scrolling and hover animations driven by Wix JS are gone. Plain anchor jumps work.
- The footer social bar still has **Wix template placeholders**: `twitter.com/wix` and `linkedin.com/company/wix-com`, plus "©2020 by Pendulum Inc.". These match the original but are probably worth fixing.
- External links (youtu.be video, Facebook, LinkedIn, Twitter @richtrix) are unchanged and stay external.

## Verification

- `tools/verify.py` loads `file://…/mirror/index.html` with **all non-file network blocked**. Results: 0 console errors, 0 failed local requests, 0 broken images, fonts loaded locally. All of these text checks pass: "About Rich Clarke", the bio paragraphs, "Our Services", "Fundamental Resources", and rich@clarkecrypto.com.
- Screenshots: `screenshots/original-index.png` vs `screenshots/mirror-index.png`. Both are 1440×6272. A pixel diff shows 0.020% of pixels differing by more than 40/255, which is anti-aliasing-level noise. There are no visible layout, font, or image differences.

## Editing content later

Everything is in `mirror/index.html` (about 400 lines, mostly very long lines of Wix markup). Find text with search, not by line number:
- **Bio** ("About Rich Clarke"): search for `Rich Clarke has been actively been working` (around line 248). Both bio paragraphs are `<p>` tags in the same rich-text block. The headshot is `assets/img/363b7e_6e36d686…jpg`.
- Testimonial: search for `Rich was instrumental`. Footer/copyright: search for `Pendulum`.
- Services cards, "Fundamental Resources" text and the hero headline are plain text inside `<p>`/`<h*>` tags. Search for the visible text.
- Positions are absolute or grid-based Wix layout. Large edits to text length can overflow fixed-height boxes. Keep edits similar in length, or switch to a hand-written page for major changes.
- `<link rel="canonical">` and `og:url` still point to https://www.clarkecrypto.com. That is correct if the domain moves to the new host. Otherwise update them.
