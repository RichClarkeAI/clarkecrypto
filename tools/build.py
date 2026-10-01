"""Build a static, offline-browsable mirror of https://www.clarkecrypto.com.

Renders the live Wix page with Playwright, cleans the DOM in-page (drops the
Wix runtime scripts, prefetch hints, tracking), then localizes every image and
font into mirror/assets/ and rewrites references to relative paths.

Run with the Playwright venv:  <venv>/bin/python tools/build.py
"""
import hashlib, json, os, re, time, urllib.request
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright

SITE = "https://www.clarkecrypto.com"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mirror")
ASSETS = os.path.join(OUT, "assets")
PAGES = {"/": "index.html"}  # every internal link on the rendered homepage is a #fragment
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
EXT = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif",
       "image/svg+xml": ".svg", "image/x-icon": ".ico", "image/vnd.microsoft.icon": ".ico",
       "font/woff2": ".woff2", "font/woff": ".woff", "application/font-woff2": ".woff2",
       "application/font-woff": ".woff", "font/ttf": ".ttf"}
ASSET_HOSTS = ("static.wixstatic.com", "static.parastorage.com")

CLEAN_JS = r"""
() => {
  const site = %s;
  // Wix runtime + tracking: useless offline, throws console errors.
  document.querySelectorAll('script, noscript, link[rel=prefetch], link[rel=preload], link[rel=modulepreload],'
    + 'link[rel=preconnect], link[rel=dns-prefetch], meta[http-equiv], meta[name=generator], iframe[src*="filesusr"]')
    .forEach(e => e.remove());
  // Inlined CSS: drop provenance attrs + source-map comments so nothing points back at Wix.
  document.querySelectorAll('style').forEach(s => {
    s.removeAttribute('data-url'); s.removeAttribute('data-href');
    s.textContent = s.textContent.replace(/\/\*# sourceMappingURL=[^*]*\*\//g, '');
  });
  const walker = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
  const comments = []; while (walker.nextNode()) comments.push(walker.currentNode);
  comments.forEach(c => c.remove());
  // Freeze responsive images on the variant the browser actually picked.
  document.querySelectorAll('img').forEach(img => {
    if (img.currentSrc) img.setAttribute('src', img.currentSrc);
    img.removeAttribute('srcset'); img.removeAttribute('sizes');
    img.removeAttribute('loading');
  });
  document.querySelectorAll('picture source').forEach(s => s.remove());
  // Internal links -> relative.
  document.querySelectorAll('a[href]').forEach(a => {
    const h = a.getAttribute('href');
    if (h.startsWith(site + '/#') || h.startsWith(site + '#') || h.startsWith('./#')) a.setAttribute('href', h.slice(h.indexOf('#')));
    else if (h === site || h === site + '/') a.setAttribute('href', 'index.html');
  });
  // YouTube embeds stay external; drop the JS-API params that expect the Wix player wrapper.
  document.querySelectorAll('iframe[src*="youtube.com/embed/"]').forEach(f => {
    const id = f.src.split('/embed/')[1].split('?')[0];
    f.setAttribute('src', 'https://www.youtube-nocookie.com/embed/' + id + '?rel=0');
    f.setAttribute('loading', 'lazy');
  });
  // Contact form has no backend offline; route it to the site's mailto address.
  document.querySelectorAll('form').forEach(f => {
    f.setAttribute('action', 'mailto:rich@clarkecrypto.com');
    f.setAttribute('method', 'post'); f.setAttribute('enctype', 'text/plain');
    f.querySelectorAll('textarea:not([name])').forEach(t => t.setAttribute('name', 'message'));
    f.querySelectorAll('button').forEach(b => b.setAttribute('type', 'submit'));
  });
  // Favicon -> local file.
  document.querySelectorAll('link[rel*=icon]').forEach(l => l.setAttribute('href', 'favicon.ico'));
  return '<!DOCTYPE html>\n' + document.documentElement.outerHTML;
}
""" % json.dumps(SITE)

URL_RE = re.compile(r"""(?:https?:)?//(?:%s)/[^\s"'()<>]+""" % "|".join(map(re.escape, ASSET_HOSTS)))

cache = {}


def fetch(url):
    if url in cache:
        return cache[url]
    full = "https:" + url if url.startswith("//") else url
    # Ask for a broadly supported format rather than AVIF.
    req_url = full.replace(",enc_avif", "").replace("enc_avif,", "")
    req = urllib.request.Request(req_url, headers={"User-Agent": UA, "Accept": "image/webp,image/png,image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data, ct = r.read(), r.headers.get_content_type()
    path = urlparse(full).path
    stem = re.sub(r"[^A-Za-z0-9._~-]", "_", os.path.basename(path.split("/v1/")[0]) or "asset")
    stem = os.path.splitext(stem)[0][:60]
    ext = EXT.get(ct) or os.path.splitext(path)[1] or ".bin"
    name = f"{stem}-{hashlib.sha1(full.encode()).hexdigest()[:8]}{ext}"
    sub = "fonts" if ext in (".woff", ".woff2", ".ttf") else "img"
    os.makedirs(os.path.join(ASSETS, sub), exist_ok=True)
    with open(os.path.join(ASSETS, sub, name), "wb") as f:
        f.write(data)
    cache[url] = f"assets/{sub}/{name}"
    return cache[url]


def localize(html):
    failed = []
    def sub(m):
        u = m.group(0).replace("&amp;", "&")
        try:
            return fetch(u)
        except Exception as e:  # keep original URL so it still works online
            failed.append((u, str(e)))
            return m.group(0)
    return URL_RE.sub(sub, html), failed


def main():
    os.makedirs(OUT, exist_ok=True)
    report = {}
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        for path, fname in PAGES.items():
            pg.goto(SITE + path, wait_until="networkidle", timeout=90000)
            h = pg.evaluate("document.body.scrollHeight")
            for y in range(0, h + 900, 400):  # trigger lazy images + entrance animations
                pg.evaluate(f"window.scrollTo(0,{y})"); time.sleep(0.25)
            pg.evaluate("window.scrollTo(0,0)"); time.sleep(3)
            html = pg.evaluate(CLEAN_JS)
            html, failed = localize(html)
            with open(os.path.join(OUT, fname), "w") as f:
                f.write(html)
            report[fname] = {"failed": failed}
        b.close()
    req = urllib.request.Request("https://static.parastorage.com/client/pfavico.ico", headers={"User-Agent": UA})
    with urllib.request.urlopen(req) as r, open(os.path.join(OUT, "favicon.ico"), "wb") as f:
        f.write(r.read())
    with open(os.path.join(OUT, "robots.txt"), "w") as f:
        f.write("User-agent: *\nAllow: /\n")
    print(json.dumps({"assets": len(cache), **report}, indent=1))


if __name__ == "__main__":
    main()
