"""Render the mirror from disk with all non-local network blocked; report errors + bio text."""
import json, os, sys, time
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
url = "file://" + os.path.join(ROOT, "mirror", "index.html")
errors, external, failed = [], [], []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("console", lambda m: m.type == "error" and errors.append(m.text))
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("requestfailed", lambda r: r.url.startswith("file:") and failed.append(r.url))
    def route(r):
        if r.request.url.startswith("file:"): return r.continue_()
        external.append(r.request.url); r.abort()
    pg.route("**/*", route)
    pg.goto(url, wait_until="load")
    time.sleep(2)
    text = pg.inner_text("body")
    checks = {k: k in text for k in ["About Rich Clarke", "Rich Clarke has been actively been working",
                                      "Austrian Economic theory", "Our Services", "Fundamental Resources", "rich@clarkecrypto.com"]}
    broken_imgs = pg.evaluate("[...document.images].filter(i => !i.complete || i.naturalWidth === 0).map(i => i.src)")
    fonts = pg.evaluate("document.fonts.ready.then(() => [...document.fonts].filter(f => f.status==='loaded').map(f => f.family))")
    pg.screenshot(path=os.path.join(ROOT, "screenshots", "mirror-index.png"), full_page=True)
    b.close()
print(json.dumps({"console_errors": errors, "external_blocked": external, "local_failed": failed,
                  "broken_imgs": broken_imgs, "fonts_loaded": sorted(set(fonts)), "text_checks": checks}, indent=1))
