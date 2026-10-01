import json, sys, time
from playwright.sync_api import sync_playwright
URL = sys.argv[1] if len(sys.argv) > 1 else "https://www.clarkecrypto.com/"
name = sys.argv[2] if len(sys.argv) > 2 else "index"
reqs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.on("response", lambda r: reqs.append({"url": r.url, "status": r.status, "type": r.request.resource_type, "ct": r.headers.get("content-type", "")}))
    pg.goto(URL, wait_until="networkidle", timeout=90000)
    h = pg.evaluate("document.body.scrollHeight")
    for y in range(0, h + 900, 400):
        pg.evaluate(f"window.scrollTo(0,{y})"); time.sleep(0.25)
    pg.evaluate("window.scrollTo(0,0)"); time.sleep(2)
    time.sleep(3)
    links = pg.evaluate("[...document.querySelectorAll('a[href]')].map(a=>a.href)")
    html = pg.content()
    open(f"raw/{name}.rendered.html", "w").write(html)
    json.dump({"requests": reqs, "links": links, "title": pg.title()}, open(f"raw/{name}.json", "w"), indent=1)
    pg.screenshot(path=f"screenshots/original-{name}.png", full_page=True)
    b.close()
print(len(reqs), "requests;", len(links), "links")
