from __future__ import annotations

import unittest

import ga_query


class CLIHelperTests(unittest.TestCase):
    def test_custom_report_parser(self):
        args = ga_query.build_parser().parse_args(
            [
                "report",
                "--property-id",
                "123",
                "--days",
                "7",
                "--dimensions",
                "date,country",
                "--metrics",
                "activeUsers,sessions",
                "--output",
                "json",
            ]
        )
        self.assertEqual(args.command, "report")
        self.assertEqual(ga_query._parse_names(args.dimensions), ["date", "country"])
        self.assertEqual(ga_query._parse_names(args.metrics), ["activeUsers", "sessions"])

    def test_table_rendering(self):
        output = ga_query.render({"rows": [{"country": "China", "activeUsers": "42"}]}, "table")
        self.assertIn("country", output)
        self.assertIn("42", output)

    def test_calendar_range_requires_end_date(self):
        args = ga_query.build_parser().parse_args(
            [
                "overview",
                "--start-date",
                "2026-09-01",
            ]
        )
        with self.assertRaises(ValueError):
            ga_query._date_kwargs(args)


if __name__ == "__main__":
    unittest.main()
