#!/usr/bin/env python3
"""Command-line access to the read-only Google Search Console integration.

Every report returns the same structured data whether you ask for --output
json, table, or csv — json is the canonical shape (and what Claude should
request when it's going to reason over the results rather than show them to you).
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import sys
from dataclasses import replace
from pathlib import Path

import gsc_client
from gsc_client import DEFAULT_AUDIT_LOOKBACK_DAYS, GSCError, Settings


def _parse_csv(value: str | None) -> list[str]:
    return [u.strip() for u in value.split(",") if u.strip()] if value else []


# ============================================================
# Reports — each returns a JSON-serializable dict.
# ============================================================


def report_properties(args: argparse.Namespace, settings: Settings) -> dict:
    return gsc_client.list_sites(settings=settings)


def report_search(args: argparse.Namespace, settings: Settings) -> dict:
    dimensions = _parse_csv(args.dimensions) or ["query"]
    filters = [{"dimension": "page", "operator": "equals", "expression": args.page_url}] if args.page_url else None
    return gsc_client.search_analytics(
        site_url=args.site_url,
        dimensions=dimensions,
        days=args.days,
        start_date=args.start,
        end_date=args.end,
        limit=args.limit,
        filters=filters,
        data_state=args.data_state,
        settings=settings,
    )


def report_pages(args: argparse.Namespace, settings: Settings) -> dict:
    args.dimensions = "page"
    return report_search(args, settings)


def report_page_queries(args: argparse.Namespace, settings: Settings) -> dict:
    args.dimensions = "query"
    return report_search(args, settings)


def report_performance(args: argparse.Namespace, settings: Settings) -> dict:
    return gsc_client.performance_report(
        site_url=args.site_url, days=args.days or 28, start_date=args.start, end_date=args.end,
        data_state=args.data_state, settings=settings,
    )


def report_compare(args: argparse.Namespace, settings: Settings) -> dict:
    return gsc_client.compare_periods(
        site_url=args.site_url, p1_start=args.p1_start, p1_end=args.p1_end,
        p2_start=args.p2_start, p2_end=args.p2_end,
        dimensions=_parse_csv(args.dimensions) or ["query"], limit=args.limit or 20,
        data_state=args.data_state, settings=settings,
    )


def report_sitemaps(args: argparse.Namespace, settings: Settings) -> dict:
    return gsc_client.list_sitemaps(site_url=args.site_url, settings=settings)


def report_inspect(args: argparse.Namespace, settings: Settings) -> dict:
    site_url = gsc_client.resolve_site_url(args.site_url, settings)
    result = gsc_client.inspect_url(site_url=site_url, page_url=args.page_url, settings=settings)
    return {"site_url": site_url, **vars(result)}


def report_indexing(args: argparse.Namespace, settings: Settings) -> dict:
    return gsc_client.check_indexing(site_url=args.site_url, urls=_parse_csv(args.urls), settings=settings)


def report_site_audit(args: argparse.Namespace, settings: Settings) -> dict:
    return gsc_client.run_site_audit(
        site_url=args.site_url, sitemap_url=args.sitemap_url,
        limit=args.limit or gsc_client.DEFAULT_SITEMAP_URL_CAP, lookback_days=args.lookback_days,
        data_state=args.data_state, settings=settings,
    )


REPORTS = {
    "properties": report_properties,
    "search": report_search,
    "pages": report_pages,
    "performance": report_performance,
    "page-queries": report_page_queries,
    "compare": report_compare,
    "sitemaps": report_sitemaps,
    "inspect": report_inspect,
    "indexing": report_indexing,
    "site-audit": report_site_audit,
}


# ============================================================
# Rendering
# ============================================================


def render_table(rows: list[dict]) -> str:
    if not rows:
        return "No data found."
    headers = list(rows[0].keys())
    str_rows = [[_fmt_cell(h, r.get(h)) for h in headers] for r in rows]
    widths = [max(len(h), *(len(v) for v in col)) for h, col in zip(headers, zip(*str_rows))]

    def line(cells):
        return "| " + " | ".join(c.ljust(w) for c, w in zip(cells, widths)) + " |"

    sep = "+-" + "-+-".join("-" * w for w in widths) + "-+"
    out = [sep, line(headers), sep, *(line(r) for r in str_rows), sep, f"\n{len(rows)} row(s)."]
    return "\n".join(out)


def _fmt_cell(header: str, value) -> str:
    if value is None:
        return ""
    if header == "ctr" and isinstance(value, (int, float)):
        return f"{value * 100:.2f}%"
    if header == "position" and isinstance(value, (int, float)):
        return f"{value:.1f}"
    return str(value)


def render_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().strip()


def render_narrative(report: str, data: dict) -> str:
    """Human-readable text for reports whose shape isn't one flat table."""
    if report == "performance":
        t = data["totals"]
        lines = [
            f"Performance for {data['site_url']} ({data['start_date']} to {data['end_date']}):",
            f"  Clicks:      {t['clicks']:,}",
            f"  Impressions: {t['impressions']:,}",
            f"  CTR:         {t['ctr'] * 100:.2f}%",
            f"  Position:    {t['position']:.1f}",
            "",
            render_table(data["daily"]),
        ]
        return "\n".join(lines)

    if report == "inspect":
        lines = [f"URL Inspection: {data['page_url']}", "-" * 60]
        for label, key in [
            ("Verdict", "verdict"), ("Coverage", "coverage_state"), ("Page fetch", "page_fetch_state"),
            ("Robots.txt", "robots_txt_state"), ("Indexing", "indexing_state"),
            ("Google canonical", "google_canonical"), ("User canonical", "user_canonical"),
            ("Last crawled", "last_crawl_time"),
        ]:
            if data.get(key):
                lines.append(f"{label + ':':20s}{data[key]}")
        if data.get("inspection_link"):
            lines.append(f"\nGSC link: {data['inspection_link']}")
        return "\n".join(lines)

    if report in ("indexing", "site-audit"):
        lines = [f"Indexing summary for {data['site_url']}", "-" * 60, f"Checked: {data['checked']}"]
        if report == "site-audit":
            lines.insert(1, f"Sitemap: {data['sitemap_source']} ({data['total_sitemap_urls']} URLs total)")
            lines.append(f"Sitemap URLs with zero clicks/impressions in last {data['lookback_days']}d: {data['zero_impression_count']}")
        lines.append("\nBy coverage state:")
        for state, count in sorted(data["coverage_breakdown"].items(), key=lambda kv: -kv[1]):
            lines.append(f"  {count:4d}  {state}")
        if data.get("stopped_early_reason"):
            lines.append(f"\nStopped early: {data['stopped_early_reason']}")
        return "\n".join(lines)

    return json.dumps(data, indent=2)


TABULAR_REPORTS = {"properties", "search", "pages", "page-queries", "compare", "sitemaps"}


def format_output(report: str, data: dict, output: str) -> str:
    if output == "json":
        return json.dumps(data, indent=2)

    if report in TABULAR_REPORTS:
        rows = data.get("sites") or data.get("rows") or data.get("sitemaps") or []
        return render_csv(rows) if output == "csv" else render_table(rows)

    if output == "csv":
        rows = data.get("daily") or data.get("results") or [data]
        return render_csv(rows)

    return render_narrative(report, data)


# ============================================================
# CLI
# ============================================================


def _add_output(parser: argparse.ArgumentParser, default: str = "table") -> None:
    parser.add_argument("--output", choices=("table", "json", "csv"), default=default)


def _add_site_url(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--site-url", help="GSC property URL; overrides GSC_SITE_URL")


def _add_date_range(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--days", type=int, help="Lookback period in days (default: 28)")
    parser.add_argument("--start", help="Start date YYYY-MM-DD, overrides --days")
    parser.add_argument("--end", help="End date YYYY-MM-DD, defaults to today")
    parser.add_argument("--data-state", choices=("final", "all"), default="final", help="'all' includes fresher, unfinalized data")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query Google Search Console with read-only access.")
    parser.add_argument("--credentials", help="Path to service account JSON; overrides GSC_CREDENTIALS_PATH")
    subparsers = parser.add_subparsers(dest="report", required=True)

    p = subparsers.add_parser("properties", help="List accessible properties")
    _add_output(p)

    for name in ("search", "pages"):
        p = subparsers.add_parser(name, help=f"Run the {name} report")
        _add_site_url(p)
        _add_date_range(p)
        p.add_argument("--limit", type=int, help="Max rows to return (default: 20)")
        p.add_argument("--dimensions", help="Comma-separated dimensions: query,page,device,country,date")
        p.add_argument("--page-url", help="Filter to this exact page URL")
        _add_output(p)

    p = subparsers.add_parser("performance", help="Totals plus a daily trend")
    _add_site_url(p)
    _add_date_range(p)
    _add_output(p)

    p = subparsers.add_parser("page-queries", help="Queries driving traffic to one page")
    _add_site_url(p)
    _add_date_range(p)
    p.add_argument("--limit", type=int)
    p.add_argument("--page-url", required=True)
    _add_output(p)

    p = subparsers.add_parser("compare", help="Compare two date ranges")
    _add_site_url(p)
    p.add_argument("--p1-start", required=True)
    p.add_argument("--p1-end", required=True)
    p.add_argument("--p2-start", required=True)
    p.add_argument("--p2-end", required=True)
    p.add_argument("--dimensions", help="Comma-separated dimensions (default: query)")
    p.add_argument("--limit", type=int)
    p.add_argument("--data-state", choices=("final", "all"), default="final")
    _add_output(p)

    p = subparsers.add_parser("sitemaps", help="List submitted sitemaps")
    _add_site_url(p)
    _add_output(p)

    p = subparsers.add_parser("inspect", help="Full URL Inspection for one URL")
    _add_site_url(p)
    p.add_argument("--page-url", required=True)
    _add_output(p, default="json")

    p = subparsers.add_parser("indexing", help="Batch-check indexing for specific URLs (max 100)")
    _add_site_url(p)
    p.add_argument("--urls", required=True, help="Comma-separated URLs")
    _add_output(p, default="json")

    p = subparsers.add_parser("site-audit", help="Sitemap-driven indexing audit")
    _add_site_url(p)
    p.add_argument("--sitemap-url", help="Explicit sitemap URL (default: first submitted sitemap)")
    p.add_argument("--limit", type=int, help=f"Max URLs to inspect (default: {gsc_client.DEFAULT_SITEMAP_URL_CAP})")
    p.add_argument("--lookback-days", type=int, default=DEFAULT_AUDIT_LOOKBACK_DAYS, help="Window for the zero-impression check (default: 90)")
    p.add_argument("--data-state", choices=("final", "all"), default="final")
    _add_output(p, default="json")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = Settings.from_env()
        if args.credentials:
            settings = replace(settings, credentials_path=Path(args.credentials))
        data = REPORTS[args.report](args, settings)
        print(format_output(args.report, data, args.output))
    except GSCError as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
