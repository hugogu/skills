from __future__ import annotations

import csv
import io
import json
import unittest

import gsc_query


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


if __name__ == "__main__":
    unittest.main()
