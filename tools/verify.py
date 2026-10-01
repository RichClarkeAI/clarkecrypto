"""Render the mirror from disk with all non-local network blocked; report errors + bio text.

  verify.py            desktop: index.html at 1440px
  verify.py --mobile   mobile:  m.html as iPhone at 375x812
Both modes also check that the load-time switcher sends the other viewport to the other page.
"""
import json, os, sys, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOBILE = "--mobile" in sys.argv
page, other, shot = ("m.html", "index.html", "mirror-mobile") if MOBILE else ("index.html", "m.html", "mirror-index")
url = "file://" + os.path.join(ROOT, "mirror", page)
errors, external, failed = [], [], []


def block_external(pg):
    def route(r):
        if r.request.url.startswith("file:"): return r.continue_()
        external.append(r.request.url); r.abort()
    pg.route("**/*", route)


with sync_playwright() as p:
    b = p.chromium.launch()
    mobile_ctx = {**p.devices["iPhone 13"], "viewport": {"width": 375, "height": 812}}
    ctx = b.new_context(**mobile_ctx) if MOBILE else b.new_context(viewport={"width": 1440, "height": 900})
    pg = ctx.new_page()
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("requestfailed", lambda r: r.url.startswith("file:") and failed.append(r.url))
    block_external(pg)
    pg.goto(url, wait_until="load")
    time.sleep(2)
    stayed = pg.url.endswith("/" + page)
    text = pg.inner_text("body")
    checks = {k: k in text for k in ["About Rich Clarke", "Rich Clarke has been actively been working",
                                      "Austrian Economic theory", "Our Services", "Fundamental Resources", "rich@clarkecrypto.com"]}
    broken_imgs = pg.evaluate("[...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)")
    fonts = pg.evaluate("document.fonts.ready.then(() => [...document.fonts].filter(f => f.status==='loaded').map(f => f.family))")
    layout = pg.evaluate("[innerWidth, document.documentElement.scrollWidth, document.querySelector('meta[name=viewport]').content]")
    pg.screenshot(path=os.path.join(ROOT, "screenshots", shot + ".png"), full_page=True)
    # Opposite viewport opening this page should be bounced to the other layout.
    octx = b.new_context(viewport={"width": 1440, "height": 900}) if MOBILE else b.new_context(**mobile_ctx)
    opg = octx.new_page(); block_external(opg)
    opg.goto(url, wait_until="load"); time.sleep(1)
    switched = opg.url.endswith("/" + other)
    b.close()
print(json.dumps({"page": page, "stayed_on_page": stayed, "other_viewport_switched_to": other if switched else False,
                  "layout[innerWidth,scrollWidth,viewport]": layout, "console_errors": errors,
                  "external_blocked": external, "local_failed": failed, "broken_imgs": broken_imgs,
                  "fonts_loaded": sorted(set(fonts)), "text_checks": checks}, indent=1))
