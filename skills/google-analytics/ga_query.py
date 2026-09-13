#!/usr/bin/env python3
"""Command-line access to the read-only Google Analytics 4 integration."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from io import StringIO
from typing import Any, Callable

import ga_client


def _common_arguments(parser: argparse.ArgumentParser, *, include_limit: bool = True) -> None:
    parser.add_argument("--property-id", help="Numeric GA4 property ID; overrides GA4_PROPERTY_ID")
    date_group = parser.add_mutually_exclusive_group()
    date_group.add_argument("--days", type=int, help="Relative lookback, for example 7")
    date_group.add_argument("--start-date", help="Start date, YYYY-MM-DD or a GA4 relative date")
    parser.add_argument("--end-date", help="End date, required with --start-date")
    if include_limit:
        parser.add_argument("--limit", type=int, help="Maximum rows to return")
    parser.add_argument("--output", choices=("table", "json", "csv"), default="table")


def _parse_names(value: str | None) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()] if value else []


def _parse_json(value: str | None, label: str) -> dict[str, Any] | None:
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON: {exc.msg}") from exc
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object.")
    return parsed


def _date_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    if args.start_date is not None:
        if args.end_date is None:
            raise ValueError("--end-date is required with --start-date")
        return {"start_date": args.start_date, "end_date": args.end_date}
    if args.end_date is not None:
        raise ValueError("--end-date can only be used with --start-date")
    return {"days": args.days}


def _report_kwargs(args: argparse.Namespace) -> dict[str, Any]:
    values = _date_kwargs(args)
    values.update(
        {
            "property_id": args.property_id,
            "limit": args.limit,
        }
    )
    return values


def _render_table(result: dict[str, Any]) -> str:
    rows = result.get("rows")
    if rows is None:
        rows = result.get("properties", [])
    if not rows:
        return "No rows returned."
    headers = list(rows[0].keys())
    widths = {
        header: max(len(header), *(len(str(row.get(header, ""))) for row in rows))
        for header in headers
    }
    line = " | ".join(header.ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    body = [
        " | ".join(str(row.get(header, "")).ljust(widths[header]) for header in headers)
        for row in rows
    ]
    return "\n".join([line, separator, *body])


def _render_csv(result: dict[str, Any]) -> str:
    rows = result.get("rows")
    if rows is None:
        rows = result.get("properties", [])
    if not rows:
        return ""
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def render(result: dict[str, Any], output: str) -> str:
    if output == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    if output == "csv":
        return _render_csv(result)
    return _render_table(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Query Google Analytics 4 with read-only access.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    properties_parser = subparsers.add_parser("properties", help="List accessible properties")
    properties_parser.add_argument("--output", choices=("table", "json", "csv"), default="table")

    metadata_parser = subparsers.add_parser("metadata", help="List property dimensions and metrics")
    metadata_parser.add_argument("--property-id")
    metadata_parser.add_argument("--output", choices=("table", "json", "csv"), default="json")

    for name in ("overview", "pages", "sources", "countries", "devices", "daily"):
        report_parser = subparsers.add_parser(name, help=f"Run the {name} report")
        _common_arguments(report_parser)

    realtime_parser = subparsers.add_parser("realtime", help="Run a realtime active-user report")
    realtime_parser.add_argument("--property-id")
    realtime_parser.add_argument("--limit", type=int)
    realtime_parser.add_argument("--output", choices=("table", "json", "csv"), default="table")

    custom_parser = subparsers.add_parser("report", help="Run a custom Core Reporting API report")
    _common_arguments(custom_parser)
    custom_parser.add_argument(
        "--dimensions", default="", help="Comma-separated dimension API names"
    )
    custom_parser.add_argument("--metrics", required=True, help="Comma-separated metric API names")
    custom_parser.add_argument("--offset", type=int, default=0)
    custom_parser.add_argument("--dimension-filter", help="FilterExpression JSON")
    custom_parser.add_argument("--metric-filter", help="FilterExpression JSON")
    custom_parser.add_argument("--order-by-metric")
    custom_parser.add_argument("--descending", action="store_true")
    return parser


def execute(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "properties":
        return ga_client.list_properties()
    if args.command == "metadata":
        return ga_client.get_metadata(property_id=args.property_id)
    if args.command == "realtime":
        return ga_client.realtime(property_id=args.property_id, limit=args.limit)

    if args.command == "report":
        kwargs = _report_kwargs(args)
        kwargs.update(
            {
                "dimensions": _parse_names(args.dimensions),
                "metrics": _parse_names(args.metrics),
                "offset": args.offset,
                "dimension_filter": _parse_json(args.dimension_filter, "--dimension-filter"),
                "metric_filter": _parse_json(args.metric_filter, "--metric-filter"),
            }
        )
        if args.order_by_metric:
            kwargs["order_by"] = [
                {"metric": {"metric_name": args.order_by_metric}, "desc": args.descending}
            ]
        return ga_client.run_report(**kwargs)

    report_function: Callable[..., dict[str, Any]] = getattr(ga_client, args.command)
    return report_function(**_report_kwargs(args))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = execute(args)
        print(render(result, args.output))
    except (ga_client.GA4Error, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
