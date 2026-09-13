# Google Search Console SEO & Indexing Audit Skill + MCP Server

A read-only Google Search Console integration for Claude Code and other MCP clients. It combines:

- the Search Console API for search analytics, sitemaps, and URL Inspection;
- a standalone CLI for setup checks and scripting;
- a sitemap-driven indexing audit that prioritizes URL Inspection calls (a 2,000/day quota per property) toward pages most likely to have a real problem;
- a local property allowlist and row-count safety limit.

The integration does not submit sitemaps, request indexing, or otherwise mutate the property.

## Requirements

- Python 3.9+
- A Google Cloud project with the **Search Console API** enabled
- A service account with a JSON key, added as a **Full** user on each Search Console property to query

## 1. Create a Google Cloud project and enable the API

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project (or pick an existing one).
2. Go to **APIs & Services > Library**, search for **Search Console API**, and enable it.

## 2. Create a service account and key

1. Go to **IAM & Admin > Service Accounts > Create Service Account**. Any name works (e.g. `gsc-seo-reader`); it doesn't need any project-level IAM role — the permission that matters is granted in Search Console itself, in the next step.
2. Open the new service account, go to the **Keys** tab, **Add Key > Create new key > JSON**. This downloads a JSON file.
3. Store that file somewhere outside this repository (e.g. `~/.config/gsc-seo-audit/service-account.json`) — never commit it. `.gitignore` in this directory already excludes `credentials*.json` and `service-account*.json` as a backstop.
4. Note the service account's email address (`...@...iam.gserviceaccount.com`) — you'll need it in the next step.

## 3. Add the service account to Search Console

1. Go to [Search Console](https://search.google.com/search-console) and select the property.
2. **Settings > Users and permissions > Add user**.
3. Paste the service account's email and set permission to **Full**. Do not use Restricted — Restricted users can't access URL Inspection or sitemap data via the API. Owner is unnecessary (it also grants the ability to manage other users).
4. Note the exact site URL string Search Console shows for the property — domain properties look like `sc-domain:example.com`, URL-prefix properties look like `https://example.com/`. Reports use this exact string.

## Install

```bash
cd skills/gsc-seo-audit
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## Configure

```bash
export GSC_CREDENTIALS_PATH=/secure/path/service-account.json
export GSC_SITE_URL=sc-domain:example.com
```

Optional safety settings:

```bash
export GSC_ALLOWED_SITE_URLS=sc-domain:example.com,https://other-site.com/
export GSC_MAX_LIMIT=1000
```

`GSC_ALLOWED_SITE_URLS` is useful when the service account can see more properties than you want this integration to query in a given context — it's a local restriction, not a substitute for Search Console's own permissions.

## Verify credentials and access

```bash
.venv/bin/python gsc_query.py properties --output table
```

This needs no site URL — it lists only properties the service account can access. If it returns an empty list, double check: the service account email was added as a Full user on the property, the Search Console API is enabled on the project the key belongs to, and `GSC_CREDENTIALS_PATH` points at the right file.

```bash
.venv/bin/python gsc_query.py performance --days 7 --site-url "sc-domain:example.com"
```

## Configure an MCP client

Point the MCP client at the Python interpreter in the environment above and the checked-out `gsc_mcp_server.py`. Replace the placeholder paths and keep the credential path outside the repository:

```json
{
  "mcpServers": {
    "gsc-seo-audit": {
      "command": "/path/to/skills/gsc-seo-audit/.venv/bin/python",
      "args": ["/path/to/skills/gsc-seo-audit/gsc_mcp_server.py"],
      "env": {
        "GSC_CREDENTIALS_PATH": "/secure/path/service-account.json",
        "GSC_SITE_URL": "sc-domain:example.com"
      }
    }
  }
}
```

The server communicates over stdio and writes no normal output to stdout (reserved for MCP messages); startup and configuration errors go to stderr.

In Claude Code, you generally don't need this at all — just run `gsc_query.py` directly, as shown above.

## MCP tools

| Tool | Purpose |
| --- | --- |
| `gsc_properties` | List accessible Search Console properties |
| `gsc_search` | Rows by dimension (query, page, device, country, date) with clicks/impressions/CTR/position |
| `gsc_page_queries` | Queries driving traffic to one specific page |
| `gsc_performance` | Totals plus a daily trend |
| `gsc_compare` | Two date ranges side by side, sorted by biggest change |
| `gsc_sitemaps` | Submitted sitemaps, status, and URL counts |
| `gsc_inspect` | Full URL Inspection for one URL (indexing verdict, coverage state, canonical, rich results) |
| `gsc_indexing` | Batch URL Inspection for a specific list of URLs (max 100) |
| `gsc_site_audit` | Sitemap-driven indexing audit prioritizing zero-traffic URLs |

## CLI examples

```bash
# Discover properties
.venv/bin/python gsc_query.py properties --output json

# Common reports
.venv/bin/python gsc_query.py search --dimensions query,page --days 28 --limit 50 --output json
.venv/bin/python gsc_query.py performance --days 7
.venv/bin/python gsc_query.py page-queries --page-url "https://example.com/blog/post" --days 28
.venv/bin/python gsc_query.py compare --p1-start 2026-01-01 --p1-end 2026-01-31 --p2-start 2026-02-01 --p2-end 2026-02-28

# Indexing
.venv/bin/python gsc_query.py inspect --page-url "https://example.com/about"
.venv/bin/python gsc_query.py indexing --urls "https://example.com/,https://example.com/about"
.venv/bin/python gsc_query.py site-audit --limit 25 --lookback-days 90
```

## Development checks

The tests use fake Google clients and do not make network requests (the MCP protocol test does spawn the real server as a subprocess over stdio, but never calls Google):

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q gsc_client.py gsc_query.py gsc_mcp_server.py tests
```

For a live smoke test, use the configured environment and a real property. Search Console data is delayed 2-3 days and only retained for the trailing 16 months — don't be surprised by empty results outside that window.

## Official references

- [Search Console API overview](https://developers.google.com/webmaster-tools/v1/api_reference_index)
- [Search Analytics: query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [URL Inspection API](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)
- [Usage limits](https://developers.google.com/webmaster-tools/limits)
- [Page indexing report — why pages aren't indexed](https://support.google.com/webmasters/answer/7440203)
- [Managing owners, users, and permissions](https://support.google.com/webmasters/answer/7687615)
- [Reference project](https://github.com/oreillyjw/gsc-skill-mcp)
