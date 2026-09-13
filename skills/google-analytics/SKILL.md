---
name: google-analytics
description: Query Google Analytics 4 (GA4) properties through a read-only MCP server or the bundled CLI. Use this skill whenever the user mentions Google Analytics, GA4, Analytics properties, active users, sessions, page views, traffic sources, campaigns, conversions, revenue, realtime visitors, dimensions, metrics, or asks for a report from a property they own or can access. It discovers accessible properties, runs standard or custom Data API reports, and presents results as concise tables or structured JSON/CSV.
compatibility: Python 3.10+, a Google Cloud project with the Google Analytics Data API and Admin API enabled, and a read-only Google identity (service account or Application Default Credentials).
---

# Google Analytics 4 query skill

Use the bundled read-only Google Analytics Data API client and MCP server to answer questions about GA4 properties. The Admin API is used only to discover accounts and properties that the configured identity can access; the Data API is used to retrieve reports.

## Safety and scope

- Treat Google Analytics data as private business data. Never print, commit, upload, or ask the user to paste a service-account private key.
- This integration is read-only. Do not add tools or call Google Analytics Admin API mutation endpoints through this skill.
- “Owned properties” means properties accessible to the configured Google identity. Google’s API does not establish legal ownership. Use `GA4_ALLOWED_PROPERTY_IDS` when the user wants a hard local allowlist.
- Never guess a property ID. If no default is configured, call `ga_list_properties` first and ask the user to choose when more than one property is available.
- State the property, date range, dimensions, metrics, and filters used in every substantive answer. This prevents a correct number from being mistaken for a different report.
- Do not cache API responses in a shared or persistent location. Reports can change as Google reprocesses data and may contain sensitive information.

## Prerequisites and setup

Read `README.md` in this skill directory for the full setup walkthrough. The short version is:

1. Enable **Google Analytics Data API** and **Google Analytics Admin API** in a Google Cloud project.
2. Create a service account, or configure Application Default Credentials.
3. Add the service-account email as at least **Viewer** in each GA4 property’s Property Access Management page.
4. Install `requirements.txt` in a dedicated virtual environment.
5. Configure these environment variables for the MCP server or CLI:

   - `GA4_CREDENTIALS_PATH` — optional path to a service-account JSON key. If omitted, Google ADC is used.
   - `GA4_PROPERTY_ID` — optional default numeric GA4 property ID.
   - `GA4_ALLOWED_PROPERTY_IDS` — optional comma-separated numeric IDs. When set, explicit and default queries outside this list are rejected.
   - `GA4_DEFAULT_DAYS` — optional default lookback, default `30`.
   - `GA4_MAX_DAYS` — optional safety ceiling, default `3650`.
   - `GA4_MAX_LIMIT` — optional maximum rows returned by one query, default `1000`.

The credential identity must have `analytics.readonly` access. A Cloud project having the APIs enabled does not itself grant access to a GA4 property.

## MCP workflow

Prefer MCP tools when the server is configured:

1. Call `ga_list_properties` if the property is missing, ambiguous, or the user asks which properties are available.
2. Resolve the exact property ID. Preserve the user’s explicit property override for this request only; do not change the default configuration.
3. Translate natural language dates to an explicit range. Use `days` for a relative range such as “last 7 days”; use `start_date` and `end_date` for calendar dates. Do not silently mix the two.
4. Use a convenience tool for common questions:
   - `ga_overview`: aggregate users, sessions, page views, bounce rate, new users, and revenue.
   - `ga_pages`: pages ranked by views.
   - `ga_sources`: source/medium traffic breakdown.
   - `ga_countries`: country breakdown.
   - `ga_devices`: device-category breakdown.
   - `ga_daily`: daily trend.
   - `ga_realtime`: current active users by device category.
5. Use `ga_get_metadata` before a custom query when the user names an unfamiliar or custom dimension/metric. Then use `ga_run_report` with explicit `dimensions` and `metrics`.
6. Keep exploratory queries small. Increase `limit` only when the user needs more rows, and prefer aggregation or a narrower date range over dumping raw event-level data.
7. Explain `(not set)`, sampling/thresholding indicators, and metric semantics when they affect interpretation. Treat metric values as strings in JSON because currency and decimal values should not be rounded implicitly.

### Custom report example

```json
{
  "property_id": "123456789",
  "days": 7,
  "dimensions": ["date", "country"],
  "metrics": ["activeUsers", "sessions"],
  "limit": 100,
  "order_by": [
    {"metric": {"metric_name": "activeUsers"}, "desc": true}
  ]
}
```

Dimension and metric filters use the Google Analytics Data API `FilterExpression` shape. For example:

```json
{
  "filter": {
    "field_name": "country",
    "string_filter": {"match_type": "EXACT", "value": "Japan"}
  }
}
```

Use `and_group`, `or_group`, and `not_expression` to compose filters. Keep filters aligned with their scope: dimension filters apply before aggregation and metric filters apply after aggregation.

## CLI fallback and verification

If MCP is unavailable, run the bundled CLI from this skill directory using the configured Python interpreter:

```bash
python3 ga_query.py properties --output table
python3 ga_query.py overview --days 7 --output json
python3 ga_query.py pages --days 30 --limit 10 --output csv
python3 ga_query.py report --days 7 --dimensions date,country --metrics activeUsers,sessions
```

Run `python3 -m unittest discover -s tests` for offline unit/integration coverage. A live smoke test requires real credentials and an accessible property:

```bash
python3 ga_query.py properties
python3 ga_query.py overview --days 7 --property-id 123456789
```

When a request fails, distinguish configuration errors, Google authentication/permission errors, invalid dimensions or metrics, and quota/rate-limit errors. Give the user the smallest actionable fix and do not expose credential contents.

## Response format

For a conversational answer, lead with the result, then show a compact table when there are multiple rows, followed by:

```text
Property: <display name and numeric ID>
Range: <start> to <end>
Dimensions: <...>
Metrics: <...>
Filters: <none or concise description>
```

For downstream use, request or return JSON/CSV from the CLI. Preserve the API metric values and include the report’s `row_count`, metadata, and headers so the result is auditable.
