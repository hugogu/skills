from __future__ import annotations

import contextlib
import csv
import io
import json
import os
import unittest
from unittest.mock import patch

import gsc_client
import gsc_query


class OmitNoneTests(unittest.TestCase):
    def test_drops_only_none_values(self):
        self.assertEqual(gsc_query._omit_none(days=0, limit=None, x="y"), {"days": 0, "x": "y"})

    def test_explicit_zero_survives_into_report_performance_call(self):
        # args.days or 28 used to turn an explicit --days 0 into 28, since 0 is falsy.
        args = gsc_query.build_parser().parse_args(["performance", "--days", "0"])
        with patch.object(gsc_client, "performance_report", return_value={}) as fake:
            gsc_query.report_performance(args, gsc_client.Settings(None, None))
        self.assertEqual(fake.call_args.kwargs["days"], 0)

    def test_explicit_zero_survives_into_site_audit_limit(self):
        args = gsc_query.build_parser().parse_args(["site-audit", "--limit", "0"])
        with patch.object(gsc_client, "run_site_audit", return_value={}) as fake:
            gsc_query.report_site_audit(args, gsc_client.Settings(None, None))
        self.assertEqual(fake.call_args.kwargs["limit"], 0)


class ParserTests(unittest.TestCase):
    def test_search_subcommand_parses_dimensions_and_output(self):
        args = gsc_query.build_parser().parse_args(
            ["search", "--dimensions", "query,page", "--days", "7", "--output", "json"]
        )
        self.assertEqual(args.report, "search")
        self.assertEqual(gsc_query._parse_csv(args.dimensions), ["query", "page"])
        self.assertEqual(args.days, 7)

    def test_page_queries_requires_page_url_flag_at_parse_time(self):
        with self.assertRaises(SystemExit):
            gsc_query.build_parser().parse_args(["page-queries"])

    def test_compare_requires_all_four_dates_at_parse_time(self):
        with self.assertRaises(SystemExit):
            gsc_query.build_parser().parse_args(["compare", "--p1-start", "2026-01-01"])

    def test_inspect_defaults_to_json_output(self):
        args = gsc_query.build_parser().parse_args(["inspect", "--page-url", "https://example.com/"])
        self.assertEqual(args.output, "json")


class RenderingTests(unittest.TestCase):
    def test_render_table_formats_ctr_and_position(self):
        rows = [{"query": "cats", "clicks": 5, "impressions": 50, "ctr": 0.1, "position": 4.2}]
        table = gsc_query.render_table(rows)
        self.assertIn("10.00%", table)
        self.assertIn("4.2", table)
        self.assertIn("1 row(s).", table)

    def test_render_table_empty(self):
        self.assertEqual(gsc_query.render_table([]), "No data found.")

    def test_render_csv_round_trips(self):
        rows = [{"query": "cats", "clicks": 5}, {"query": "dogs", "clicks": 3}]
        parsed = list(csv.DictReader(io.StringIO(gsc_query.render_csv(rows))))
        self.assertEqual(parsed, [{"query": "cats", "clicks": "5"}, {"query": "dogs", "clicks": "3"}])

    def test_format_output_json_is_canonical_for_any_report(self):
        data = {"site_url": "sc-domain:example.com", "rows": [{"query": "cats", "clicks": 1}]}
        self.assertEqual(json.loads(gsc_query.format_output("search", data, "json")), data)

    def test_format_output_table_for_tabular_report(self):
        data = {"sites": [{"site_url": "sc-domain:example.com", "permission_level": "siteFullUser"}]}
        self.assertIn("siteFullUser", gsc_query.format_output("properties", data, "table"))

    def test_format_output_narrative_for_performance(self):
        data = {
            "site_url": "sc-domain:example.com", "start_date": "2026-01-01", "end_date": "2026-01-28",
            "totals": {"clicks": 100, "impressions": 1000, "ctr": 0.1, "position": 5.0}, "daily": [],
        }
        out = gsc_query.format_output("performance", data, "table")
        self.assertIn("Clicks:", out)
        self.assertIn("100", out)


class MainEntryPointTests(unittest.TestCase):
    def test_invalid_env_settings_produce_clean_error_not_a_traceback(self):
        # Settings.from_env() used to run before the try/except in main(), so a bad
        # GSC_MAX_LIMIT raised GSCConfigurationError uncaught instead of a clean exit.
        with patch.dict(os.environ, {"GSC_MAX_LIMIT": "not-a-number"}, clear=False):
            stderr = io.StringIO()
            with contextlib.redirect_stderr(stderr):
                exit_code = gsc_query.main(["properties"])
        self.assertEqual(exit_code, 1)
        self.assertIn("Error:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
