#!/usr/bin/env python3
"""Single-pass SEO / crawlability / payload audit for a live URL.

Usage:
    python3 audit_site.py https://example.com [--proxy http://127.0.0.1:7890]
                          [--sample 6] [--json out.json]

Design notes (learned the hard way — see references/checklist.md):
  * NEVER infer compression from a bare request. Send Accept-Encoding explicitly
    and compare the response header; a site may serve 317 KB raw but 24 KB brotli.
  * Do NOT use HEAD to measure asset size on CDNs that return chunked encoding —
    read the full body and take len(). http.client does not auto-decompress, so
    that length IS the on-the-wire (compressed) size.
  * Read bodies fully before closing; a partial read loses content-length.
"""

import argparse
import concurrent.futures
import gzip
import http.client
import json
import re
import ssl
import sys
import time
import urllib.parse

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"
ACCEPT = "br, gzip, deflate"


def make_conn(host, proxy, timeout=25):
    """Return a connection to `host:443`, tunnelling through an HTTP proxy if given."""
    if proxy:
        p = urllib.parse.urlparse(proxy if "://" in proxy else "http://" + proxy)
        c = http.client.HTTPSConnection(p.hostname, p.port or 7890, timeout=timeout)
        c.set_tunnel(host, 443)
        return c
    return http.client.HTTPSConnection(host, 443, timeout=timeout, context=ssl.create_default_context())


def fetch(url, proxy=None, accept_encoding=ACCEPT, tries=4, timeout=25, read=True):
    """GET url. Returns dict with status, headers, body(bytes), elapsed, encoding, error."""
    parts = urllib.parse.urlsplit(url)
    host = parts.netloc
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    headers = {"User-Agent": UA, "Accept-Encoding": accept_encoding, "Connection": "close"}

    last = None
    for attempt in range(tries):
        try:
            t0 = time.time()
            c = make_conn(host, proxy, timeout)
            c.request("GET", path, headers=headers)
            r = c.getresponse()
            body = r.read() if read else b""
            enc = r.getheader("content-encoding") or "none"
            hdrs = {k.lower(): v for k, v in r.getheaders()}
            status = r.status
            c.close()
            return {
                "url": url, "status": status, "headers": hdrs, "body": body,
                "elapsed_ms": round((time.time() - t0) * 1000, 1),
                "encoding": enc, "wire_bytes": len(body), "error": None,
            }
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
            time.sleep(0.5 * (attempt + 1))
    return {"url": url, "status": 0, "headers": {}, "body": b"", "elapsed_ms": 0,
            "encoding": "ERR", "wire_bytes": 0, "error": last}


def has_brotli():
    try:
        import brotli  # noqa: F401
        return True
    except ImportError:
        return False


def decode(res):
    """Decode a response body to text using the reported content-encoding."""
    b = res["body"]
    if not b:
        return ""
    enc = (res["encoding"] or "").lower()
    try:
        if enc == "gzip":
            b = gzip.decompress(b)
        elif enc == "deflate":
            import zlib
            b = zlib.decompress(b, -zlib.MAX_WBITS)
        elif enc == "br":
            import brotli
            b = brotli.decompress(b)
    except ImportError:
        return ""
    except Exception:  # noqa: BLE001
        return ""
    return b.decode("utf-8", "ignore")


def meta_audit(html):
    def first(pat):
        m = re.search(pat, html, re.S | re.I)
        return m.group(1).strip() if m else None

    og = re.findall(r'property="(og:[^"]+)"', html)
    tw = re.findall(r'name="(twitter:[^"]+)"', html)
    ld = re.findall(r'application/ld\+json', html)
    ld_types = re.findall(r'"@type"\s*:\s*"([^"]+)"', html)
    title = first(r"<title>(.*?)</title>")
    desc = first(r'<meta\s+name="description"\s+content="(.*?)"')
    canonical = first(r'<link\s+rel="canonical"\s+href="([^"]+)"')
    robots = first(r'<meta\s+name="robots"\s+content="([^"]+)"')
    return {
        "title": title,
        "title_len": len(title) if title else 0,
        "description": desc,
        "description_len": len(desc) if desc else 0,
        "canonical": canonical,
        "robots": robots,
        "og_properties": sorted(set(og)),
        "og_missing": [p for p in ["og:title", "og:description", "og:url", "og:image", "og:type", "og:site_name"]
                       if p not in og],
        "twitter_properties": sorted(set(tw)),
        "h1_count": len(re.findall(r"<h1[\s>]", html, re.I)),
        "h2_count": len(re.findall(r"<h2[\s>]", html, re.I)),
        "jsonld_blocks": len(ld),
        "jsonld_types": sorted(set(ld_types)),
        "html_chars": len(html),
        "html_gzip": len(gzip.compress(html.encode(), 9)) if html else 0,
        "img_total": len(re.findall(r"<img[\s>]", html, re.I)),
        "img_no_alt": len([m for m in re.findall(r"<img[^>]*>", html, re.I)
                           if not re.search(r'\balt="', m)]),
        "inline_svg": len(re.findall(r"<svg", html, re.I)),
        "inline_script_chars": sum(len(x) for x in re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, re.S)),
        "class_attr_chars": sum(len(m) for m in re.findall(r'class="[^"]*"', html)),
        "anchor_buttons": len(re.findall(r"<button", html, re.I)),
    }


def asset_list(html, base):
    js = {u.split("?")[0] for u in re.findall(r'<script[^>]*\bsrc="([^"]+)"', html)}
    css = {u.split("?")[0] for u in re.findall(r'<link[^>]*rel="stylesheet"[^>]*href="([^"]+)"', html)}
    no_module = set(re.findall(r'<script(?=[^>]*\bsrc="([^"]+)")(?=[^>]*\bnoModule)[^>]*>', html))
    to_abs = lambda u: u if u.startswith("http") else urllib.parse.urljoin(base, u)
    return ({to_abs(u) for u in js}, {to_abs(u) for u in css}, {to_abs(u).split("?")[0] for u in no_module})


def internal_links(html, base):
    links = [a for a in re.findall(r'href="(/[^"]*)"', html)
             if not a.startswith(("/_next", "/static")) and not a.endswith((".css", ".js", ".png", ".jpg", ".svg", ".ico", ".woff", ".woff2"))]
    return sorted(set(links))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--proxy", default=None, help="http://127.0.0.1:7890")
    ap.add_argument("--sample", type=int, default=8, help="how many internal links to probe")
    ap.add_argument("--json", default=None)
    ap.add_argument("--no-brotli", action="store_true", help="request gzip only (when python-brotli is absent)")
    args = ap.parse_args()

    base = args.url.rstrip("/")
    # Brotli is what Vercel/Cloudflare serve by default, but the Python `brotli`
    # module is often absent. Fall back to gzip so HTML analysis always works.
    if not args.no_brotli and not has_brotli():
        print("  (brotli module not installed -> requesting gzip so the HTML can be parsed)")
        args.no_brotli = True
    accept = "gzip, deflate" if args.no_brotli else ACCEPT

    print(f"\n=== 1. Document load: {base} ===")
    main_res = fetch(base, args.proxy, accept)
    if main_res["status"] == 0:
        print(f"  FAILED: {main_res['error']}")
        print("  Hint: if the site is behind a proxy, pass --proxy; if the sandbox blocks egress, re-run outside the sandbox.")
        return 1
    h = main_res["headers"]
    print(f"  status          : {main_res['status']}")
    print(f"  server          : {h.get('server', '?')}")
    print(f"  elapsed         : {main_res['elapsed_ms']} ms")
    print(f"  content-encoding: {main_res['encoding']}")
    print(f"  content-length  : {h.get('content-length', 'chunked')}")
    print(f"  wire bytes      : {main_res['wire_bytes']:,}  <-- what the browser actually downloads")
    print(f"  cache           : {h.get('cache-control', '?')} | {h.get('x-vercel-cache', h.get('cf-cache-status', ''))}")
    for k in ("strict-transport-security", "x-content-type-options", "x-frame-options", "content-security-policy"):
        if k not in h:
            print(f"  MISSING header  : {k}")

    raw = fetch(base, args.proxy, accept_encoding="identity") if args.no_brotli else None
    if raw and raw["wire_bytes"]:
        ratio = raw["wire_bytes"] / max(1, main_res["wire_bytes"])
        print(f"  raw html (no enc): {raw['wire_bytes']:,}  -> compression ratio {ratio:.1f}:1")

    html = decode(main_res)
    if not html:
        print("  !! could not decode body (install brotli or use --no-brotli). Skipping HTML analysis.")
        return 1

    print("\n=== 2. Metadata / SEO ===")
    m = meta_audit(html)
    print(f"  title ({m['title_len']} chars): {m['title']}")
    print(f"  description ({m['description_len']}): {str(m['description'])[:100]}")
    print(f"  canonical      : {m['canonical']}")
    print(f"  robots         : {m['robots']}")
    print(f"  og present     : {', '.join(m['og_properties']) or 'NONE'}")
    if m["og_missing"]:
        print(f"  og MISSING     : {', '.join(m['og_missing'])}   <-- check social sharing!")
    print(f"  twitter        : {', '.join(m['twitter_properties']) or 'NONE'}")
    print(f"  h1/h2          : {m['h1_count']} / {m['h2_count']}" + ("   <-- h1 count != 1" if m["h1_count"] != 1 else ""))
    print(f"  JSON-LD        : {m['jsonld_blocks']} blocks, types={m['jsonld_types']}")
    print(f"  images         : {m['img_total']} total, {m['img_no_alt']} missing alt")

    print("\n=== 3. Payload composition ===")
    total = m["html_chars"] or 1
    print(f"  HTML raw       : {m['html_chars']:,} chars  (gzip {m['html_gzip']:,})")
    print(f"    class attrs  : {m['class_attr_chars']:,} ({100*m['class_attr_chars']/total:.1f}%)  <- Tailwind bloat, compresses well")
    print(f"    inline script: {m['inline_script_chars']:,} ({100*m['inline_script_chars']/total:.1f}%)")
    print(f"    inline <svg> : {m['inline_svg']} instances")
    print(f"    <button>     : {m['anchor_buttons']}  <- primary CTAs should be <a href> for crawlability")

    js, css, no_module = asset_list(html, base)
    print(f"\n  scripts: {len(js)}  stylesheets: {len(css)}")
    tjs = tcss = 0
    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        results = list(ex.map(lambda u: fetch(u, args.proxy, accept, read=True), sorted(js | css)))
    for r in sorted(results, key=lambda r: -r["wire_bytes"]):
        kind = "CSS" if r["url"].endswith(".css") else "JS "
        flag = " (noModule: modern browsers skip)" if r["url"].split("?")[0] in no_module else ""
        print(f"    {r['wire_bytes']:>9,} B  {kind} {r['url'].split('/')[-1][:48]}{flag}")
        if r["url"].endswith(".css"):
            tcss += r["wire_bytes"]
        elif r["url"].split("?")[0] not in no_module:
            tjs += r["wire_bytes"]
    print(f"\n  JS  (modern browsers): {tjs:,} B = {tjs/1024:.1f} KB")
    print(f"  CSS                  : {tcss:,} B = {tcss/1024:.1f} KB")
    print(f"  HTML                 : {main_res['wire_bytes']:,} B = {main_res['wire_bytes']/1024:.1f} KB")
    crit = tjs + tcss + main_res["wire_bytes"]
    verdict = "OK" if crit < 300_000 else "HEAVY"
    print(f"  ---> first-load total: {crit:,} B = {crit/1024:.1f} KB  [{verdict}]")

    print(f"\n=== 4. robots.txt / sitemap.xml ===")
    for p in ("/robots.txt", "/sitemap.xml"):
        r = fetch(base + p, args.proxy, accept, read=True)
        txt = decode(r)
        print(f"  {p}: {r['status']}  {r['wire_bytes']:,} B")
        if p.endswith("robots.txt") and txt:
            for line in txt.splitlines():
                if line.strip() and not line.strip().startswith("#"):
                    print(f"      {line}")
            if re.search(r"^Disallow:\s*/_next", txt, re.M | re.I):
                print("      !! Disallow /_next/ — longest-match rules may block CSS/JS for generic crawlers")
        if p.endswith("sitemap.xml") and txt:
            locs = re.findall(r"<loc>(.*?)</loc>", txt)
            mods = re.findall(r"<lastmod>(.*?)</lastmod>", txt)
            print(f"      {len(locs)} URLs, {len(set(mods))} distinct lastmod values"
                  + ("   !! all identical -> lastmod carries no signal" if len(mods) > 1 and len(set(mods)) == 1 else ""))

    print(f"\n=== 5. Internal links requiring a redirect (wasted RTT) ===")
    links = internal_links(html, base)
    sample = links[: args.sample]
    bad = []
    with concurrent.futures.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(lambda u: fetch(base + u, args.proxy, accept, read=False), sample))
    for r in res:
        loc = r["headers"].get("location", "")
        mark = "  <-- REDIRECT" if 300 <= r["status"] < 400 else ""
        print(f"    {r['status']}  {r['url'].replace(base, '')}  {('-> ' + loc) if loc else ''}{mark}")
        if 300 <= r["status"] < 400:
            bad.append((r["url"].replace(base, ""), r["status"], loc))
    if bad:
        print(f"\n  {len(bad)} internal link(s) cost an extra round-trip. Fix the hrefs in the data/templates:")
        for u, s, l in bad:
            print(f"    {u}  ({s} -> {l})")

    if args.json:
        with open(args.json, "w") as f:
            json.dump({"main": {k: v for k, v in main_res.items() if k != "body"},
                       "meta": m, "js_bytes": tjs, "css_bytes": tcss,
                       "redirects": bad}, f, ensure_ascii=False, indent=2)
        print(f"\n  JSON written to {args.json}")

    print("\n=== Next: real-browser Core Web Vitals ===")
    print("  agent-browser vitals <url> --json")
    print("  * run it 3x and take the steady-state number; the first cold run includes TLS/proxy handshake")
    print("  * if the sandbox blocks egress, re-run with HTTPS_PROXY set and outside the sandbox")
    return 0


if __name__ == "__main__":
    sys.exit(main())
