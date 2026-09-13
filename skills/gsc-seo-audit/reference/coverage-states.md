# Interpreting indexing results

`inspect`, `indexing`, and `site-audit` all return a `coverage_state` string per
URL (Google's own human-readable category name, not a code) plus a `verdict`
(`PASS` / `FAIL` / `NEUTRAL`). This table maps each category to what it means
and what's worth telling the user. Source: [Search Console Help — Page indexing report](https://support.google.com/webmasters/answer/7440203)
and the [UrlInspectionResult reference](https://developers.google.com/webmaster-tools/v1/urlInspection.index/UrlInspectionResult).

## Indexed (verdict: PASS)

| coverage_state | Meaning | Action |
|---|---|---|
| Submitted and indexed | Working as intended. | None. |
| Indexed, though blocked by robots.txt | Indexed despite a robots.txt disallow — Google had the content from another source (e.g. it was linked with descriptive text). | If blocking was intentional, use `noindex` instead of robots.txt — robots.txt only blocks crawling, not indexing. |
| Page indexed without content | In the index, but Google couldn't read the content (cloaking, JS rendering issue, empty response to Googlebot). | Fetch as Googlebot (or check `page_fetch_state`) to see what Google actually received. |

## Not indexed by choice or structure (verdict: NEUTRAL — usually not a bug)

| coverage_state | Meaning | Action |
|---|---|---|
| Alternate page with proper canonical tag | This URL correctly points to a canonical elsewhere; the canonical is indexed instead. | None — this is the intended outcome of a canonical tag. |
| Duplicate without user-selected canonical | Google found duplicates and picked one itself; you didn't specify a canonical. | Add an explicit `rel=canonical` if you have a preference; otherwise low priority. |
| Duplicate, Google chose different canonical than user | Your declared canonical was overridden. | Worth investigating if the page Google prefers isn't the one you want ranking — check for it being weaker (thinner content, fewer inbound links) than your intended canonical. |
| Page with redirect | Non-canonical URL that redirects elsewhere; expected to never be indexed itself. | None, unless the redirect target is wrong. |

## Not indexed — usually worth attention (verdict: NEUTRAL or FAIL)

| coverage_state | Meaning | Action |
|---|---|---|
| Crawled - currently not indexed | Google fetched it but chose not to index it (often a quality/uniqueness signal, not a technical block). | Check thin/duplicate content, low-value pages, or weak internal linking. Can resolve on its own after a re-crawl. |
| Discovered - currently not indexed | Google knows the URL exists but hasn't crawled it yet — usually a crawl-budget/prioritization decision, not an error. | If it's an important page, add internal links to it and make sure it's in the sitemap. Don't request re-indexing repeatedly; it doesn't speed this up. |
| URL is unknown to Google | Google has no record of this URL at all. | Check it's actually linked from somewhere or in a submitted sitemap. Brand new URLs land here until first crawled. |

## Blocked (verdict: FAIL — usually needs a fix, unless intentional)

| coverage_state | Meaning | Action |
|---|---|---|
| Blocked by robots.txt | robots.txt disallows crawling this path. | Confirm intentional. If not, fix the robots.txt rule. |
| URL marked 'noindex' | A `noindex` meta tag or `X-Robots-Tag` header is present. | Confirm intentional. If not, remove the directive. |
| Blocked due to unauthorized request (401) | Googlebot got an auth challenge. | Remove auth for Googlebot's user agent/IP range, or confirm the page should be private. |
| Blocked due to access forbidden (403) | Googlebot was denied by a WAF/CDN rule or server config, not real auth. | Check for bot-blocking rules (Cloudflare, WAF) that also catch Googlebot. |
| Blocked due to other 4xx issue | Some other 4xx status was returned to Googlebot. | Run `inspect` on the URL and check `page_fetch_state` for specifics. |
| Not found (404) | Page genuinely returns 404. | Expected for removed content. If the page should exist, check for a bad deploy or broken route. |
| Soft 404 | Page returns 200 but the content looks like an error/empty page to Google. | Return a real 404/410 for missing content, or add substantive content if the page is meant to exist. |
| Server error (5xx) | Server errored when Googlebot requested it. | Check server logs around the `last_crawl_time`; could be a capacity or crash issue specific to that path. |
| Redirect error | Redirect chain too long, a loop, or the target itself is broken. | Trace the chain (`curl -IL`) and collapse it to a single hop. |

## Reading `verdict` vs `coverage_state`

`verdict` is the coarse signal (`PASS` = indexed, `FAIL` = a real problem, `NEUTRAL`
= excluded on purpose or by normal Google discretion). Lead with `verdict` when
summarizing counts for a user, then use `coverage_state` to explain *why* —
don't report every `NEUTRAL` row as a "problem"; "Discovered - currently not
indexed" on a brand-new blog post is normal, not a bug.

## Related fields worth surfacing alongside coverage_state

- `robots_txt_state` (`ALLOWED`/`DISALLOWED`) and `indexing_state`
  (`INDEXING_ALLOWED`/`BLOCKED_BY_META_TAG`/`BLOCKED_BY_HTTP_HEADER`) pinpoint
  *which* mechanism is blocking a page when coverage_state is one of the
  "Blocked" rows above.
- `google_canonical` vs `user_canonical` — when these differ, Google overrode
  the publisher's canonical choice; worth calling out explicitly.
- `page_fetch_state` gives the low-level fetch outcome (`SERVER_ERROR`,
  `ACCESS_DENIED`, `REDIRECT_ERROR`, etc.) — more specific than coverage_state
  for debugging *why* a fetch failed.

## What this API can't do

- There's no bulk "list every indexed/unindexed URL" endpoint — indexing status
  is only available per-URL via `inspect`/`indexing`/`site-audit`, which is why
  `site-audit` samples from the sitemap rather than checking everything.
- The public "Indexing API" (`indexing.googleapis.com`) is **not** a general
  request-indexing mechanism — Google restricts it to JobPosting and
  BroadcastEvent (livestream) structured data. Don't tell a user you can
  "request indexing" for an arbitrary page via API; that action only exists in
  the Search Console UI ("Request indexing" button), which isn't
  API-accessible for ordinary pages.
