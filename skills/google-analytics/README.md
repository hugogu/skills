# Google Analytics 4 Skill + MCP Server

This skill provides a read-only Google Analytics 4 integration for Claude Code and other MCP clients. It combines:

- the Google Analytics Admin API `accountSummaries.list` method to discover accounts and properties accessible to the configured identity;
- the Google Analytics Data API for standard, realtime, metadata, and custom reports;
- a standalone CLI for setup checks and scripting;
- a local property allowlist and row/date safety limits.

The integration does not create, edit, or delete Analytics resources.

## Requirements

- Python 3.10+
- A Google Cloud project with **Google Analytics Data API** and **Google Analytics Admin API** enabled
- A service account JSON key or Application Default Credentials (ADC)
- The service account added as **Viewer** or higher on each GA4 property to query

Google’s quickstart covers both service-account and ADC setup: <https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart>.

## Install

Create an isolated environment and install the skill dependencies:

```bash
cd skills/google-analytics
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Do not store the credential JSON in this directory or commit it to Git.

## Configure

Use either an explicit credential path:

```bash
export GA4_CREDENTIALS_PATH=/secure/path/ga4-service-account.json
export GA4_PROPERTY_ID=123456789
```

or Google ADC:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/secure/path/ga4-service-account.json
```

Optional safety settings:

```bash
export GA4_ALLOWED_PROPERTY_IDS=123456789,987654321
export GA4_DEFAULT_DAYS=30
export GA4_MAX_DAYS=3650
export GA4_MAX_LIMIT=1000
```

`GA4_ALLOWED_PROPERTY_IDS` is useful when the Google identity can see more properties than the user wants this integration to query. It is not a substitute for Google Analytics permissions.

## Verify credentials and access

The first command does not need a default property ID. It lists only properties visible to the configured identity:

```bash
.venv/bin/python ga_query.py properties --output table
.venv/bin/python ga_query.py overview --days 7 --property-id 123456789 --output json
```

If discovery returns no properties, check that the service account email was added in **Admin → Property Access Management**, that both APIs are enabled, and that the selected credentials are the ones being used by the process.

## Configure an MCP client

Point the MCP client at the Python interpreter in the environment above and the checked-out `ga_mcp_server.py`. The following is a template; replace the placeholder paths and property ID in the client’s configuration, and keep the credential path outside the repository:

```json
{
  "mcpServers": {
    "google-analytics": {
      "command": "/path/to/skills/google-analytics/.venv/bin/python",
      "args": ["/path/to/skills/google-analytics/ga_mcp_server.py"],
      "env": {
        "GA4_CREDENTIALS_PATH": "/secure/path/ga4-service-account.json",
        "GA4_PROPERTY_ID": "123456789",
        "GA4_ALLOWED_PROPERTY_IDS": "123456789,987654321"
      }
    }
  }
}
```

The server communicates over stdio. It intentionally writes no normal output to stdout because stdout is reserved for MCP messages; startup and configuration errors go to stderr.

## MCP tools

| Tool | Purpose |
| --- | --- |
| `ga_list_properties` | List accessible accounts and GA4 properties |
| `ga_get_metadata` | List available dimensions and metrics for a property |
| `ga_run_report` | Run a custom Core Reporting API report |
| `ga_overview` | Aggregate users, sessions, views, bounce rate, new users, and revenue |
| `ga_pages` | Rank pages by views |
| `ga_sources` | Rank source/medium traffic |
| `ga_countries` | Geographic breakdown |
| `ga_devices` | Device-category breakdown |
| `ga_daily` | Daily trend |
| `ga_realtime` | Current active users by device category |

All report tools accept a per-call `property_id` override. Relative ranges default to 30 days, and results are capped at 1,000 rows unless `GA4_MAX_LIMIT` is changed.

## CLI examples

```bash
# Discover properties
.venv/bin/python ga_query.py properties --output json

# Common reports
.venv/bin/python ga_query.py overview --days 30
.venv/bin/python ga_query.py pages --days 7 --limit 20 --output csv
.venv/bin/python ga_query.py daily --start-date 2026-01-01 --end-date 2026-01-31

# Metadata and a custom report
.venv/bin/python ga_query.py metadata --property-id 123456789 --output json
.venv/bin/python ga_query.py report \
  --property-id 123456789 \
  --days 7 \
  --dimensions date,country \
  --metrics activeUsers,sessions \
  --limit 100 \
  --output json
```

## Development checks

The tests use fake Google clients and do not make network requests:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q ga_client.py ga_query.py ga_mcp_server.py tests
```

For a live smoke test, use the configured environment and an actual property ID. Google Analytics report values can change after reprocessing, and the API can apply data thresholds; keep the returned metadata with any saved result.

## Official references

- [Google Analytics Data API quickstart](https://developers.google.com/analytics/devguides/reporting/data/v1/quickstart)
- [Create a Data API report](https://developers.google.com/analytics/devguides/reporting/data/v1/basics)
- [Dimensions and metrics](https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema)
- [Admin API account summaries](https://developers.google.com/analytics/devguides/config/admin/v1/rest/v1alpha/accountSummaries/list)
- [Reference project](https://github.com/oreillyjw/ga4-skill-mcp)
