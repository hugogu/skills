#!/usr/bin/env python3
"""MCP server exposing read-only Google Search Console tools over stdio.

Only needed for MCP-native clients (Claude Desktop, Cursor, etc). In Claude
Code, calling gsc_query.py directly is simpler and needs no server process —
see SKILL.md. Every tool below is a thin wrapper around gsc_client, which also
backs the CLI, so both entry points share one implementation.
"""

from __future__ import annotations

import dataclasses
import json
import sys
from typing import Any

import gsc_client
from gsc_client import GSCError


def _json_default(obj: Any) -> Any:
    # gsc_client functions like inspect_url return a dataclass instance directly
    # (the CLI unwraps it with vars() itself) rather than a plain dict; json.dumps
    # doesn't know how to serialize that on its own.
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def _json_result(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False, default=_json_default)


def _run(fn, *args, **kwargs) -> str:
    try:
        return _json_result(fn(*args, **kwargs))
    except GSCError as err:
        return _json_result({"error": str(err)})


def create_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise GSCError(
            "The MCP dependency is not installed. Run: python3 -m pip install -r requirements.txt"
        ) from exc

    server = FastMCP("gsc-seo-audit")

    @server.tool()
    def gsc_properties() -> str:
        """List Search Console properties the configured credential can access."""
        return _run(gsc_client.list_sites)

    @server.tool()
    def gsc_search(
        dimensions: str = "query",
        days: int = 28,
        limit: int = 20,
        site_url: str | None = None,
        page_url: str | None = None,
    ) -> str:
        """Top rows by clicks for the given dimensions (query, page, device, country, date),
        with impressions, CTR, and position. Pass page_url to filter to one exact page."""
        filters = [{"dimension": "page", "operator": "equals", "expression": page_url}] if page_url else None
        return _run(
            gsc_client.search_analytics,
            site_url=site_url, dimensions=[d.strip() for d in dimensions.split(",")],
            days=days, limit=limit, filters=filters,
        )

    @server.tool()
    def gsc_performance(days: int = 28, site_url: str | None = None) -> str:
        """Performance overview: totals plus a daily trend, for spotting drops or spikes."""
        return _run(gsc_client.performance_report, site_url=site_url, days=days)

    @server.tool()
    def gsc_page_queries(page_url: str, days: int = 28, limit: int = 20, site_url: str | None = None) -> str:
        """Queries that drive traffic to one specific page URL."""
        return _run(
            gsc_client.search_analytics,
            site_url=site_url, dimensions=["query"], days=days, limit=limit,
            filters=[{"dimension": "page", "operator": "equals", "expression": page_url}],
        )

    @server.tool()
    def gsc_compare(
        p1_start: str, p1_end: str, p2_start: str, p2_end: str,
        dimensions: str = "query", limit: int = 20, site_url: str | None = None,
    ) -> str:
        """Compare search performance between two date ranges (YYYY-MM-DD), sorted by biggest change."""
        return _run(
            gsc_client.compare_periods,
            site_url=site_url, p1_start=p1_start, p1_end=p1_end, p2_start=p2_start, p2_end=p2_end,
            dimensions=[d.strip() for d in dimensions.split(",")], limit=limit,
        )

    @server.tool()
    def gsc_sitemaps(site_url: str | None = None) -> str:
        """List submitted sitemaps with status, submitted/indexed URL counts, and errors."""
        return _run(gsc_client.list_sitemaps, site_url=site_url)

    @server.tool()
    def gsc_inspect(page_url: str, site_url: str | None = None) -> str:
        """Full URL Inspection for one URL: indexing verdict, coverage state, canonical, rich results."""
        try:
            settings = gsc_client.Settings.from_env()
            resolved_site = gsc_client.resolve_site_url(site_url, settings)
            result = gsc_client.inspect_url(site_url=resolved_site, page_url=page_url, settings=settings)
        except GSCError as err:
            return _json_result({"error": str(err)})
        return _json_result({"site_url": resolved_site, **dataclasses.asdict(result)})

    @server.tool()
    def gsc_indexing(urls: str, site_url: str | None = None) -> str:
        """Batch-check indexing status for specific URLs (comma-separated, max 100 per call)."""
        return _run(gsc_client.check_indexing, site_url=site_url, urls=[u.strip() for u in urls.split(",") if u.strip()])

    @server.tool()
    def gsc_site_audit(
        limit: int = gsc_client.DEFAULT_SITEMAP_URL_CAP,
        lookback_days: int = gsc_client.DEFAULT_AUDIT_LOOKBACK_DAYS,
        sitemap_url: str | None = None,
        site_url: str | None = None,
    ) -> str:
        """Sitemap-driven indexing audit: samples the sitemap, prioritizes URLs with zero search
        traffic in the lookback window for real URL Inspection, and returns a coverage-state
        breakdown. This is the tool for "what's wrong with my indexing" rather than one-off checks."""
        return _run(
            gsc_client.run_site_audit,
            site_url=site_url, sitemap_url=sitemap_url, limit=limit, lookback_days=lookback_days,
        )

    return server


def main() -> int:
    try:
        server = create_server()
        server.run(transport="stdio")
    except GSCError as exc:
        print(f"Google Search Console MCP server error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
