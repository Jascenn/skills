---
name: web-seo-perf-audit
description: This skill should be used when auditing a live website for SEO, crawlability, social-sharing metadata, or first-load payload problems — e.g. "帮我看看这个页面怎么优化", "audit this site", "why isn't my site ranking", "检查一下 SEO", "为什么分享出去没缩略图", "页面太大了怎么优化", "hreflang 检查". It measures real response headers, compression, asset weights, metadata completeness, sitemap coverage, and redirecting internal links, then produces a prioritised fix list.
---

# Web SEO & Performance Audit

Audit a live URL and produce an evidence-backed, priority-ranked optimisation report.

## Purpose

Most "optimise my site" requests get answered with guesses. This skill replaces guessing with measurement: probe the real production response, separate bandwidth problems from crawlability problems from metadata problems, and report only what is actually broken.

The single most important distinction this skill enforces: **page speed and page discoverability are different problems with different fixes.** A site can have a perfect LCP/CLS and still be invisible in search and share as a blank card. Measure both, then lead the report with whichever is actually failing.

## Workflow

### 1. Establish what the production response actually is

Run the bundled script first — it covers the probing steps in one pass:

```bash
python3 scripts/audit_site.py https://example.com --proxy http://127.0.0.1:7890 --sample 8
```

Omit `--proxy` when none is needed. Add `--json out.json` to keep raw numbers.

It reports: status/server/TTFB, the real `content-encoding`, on-the-wire bytes, missing security headers, full metadata inventory, payload composition, per-asset compressed sizes split into modern vs `noModule`, robots.txt and sitemap health, and any internal link returning 3xx.

### 2. Measure Core Web Vitals with a real browser

Header probing cannot tell you LCP or CLS. Use a browser:

```bash
agent-browser vitals https://example.com --json
```

**Run it at least three times and take the steady-state number.** The first cold run includes TLS/proxy handshake and routinely overstates LCP by an order of magnitude — a site measuring 1052 ms steady-state produced 2264 ms on the first cold pass. Reporting that first number as a finding is a false positive.

If the sandbox blocks egress (`net::ERR_CONNECTION_CLOSED`), re-run outside the sandbox with explicit `HTTPS_PROXY` / `HTTP_PROXY` environment variables.

For a deeper timeline inside the page, use `agent-browser eval` against the Performance API:

```js
performance.getEntriesByType('paint')
performance.getEntriesByType('navigation')[0]
performance.getEntriesByType('resource')
document.getElementsByTagName('*').length
```

With a warm browser profile, `transferSize` on resources reads 0 — that means cache hit, not a missing asset.

### 3. Check the bilingual / multilingual dimension explicitly

The most commonly missed category, and the findings are usually severe. If the site has an `/en/` or `/locale/` branch:

- Does each branch set its own `<html lang>`? A `lang="zh-CN"` on English pages is a real bug affecting search language filters and screen readers (WCAG 3.1.1).
- Are `hreflang` alternates declared **both directions**, with self-referencing canonicals? Check `<link rel="alternate" hreflang>`, the HTTP `Link:` header, and `<meta http-equiv="content-language">`.
- Does the sitemap contain the localised URLs?

A full `/en` mirror with zero hreflang means two competing copies of the same content, each diluting the other.

### 4. Verify every claim before writing it

| Claim | How to verify |
|---|---|
| "The page is too heavy" | Compare wire bytes **with** and **without** `Accept-Encoding`. A 317 KB HTML is often 23 KB brotli. Never infer weight from raw file size. |
| "The sitemap lastmod is useless" | Count **distinct** values, not whether the first few match. Report the real ratio (e.g. 351/361 identical), not "all identical". |
| "These links are broken" | A 3xx is not a 404. Distinguish redirects (wasted RTT) from genuine breakage, and confirm the destination returns 200. |

Before proposing any code change, confirm the local checkout matches production. If the live site has content the local repo lacks, surface that as a blocking prerequisite — edits to a stale tree never reach production.

### 5. Write the report

Structure: **conclusion → measured evidence → prioritised fixes → execution order.**

- Lead with the verdict on speed, including the fact that it is fine when it is fine. "Don't optimise speed" is itself a valuable finding.
- Rank by impact, not by ease. Tag each item P0/P1/P2.
- Give exact numbers with units. "LCP 0.21–1.05 s" beats "fast".
- Include copy-pasteable code for the fixes.
- State what is correctly configured and should be left alone, so the user does not break working things.
- Explicitly flag any finding that reverses an earlier assumption, so a reader who saw a previous version is not misled.

## Pitfalls

- **Brotli is the default on Vercel and Cloudflare, but the Python `brotli` module is often absent.** The bundled script detects this and downgrades to a gzip request automatically; in ad-hoc probing code, remember a bare request returns the raw body and a partial read can lose `content-length`.
- **robots.txt groups do not merge.** A `Disallow: /_next/` under `User-Agent: *` does not affect Googlebot when Googlebot has its own group. Check whether major crawlers have their own block before declaring an indexing problem.
- **robots.txt uses longest-match, not first-match.** `Disallow: /_next/` (7 chars) beats `Allow: /*.css` (6 chars); a later, longer Allow does not rescue it.
- **`Disallow: *.json` is not a valid prefix rule** — flag it for removal instead of reasoning about its effect.
- **A `<button>` where a link belongs is both an SEO and a UX defect.** Primary CTAs rendered as `<button>` cannot be opened in a new tab, are not followed by crawlers, and fail outright when JS does not run.
- **`next.config.mjs` can contain dead analysis branches.** An `ANALYZE === 'true'` guard is useless when `@next/bundle-analyzer` is absent from `devDependencies` — verify the tool runs before recommending it.
- **Decorative emoji without `aria-hidden` pollute both accessibility and AI extraction.** Screen readers announce them, and text-extraction tools treat them as body content.

## Bundled resources

- `scripts/audit_site.py` — one-pass audit: headers, compression ratio, metadata inventory, payload composition, robots/sitemap health, redirect detection. Run `--help` for flags.
- `references/checklist.md` — item-by-item checklist with thresholds and the cost of each failure, covering what the script does not: accessibility, PWA, analytics wiring, structured-data depth, content strategy.
