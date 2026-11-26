# Site audit checklist

Thresholds and the cost of each failure. Use alongside `scripts/audit_site.py`.

## 1. Delivery & headers

| Item | Pass | Why it matters |
|---|---|---|
| `content-encoding` on HTML | `br` or `gzip` | Uncompressed HTML is 5–15× larger on the wire. A raw 317 KB page is 23 KB brotli. |
| `cache-control` on HTML | short TTL + `must-revalidate`, served via CDN | Long-TTL HTML traps users on stale content. |
| Static assets | hashed filenames + `max-age=31536000, immutable` | Enables permanent caching. |
| `strict-transport-security` | `max-age=31536000; includeSubDomains` | Prevents downgrade attacks. |
| `x-content-type-options` | `nosniff` | Blocks MIME confusion. |
| `content-security-policy` | present (even report-only) | The most commonly absent header; flag as a hardening gap, not a bug. |
| Edge cache | `HIT` on repeat requests | A `MISS` on a static page means every visitor pays origin latency. |

## 2. Metadata

| Item | Pass | Cost of failure |
|---|---|---|
| `<title>` | present, ≤ 30 CJK chars or ≤ 60 latin chars | Truncated in SERP; duplicated brand names waste the visible portion. |
| `description` | present, 70–160 chars, unique per page | Search engines synthesize a snippet from body text instead. |
| `canonical` | present, absolute, self-referencing per page | Missing canonical on templated pages risks duplicate-content dilution. |
| `og:title` `og:description` `og:url` `og:image` `og:type` `og:site_name` | all six | **WeChat, Feishu, Slack, Facebook and LinkedIn read `og:*` only — not `twitter:*`.** A missing `og:image` means a text-only share card. |
| `og:image` dimensions | 1200×630, declared with `width`/`height` | Without declared dimensions some crawlers refuse the image or crop it badly. |
| `twitter:card` | `summary_large_image` | Falls back to a small card. |
| `<h1>` | exactly one per page | Zero weakens keyword signal; multiple dilutes it. |
| JSON-LD | `WebSite` + `Organization` site-wide; per-page `SoftwareApplication` / `WebApplication` / `CollectionPage` / `Article` | No rich results, no entity understanding. |
| `lang` on `<html>` | matches the page's actual language | Wrong `lang` mis-filters the page out of language-scoped results and breaks screen readers (WCAG 3.1.1). |

## 3. Multilingual sites

| Item | Pass | Cost of failure |
|---|---|---|
| `<html lang>` per locale branch | each branch declares its own | See above; this is the single most common bilingual bug. |
| `hreflang` alternates | declared **on every page**, **both directions**, including `x-default` | Without it, translated pages compete with each other instead of serving the right audience. |
| canonical per locale | each locale points to itself, never to the other locale | Cross-locale canonicals de-index a whole branch. |
| sitemap | contains localised URLs | Localised pages may never be discovered. |
| Titles/descriptions localised | no foreign-language brand strings left in | Mixed-language titles look machine-translated and depress CTR. |

## 4. Payload

| Item | Pass | Notes |
|---|---|---|
| First-load JS | < 200 KB compressed | Measure with `noModule` polyfills excluded — modern browsers never download them, so counting them inflates the number by 40 KB+ on Next.js. |
| First-load CSS | < 50 KB compressed | Tailwind v4 output can exceed 150 KB raw; compression saves it. |
| DOM nodes | < 1,400 | Above this, layout and style recalculation cost becomes visible on mid-range mobile. |
| Inline SVG count | low, or deduplicated | SSR frameworks re-emit the full `<path>` for every icon instance. 159 icons × 422 chars = 67 KB of duplicated markup. |
| Class-attribute share of HTML | informational | Tailwind strings can reach 60% of raw HTML while compressing to almost nothing. Report it as a parse cost, never as a bandwidth cost. |
| Third-party scripts | minimal, deferred | Each adds a connection and main-thread work outside your control. |

## 5. Crawlability

| Item | Pass | Notes |
|---|---|---|
| `robots.txt` reachable | 200, cached | A 5xx or timeout causes crawlers to back off entirely. |
| `Disallow` rules | no unintended blocks of CSS/JS | Longest-match wins: `Disallow: /_next/` beats a shorter `Allow: /*.css`. |
| robots groups | per-crawler blocks are valid | Groups do not merge; verify before declaring an indexing problem. |
| AI crawler policy | intentional | Allowing search/answer bots (`OAI-SearchBot`, `PerplexityBot`, `Claude-SearchBot`) while blocking training bots (`GPTBot`, `CCBot`, `Google-Extended`) is a coherent stance — do not "fix" it. |
| `sitemap.xml` | all canonical URLs, correct count, no 404s/redirects | Compare URL count against the expected page count; missing entries are silent de-indexing. |
| `lastmod` | real per-page modification time | A single bulk timestamp across 97% of URLs removes all freshness signal. |
| Internal links | resolve in one hop | Each 3xx costs an extra RTT and leaks link equity. Trailing-slash and `.html` mismatches are the usual cause. |
| Primary CTAs | real `<a href>`, not `<button>` | Buttons cannot be opened in a new tab, are not crawled, and break without JS. |

## 6. Accessibility (frequently overlooked, cheap to fix)

| Item | Check |
|---|---|
| Decorative emoji | `aria-hidden="true"` — otherwise announced by screen readers and captured by text extractors |
| `alt` on every `<img>` | including decorative (use `alt=""`) |
| Icon-only buttons | `aria-label` present |
| Touch targets | ≥ 40×40 CSS px |
| Skip link | present and functional |
| Heading order | no skipped levels; single `h1` |

## 7. PWA (only if a manifest exists)

| Item | Pass |
|---|---|
| `theme_color` / `background_color` | match the site's actual default theme, or the launch screen flashes the wrong colour |
| `maskable` icon | present, or Android adds a white letterbox |
| `display` | intentional (`standalone` forces app-like chrome) |
| `orientation` | omit unless there is a real reason to lock it |

## 8. Reporting discipline

- Re-run every measurement at least three times for anything timing-based; keep the steady-state value and mention the variance.
- Before recommending a code edit, confirm the local checkout matches what is deployed. A stale working copy makes every fix unreachable, and that must be reported as a blocking prerequisite.
- When a later measurement contradicts an earlier statement in the same review, say so explicitly rather than quietly correcting it.
- List what is correctly configured and should be left alone — this is as useful as the defect list.
