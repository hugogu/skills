---
name: gsc-seo-audit
description: Query and analyze Google Search Console (GSC) data for SEO performance and page indexing health — search rankings, clicks, impressions, CTR, average position, indexed vs. not-indexed pages, sitemaps, and URL-level indexing status — through a read-only MCP server or the bundled CLI. Use this skill whenever the user asks about their site's SEO, organic search traffic, Google rankings, why a page isn't showing up in search, indexing problems or errors, crawl issues, Search Console data, or wants an SEO audit, indexing audit, or search-performance report for a property they own or can access — even if they don't say "Google Search Console" or "GSC" by name.
compatibility: Python 3.9+, a Google Cloud project with the Search Console API enabled, and a service account added as a Full user on each property to query.
---

# Google Search Console SEO & indexing audit skill

Use the bundled read-only Search Console API client and MCP server to answer questions about a site's organic search performance and indexing health. This skill does two distinct jobs: `gsc_client.py` retrieves and shapes GSC data, and this document teaches you how to turn that data into an actual SEO finding — the raw numbers alone rarely answer "is my SEO healthy" or "why isn't this page ranking."

## Safety and scope

- Treat Search Console data as private business data. Never print, commit, upload, or ask the user to paste a service-account private key.
- This integration is read-only (`webmasters.readonly` scope). Do not add tools that submit sitemaps, request indexing, or otherwise mutate the property.
- The public Indexing API (`indexing.googleapis.com`) is **not** a general "request indexing" mechanism — Google restricts it to JobPosting and BroadcastEvent structured data. Don't imply you can request indexing for an arbitrary page via API; that action only exists as the "Request indexing" button in the Search Console UI.
- Never guess a site URL. If none is configured and the user didn't name one, call `gsc_properties` first and ask the user to choose when more than one property is available.
- State the site URL, date range, and report used in every substantive answer — this prevents a correct number from being mistaken for a different property or period.
- Search Analytics data is delayed 2-3 days and is only retained for the trailing **16 months**. A query reaching further back will silently return less data, not an error — don't interpret a sparse older range as a traffic collapse without checking the date window first.

## Prerequisites and setup

Read `README.md` in this skill directory for the full walkthrough (creating the GCP project, service account, and adding it to the property). The short version:

1. Enable the **Search Console API** in a Google Cloud project.
2. Create a service account and download a JSON key for it.
3. Add the service account's email as a **Full** user (not Restricted — Restricted accounts can't use URL Inspection or see sitemaps) on each property to query: Search Console > Settings > Users and permissions.
4. Install `requirements.txt`.
5. Configure environment variables:

   - `GSC_CREDENTIALS_PATH` — path to the service-account JSON key.
   - `GSC_SITE_URL` — optional default property (`sc-domain:example.com` or `https://example.com/`).
   - `GSC_ALLOWED_SITE_URLS` — optional comma-separated allowlist. When set, queries for any other property are rejected, even if the credential can technically see it.
   - `GSC_MAX_LIMIT` — optional safety ceiling on row counts (default 1000).

## MCP workflow

Prefer MCP tools when the server is configured; otherwise run the CLI directly (see below) — both call the same underlying code and return identical JSON.

1. Call `gsc_properties` if the site is missing or ambiguous, and ask the user to choose when more than one is available.
2. Pick a lookback window. Relative ranges ("last 7 days", "this month") map to `days`; explicit ranges use start/end dates. Remember the 2-3 day data lag — "today" and "yesterday" usually have no data yet.
3. Reach for the right tool:
   - `gsc_search` — top rows for one or more dimensions (`query`, `page`, `device`, `country`, `date`). This is the workhorse for most performance questions.
   - `gsc_page_queries` — which queries drive traffic to one specific page.
   - `gsc_performance` — totals plus a daily trend, for a quick health check.
   - `gsc_compare` — two date ranges side by side, sorted by biggest change. Use this instead of eyeballing two separate `gsc_search` calls.
   - `gsc_inspect` — full indexing detail for one URL. This is what answers "why isn't page X showing up in search."
   - `gsc_indexing` — the same check across a specific list of URLs (max 100) when the user already knows which pages to check.
   - `gsc_site_audit` — a sitemap-driven indexing sweep when the user wants to know about indexing problems *across the site* rather than one URL. See "Indexing audit" below before using this one — it needs interpretation, not just a raw dump.
   - `gsc_sitemaps` — sitemap submission status (separate from actual indexing status; a sitemap can be error-free while its pages still aren't indexed).
4. Read `reference/coverage-states.md` before explaining any `coverage_state` value to the user — several states that sound alarming (e.g. "Discovered - currently not indexed") are normal and don't need action, while others genuinely do.

## CLI fallback and verification

If MCP is unavailable, run the bundled CLI from this skill's directory:

```bash
python3 gsc_query.py properties --output table
python3 gsc_query.py search --days 28 --output json
python3 gsc_query.py performance --days 7 --site-url "sc-domain:example.com"
python3 gsc_query.py site-audit --output json
```

Every subcommand has its own `--help`. Run `python3 -m unittest discover -s tests` for offline unit/integration coverage (no credentials needed — it mocks the Google client). For a live smoke test once credentials are configured:

```bash
python3 gsc_query.py properties
python3 gsc_query.py performance --days 7 --site-url "sc-domain:example.com"
```

When a request fails, the error message distinguishes configuration problems (missing credentials, property not in the allowlist), permission problems (403 — service account not added as Full user), and quota/rate-limit problems (429). Give the user the smallest actionable fix rather than a generic "it failed."

## SEO analysis playbooks

The tools above return facts; these playbooks turn facts into a finding. Request `--output json` (CLI) or use the MCP tools' JSON responses directly — you'll be doing arithmetic over the rows, not just displaying them.

### Health check

Pull `gsc_performance` for the requested window, then `gsc_compare` against the immediately preceding period of equal length. A change of roughly 15-20%+ in clicks or impressions is usually worth calling out; smaller swings are often ordinary week-to-week noise. If clicks dropped but impressions didn't, suspect a ranking/CTR problem (see below); if both dropped together, suspect an indexing or technical issue (crawl errors, a bad deploy, seasonality) — check `gsc_site_audit` next.

### Indexing audit

`gsc_site_audit` samples the sitemap, checks which sampled URLs got zero clicks/impressions in the lookback window (a cheap signal computed from Search Analytics, not proof of non-indexing), and prioritizes those for a real `URL Inspection` call — the only API that gives ground truth on indexing status. There's no bulk "list every indexed page" endpoint, so this sampling approach is the practical ceiling of what the API supports; say so if the user expects a complete inventory.

To present the results:
1. Group `results[].coverage_state` using `reference/coverage-states.md` — split into "expected, no action" (canonicalization outcomes, "Discovered/Crawled - currently not indexed" on new content) versus "worth investigating" (blocked, error, soft-404 states).
2. Only report a problem count from the states in the second group. Reporting every `NEUTRAL` verdict as broken will make a healthy site look broken.
3. If `zero_impression_count` is much larger than what got inspected (quota-limited to 100/call), say so — the sample is indicative, not exhaustive.
4. If no sitemap is submitted at all, ask the user for one (or their homepage, to infer `/sitemap.xml`) rather than silently giving up.

### CTR opportunity finder

Pull `gsc_search` with `dimensions=query` over a decent window (28-90 days) and enough rows to see the long tail (`limit=100`+). Bucket the rows by position range (1-3, 4-10, 11-20, 21+) and compute each bucket's average CTR from *this site's own data* — not a generic industry benchmark, which varies wildly by query intent, brand strength, and SERP features and will produce false positives. Flag individual queries with meaningful impressions (e.g. 100+) whose CTR sits well below their own bucket's average: these are ranking fine but underperforming on the click, which usually means the title/meta description isn't compelling relative to competitors for that query.

### Striking-distance keywords

From the same `gsc_search` pull, filter to queries at position 8-20 with non-trivial impressions. These are already close to page one and are typically the highest-leverage on-page optimization targets — closing the gap from position 12 to position 6 is usually far cheaper than winning a brand-new keyword from nothing.

### Cannibalization check

Pull `gsc_search` with `dimensions=query,page`. Group rows by `query` and look for queries where two or more distinct pages each receive meaningful impressions. That's a signal of internal competition — the fix is usually consolidating the pages or sharpening each page's targeting, not creating more content for the same query.

## Response format

For a conversational answer, lead with the finding, then a compact table if there are multiple rows, then:

```text
Property: <site URL>
Range: <start> to <end>
Report: <which tool/report, and dimensions if relevant>
```

For downstream use (the user is piping this into something else), return the JSON as-is rather than reformatting it — it already carries `site_url`, the date range, and row-level detail needed to audit the number later.
