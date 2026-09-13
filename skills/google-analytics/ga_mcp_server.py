#!/usr/bin/env python3
"""MCP server exposing read-only Google Analytics 4 tools over stdio."""

from __future__ import annotations

import json
import sys
from typing import Any

import ga_client


def _json_result(value: dict[str, Any]) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


def create_server() -> Any:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise ga_client.GA4ConfigurationError(
            "The MCP dependency is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc

    server = FastMCP("google-analytics")

    @server.tool()
    def ga_list_properties() -> str:
        """List GA4 accounts and properties accessible to the configured identity."""

        return _json_result(ga_client.list_properties())

    @server.tool()
    def ga_get_metadata(property_id: str | None = None) -> str:
        """List available dimension and metric API names for a GA4 property."""

        return _json_result(ga_client.get_metadata(property_id=property_id or ""))

    @server.tool()
    def ga_run_report(
        dimensions: list[str],
        metrics: list[str],
        property_id: str | None = None,
        days: int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        limit: int | None = None,
        offset: int = 0,
        dimension_filter: dict[str, Any] | None = None,
        metric_filter: dict[str, Any] | None = None,
        order_by: list[dict[str, Any]] | None = None,
    ) -> str:
        """Run a custom GA4 Core Reporting API report.

        Use either days or start_date/end_date. Filters use the Google
        Analytics Data API FilterExpression JSON shape.
        """

        return _json_result(
            ga_client.run_report(
                property_id=property_id or "",
                dimensions=dimensions,
                metrics=metrics,
                days=days,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
                dimension_filter=dimension_filter,
                metric_filter=metric_filter,
                order_by=order_by,
            )
        )

    @server.tool()
    def ga_overview(
        days: int | None = None,
        property_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return aggregate users, sessions, page views, bounce rate, new users, and revenue."""

        return _json_result(
            ga_client.overview(
                property_id=property_id or "",
                days=days,
                start_date=start_date,
                end_date=end_date,
            )
        )

    @server.tool()
    def ga_pages(
        days: int | None = None,
        limit: int | None = None,
        property_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return pages ranked by screen views."""

        return _json_result(
            ga_client.pages(
                property_id=property_id or "",
                days=days,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )

    @server.tool()
    def ga_sources(
        days: int | None = None,
        limit: int | None = None,
        property_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return sessions, users, and engaged sessions by source and medium."""

        return _json_result(
            ga_client.sources(
                property_id=property_id or "",
                days=days,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )

    @server.tool()
    def ga_countries(
        days: int | None = None,
        limit: int | None = None,
        property_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return active users and sessions by country."""

        return _json_result(
            ga_client.countries(
                property_id=property_id or "",
                days=days,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        )

    @server.tool()
    def ga_devices(
        days: int | None = None,
        property_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return active users and sessions by device category."""

        return _json_result(
            ga_client.devices(
                property_id=property_id or "",
                days=days,
                start_date=start_date,
                end_date=end_date,
            )
        )

    @server.tool()
    def ga_daily(
        days: int | None = None,
        property_id: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> str:
        """Return the daily users, sessions, views, and revenue trend."""

        return _json_result(
            ga_client.daily(
                property_id=property_id or "",
                days=days,
                start_date=start_date,
                end_date=end_date,
            )
        )

    @server.tool()
    def ga_realtime(
        limit: int | None = None,
        property_id: str | None = None,
    ) -> str:
        """Return current active users grouped by device category."""

        return _json_result(ga_client.realtime(property_id=property_id or "", limit=limit))

    return server


def main() -> int:
    try:
        server = create_server()
        server.run(transport="stdio")
    except ga_client.GA4Error as exc:
        print(f"Google Analytics MCP server error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
