from __future__ import annotations

import gzip
import json
import os
import unittest
from unittest.mock import patch

import gsc_client


def make_http_error(status: int, reason: str | None = None, message: str = "error"):
    import httplib2
    from googleapiclient.errors import HttpError

    resp = httplib2.Response({"status": status})
    body = {"error": {"code": status, "message": message}}
    if reason:
        body["error"]["errors"] = [{"reason": reason, "message": message}]
    return HttpError(resp, json.dumps(body).encode("utf-8"))


class FakeService:
    """Duck-types the googleapiclient Resource chain far enough for these tests."""

    def __init__(self):
        self.sites_response = {"siteEntry": []}
        self.search_response = {"rows": []}
        self.sitemaps_response = {"sitemap": []}
        self.inspect_response = {}
        self.inspect_error: Exception | None = None
        self.inspect_calls: list[str] = []

    def sites(self):
        return _Chain(list=lambda: _Executable(self.sites_response))

    def searchanalytics(self):
        return _Chain(query=lambda siteUrl, body: _Executable(self.search_response))

    def sitemaps(self):
        return _Chain(list=lambda siteUrl: _Executable(self.sitemaps_response))

    def urlInspection(self):
        outer = self

        class _Index:
            def inspect(self, body):
                outer.inspect_calls.append(body["inspectionUrl"])
                if outer.inspect_error is not None:
                    raise outer.inspect_error
                return _Executable(outer.inspect_response)

        return _Chain(index=lambda: _Index())


class _Chain:
    def __init__(self, **methods):
        for name, fn in methods.items():
            setattr(self, name, fn)


class _Executable:
    def __init__(self, result):
        self._result = result

    def execute(self):
        return self._result


class SettingsTests(unittest.TestCase):
    def test_from_env_parses_allowlist_and_limit(self):
        with patch.dict(
            os.environ,
            {
                "GSC_SITE_URL": "sc-domain:example.com",
                "GSC_ALLOWED_SITE_URLS": "sc-domain:example.com,sc-domain:other.com",
                "GSC_MAX_LIMIT": "50",
            },
            clear=False,
        ):
            settings = gsc_client.Settings.from_env()
        self.assertEqual(settings.default_site_url, "sc-domain:example.com")
        self.assertEqual(
            settings.allowed_site_urls, frozenset({"sc-domain:example.com", "sc-domain:other.com"})
        )
        self.assertEqual(settings.max_limit, 50)

    def test_resolve_site_url_falls_back_to_default(self):
        settings = gsc_client.Settings(None, "sc-domain:example.com")
        self.assertEqual(gsc_client.resolve_site_url(None, settings), "sc-domain:example.com")
        self.assertEqual(gsc_client.resolve_site_url("sc-domain:other.com", settings), "sc-domain:other.com")

    def test_resolve_site_url_raises_when_nothing_given(self):
        settings = gsc_client.Settings(None, None)
        with self.assertRaises(gsc_client.GSCConfigurationError):
            gsc_client.resolve_site_url(None, settings)

    def test_allowlist_rejects_unlisted_site(self):
        settings = gsc_client.Settings(None, None, frozenset({"sc-domain:example.com"}))
        with self.assertRaises(gsc_client.GSCConfigurationError):
            gsc_client.resolve_site_url("sc-domain:other.com", settings)

    def test_validate_limit_rejects_over_max(self):
        settings = gsc_client.Settings(None, None, max_limit=100)
        with self.assertRaises(gsc_client.GSCQueryError):
            gsc_client.validate_limit(500, settings)

    def test_validate_limit_rejects_bool(self):
        settings = gsc_client.Settings(None, None)
        with self.assertRaises(gsc_client.GSCQueryError):
            gsc_client.validate_limit(True, settings)


class EvenSampleTests(unittest.TestCase):
    def test_returns_all_when_under_cap(self):
        self.assertEqual(gsc_client.even_sample([1, 2, 3], 5), [1, 2, 3])

    def test_spreads_across_full_range(self):
        sampled = gsc_client.even_sample(list(range(100)), 10)
        self.assertEqual(len(sampled), 10)
        self.assertEqual(sampled[0], 0)
        self.assertGreaterEqual(sampled[-1], 90)

    def test_empty_or_zero(self):
        self.assertEqual(gsc_client.even_sample([], 5), [])
        self.assertEqual(gsc_client.even_sample([1, 2, 3], 0), [])


class DateRangeTests(unittest.TestCase):
    def test_explicit_start_end_overrides_days(self):
        start, end = gsc_client.default_date_range(28, end="2026-06-30", start="2026-06-01")
        self.assertEqual((start, end), ("2026-06-01", "2026-06-30"))

    def test_days_computes_start_from_end(self):
        start, end = gsc_client.default_date_range(7, end="2026-06-30")
        self.assertEqual((start, end), ("2026-06-23", "2026-06-30"))

    def test_malformed_end_raises_gscqueryerror_not_valueerror(self):
        with self.assertRaisesRegex(gsc_client.GSCQueryError, "YYYY-MM-DD"):
            gsc_client.default_date_range(7, end="not-a-date")

    def test_malformed_start_raises_gscqueryerror_not_valueerror(self):
        with self.assertRaisesRegex(gsc_client.GSCQueryError, "YYYY-MM-DD"):
            gsc_client.default_date_range(7, end="2026-06-30", start="06/01/2026")

    def test_negative_days_raises_gscqueryerror(self):
        with self.assertRaises(gsc_client.GSCQueryError):
            gsc_client.default_date_range(-7, end="2026-06-30")


class HttpErrorWrappingTests(unittest.TestCase):
    def test_403_mentions_full_user(self):
        err = gsc_client._wrap_http_error(make_http_error(403, reason="forbidden"), "Listing sitemaps")
        self.assertIsInstance(err, gsc_client.GSCConfigurationError)
        self.assertIn("Full", str(err))

    def test_404_mentions_site_url_format(self):
        err = gsc_client._wrap_http_error(make_http_error(404), "Listing sitemaps")
        self.assertIn("sc-domain:", str(err))

    def test_quota_by_status_code(self):
        err = gsc_client._wrap_http_error(make_http_error(429), "Inspecting url")
        self.assertIn("quota", str(err).lower())

    def test_quota_by_reason_string(self):
        err = gsc_client._wrap_http_error(make_http_error(400, reason="quotaExceeded"), "Inspecting url")
        self.assertIn("quota", str(err).lower())


class ServiceConstructionTests(unittest.TestCase):
    def test_create_service_raises_without_credentials_path(self):
        settings = gsc_client.Settings(credentials_path=None, default_site_url=None)
        with self.assertRaisesRegex(gsc_client.GSCConfigurationError, "No credentials"):
            gsc_client.create_service(settings)

    def test_create_service_raises_when_file_missing(self):
        from pathlib import Path

        settings = gsc_client.Settings(credentials_path=Path("/nonexistent/creds.json"), default_site_url=None)
        with self.assertRaisesRegex(gsc_client.GSCConfigurationError, "not found"):
            gsc_client.create_service(settings)


class SearchAnalyticsTests(unittest.TestCase):
    def test_maps_rows_into_flat_records(self):
        service = FakeService()
        service.search_response = {
            "rows": [{"keys": ["hello world"], "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.5}]
        }
        settings = gsc_client.Settings(None, "sc-domain:example.com")
        result = gsc_client.search_analytics(
            site_url=None, dimensions=["query"], service=service, settings=settings
        )
        self.assertEqual(
            result["rows"],
            [{"query": "hello world", "clicks": 10, "impressions": 100, "ctr": 0.1, "position": 3.5}],
        )

    def test_rejects_limit_over_max(self):
        service = FakeService()
        settings = gsc_client.Settings(None, "sc-domain:example.com", max_limit=10)
        with self.assertRaises(gsc_client.GSCQueryError):
            gsc_client.search_analytics(
                site_url=None, dimensions=["query"], limit=999, service=service, settings=settings
            )


class ListSitesTests(unittest.TestCase):
    def test_returns_entries(self):
        service = FakeService()
        service.sites_response = {
            "siteEntry": [{"siteUrl": "sc-domain:example.com", "permissionLevel": "siteFullUser"}]
        }
        result = gsc_client.list_sites(service=service, settings=gsc_client.Settings(None, None))
        self.assertEqual(result["sites"][0]["site_url"], "sc-domain:example.com")

    def test_filters_by_allowlist(self):
        service = FakeService()
        service.sites_response = {
            "siteEntry": [
                {"siteUrl": "sc-domain:allowed.com", "permissionLevel": "siteFullUser"},
                {"siteUrl": "sc-domain:hidden.com", "permissionLevel": "siteFullUser"},
            ]
        }
        settings = gsc_client.Settings(None, None, frozenset({"sc-domain:allowed.com"}))
        result = gsc_client.list_sites(service=service, settings=settings)
        self.assertEqual([s["site_url"] for s in result["sites"]], ["sc-domain:allowed.com"])


class InspectUrlTests(unittest.TestCase):
    def test_maps_nested_response(self):
        service = FakeService()
        service.inspect_response = {
            "inspectionResult": {
                "inspectionResultLink": "https://search.google.com/...",
                "indexStatusResult": {
                    "verdict": "PASS",
                    "coverageState": "Submitted and indexed",
                    "referringUrls": ["https://example.com/b"],
                },
                "richResultsResult": {"verdict": "PASS", "detectedItems": [{"richResultType": "FAQ"}]},
            }
        }
        result = gsc_client.inspect_url(
            site_url="sc-domain:example.com", page_url="https://example.com/a",
            service=service, settings=gsc_client.Settings(None, None),
        )
        self.assertEqual(result.verdict, "PASS")
        self.assertEqual(result.coverage_state, "Submitted and indexed")
        self.assertEqual(result.rich_result_types, ["FAQ"])
        self.assertEqual(result.error, "")

    def test_handles_missing_inspection_result(self):
        service = FakeService()
        result = gsc_client.inspect_url(
            site_url="sc-domain:example.com", page_url="https://example.com/a",
            service=service, settings=gsc_client.Settings(None, None),
        )
        self.assertEqual(result.verdict, "UNKNOWN")
        self.assertEqual(result.coverage_state, "Unknown")


class BatchInspectTests(unittest.TestCase):
    def test_stops_early_on_quota_error(self):
        service = FakeService()
        service.inspect_error = make_http_error(429)
        results, stopped = gsc_client.batch_inspect(
            site_url="sc-domain:example.com", urls=["a", "b", "c"], pace_seconds=0,
            service=service, settings=gsc_client.Settings(None, None),
        )
        self.assertEqual(len(results), 0)
        self.assertIsNotNone(stopped)
        self.assertIn("quota", stopped.lower())

    def test_continues_past_single_url_error(self):
        def fake_inspect(*, site_url, page_url, service=None, settings=None):
            if page_url == "bad":
                raise gsc_client.GSCQueryError("Inspecting bad: 500 server error")
            return gsc_client.InspectionResult(page_url=page_url, verdict="PASS")

        with patch.object(gsc_client, "inspect_url", side_effect=fake_inspect):
            results, stopped = gsc_client.batch_inspect(
                site_url="sc-domain:example.com", urls=["good1", "bad", "good2"], pace_seconds=0,
                service=FakeService(), settings=gsc_client.Settings(None, None),
            )

        self.assertIsNone(stopped)
        self.assertEqual(len(results), 3)
        self.assertNotEqual(results[1].error, "")
        self.assertEqual(results[0].verdict, "PASS")


class PerformanceReportTests(unittest.TestCase):
    def test_combines_totals_and_daily_trend(self):
        service = FakeService()
        responses = iter(
            [
                {"rows": [{"keys": [], "clicks": 100, "impressions": 1000, "ctr": 0.1, "position": 5.0}]},
                {
                    "rows": [
                        {"keys": ["2026-06-02"], "clicks": 40, "impressions": 400, "ctr": 0.1, "position": 5.0},
                        {"keys": ["2026-06-01"], "clicks": 60, "impressions": 600, "ctr": 0.1, "position": 5.0},
                    ]
                },
            ]
        )
        service.searchanalytics = lambda: _Chain(query=lambda siteUrl, body: _Executable(next(responses)))
        result = gsc_client.performance_report(
            site_url="sc-domain:example.com", start_date="2026-06-01", end_date="2026-06-02",
            service=service, settings=gsc_client.Settings(None, None),
        )
        self.assertEqual(result["totals"]["clicks"], 100)
        self.assertEqual([d["date"] for d in result["daily"]], ["2026-06-01", "2026-06-02"])


class ComparePeriodsTests(unittest.TestCase):
    def test_respects_max_limit_below_the_1000_default(self):
        service = FakeService()
        seen_row_limits = []

        def fake_query(siteUrl, body):
            seen_row_limits.append(body["rowLimit"])
            return _Executable({"rows": []})

        service.searchanalytics = lambda: _Chain(query=fake_query)

        # Previously this hard-coded limit=1000 for the internal fetch, which made
        # validate_limit raise as soon as GSC_MAX_LIMIT was configured below 1000.
        result = gsc_client.compare_periods(
            site_url="sc-domain:example.com", p1_start="2026-01-01", p1_end="2026-01-31",
            p2_start="2026-02-01", p2_end="2026-02-28", service=service,
            settings=gsc_client.Settings(None, None, max_limit=50),
        )

        self.assertEqual(seen_row_limits, [50, 50])
        self.assertEqual(result["rows"], [])


class CheckIndexingTests(unittest.TestCase):
    def test_rejects_too_many_urls(self):
        with self.assertRaisesRegex(gsc_client.GSCQueryError, "max"):
            gsc_client.check_indexing(
                site_url="sc-domain:example.com",
                urls=[f"https://x.com/{i}" for i in range(gsc_client.MAX_BATCH_URLS + 1)],
                settings=gsc_client.Settings(None, None),
            )


class RunSiteAuditTests(unittest.TestCase):
    def test_requires_sitemap_when_none_submitted(self):
        service = FakeService()
        service.sitemaps_response = {"sitemap": []}
        with self.assertRaisesRegex(gsc_client.GSCQueryError, "No sitemaps"):
            gsc_client.run_site_audit(
                site_url="sc-domain:example.com", service=service, settings=gsc_client.Settings(None, None)
            )

    def test_prioritizes_zero_impression_urls(self):
        service = FakeService()
        service.sitemaps_response = {"sitemap": [{"path": "https://example.com/sitemap.xml"}]}
        service.search_response = {
            "rows": [
                {"keys": [f"https://example.com/{i}"], "clicks": 1, "impressions": 10, "ctr": 0.1, "position": 5.0}
                for i in range(5)
            ]
        }
        all_urls = [f"https://example.com/{i}" for i in range(10)]

        with (
            patch.object(gsc_client, "fetch_sitemap_urls", return_value=(all_urls, 10)),
            patch.object(gsc_client, "batch_inspect") as fake_batch,
        ):
            fake_batch.side_effect = lambda *, site_url, urls, **kw: (
                [gsc_client.InspectionResult(page_url=u, verdict="PASS", coverage_state="Submitted and indexed") for u in urls],
                None,
            )
            result = gsc_client.run_site_audit(
                site_url="sc-domain:example.com", limit=3, service=service, settings=gsc_client.Settings(None, None)
            )

        self.assertEqual(result["zero_impression_count"], 5)
        inspected = {r["page_url"] for r in result["results"]}
        self.assertTrue(inspected <= {f"https://example.com/{i}" for i in range(5, 10)})
        self.assertEqual(len(inspected), 3)


class FakeHttpResponse:
    def __init__(self, data: bytes):
        self._data = data

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


URLSET_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/a</loc></url>
  <url><loc>https://example.com/b</loc></url>
</urlset>"""

INDEX_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/sitemap-a.xml</loc></sitemap>
  <sitemap><loc>https://example.com/sitemap-b.xml</loc></sitemap>
</sitemapindex>"""

CHILD_A_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/from-a-1</loc></url>
</urlset>"""

CHILD_B_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/from-b-1</loc></url>
</urlset>"""


class SitemapParsingTests(unittest.TestCase):
    def test_simple_urlset(self):
        with patch("urllib.request.urlopen", return_value=FakeHttpResponse(URLSET_XML)):
            urls, total = gsc_client.fetch_sitemap_urls("https://example.com/sitemap.xml", cap=25)
        self.assertEqual(total, 2)
        self.assertEqual(urls, ["https://example.com/a", "https://example.com/b"])

    def test_gzip(self):
        gz = gzip.compress(URLSET_XML)
        with patch("urllib.request.urlopen", return_value=FakeHttpResponse(gz)):
            _urls, total = gsc_client.fetch_sitemap_urls("https://example.com/sitemap.xml.gz", cap=25)
        self.assertEqual(total, 2)

    def test_recurses_into_sitemap_index(self):
        responses = {
            "https://example.com/sitemap-index.xml": FakeHttpResponse(INDEX_XML),
            "https://example.com/sitemap-a.xml": FakeHttpResponse(CHILD_A_XML),
            "https://example.com/sitemap-b.xml": FakeHttpResponse(CHILD_B_XML),
        }

        def fake_urlopen(req, timeout=20):
            return responses[req.full_url]

        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            urls, total = gsc_client.fetch_sitemap_urls("https://example.com/sitemap-index.xml", cap=25)

        self.assertEqual(total, 2)
        self.assertEqual(set(urls), {"https://example.com/from-a-1", "https://example.com/from-b-1"})

    def test_samples_when_over_cap(self):
        big_urlset = (
            b"<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"
            + b"".join(f"<url><loc>https://example.com/{i}</loc></url>".encode() for i in range(1000))
            + b"</urlset>"
        )
        with patch("urllib.request.urlopen", return_value=FakeHttpResponse(big_urlset)):
            urls, total = gsc_client.fetch_sitemap_urls("https://example.com/sitemap.xml", cap=10)
        self.assertEqual(total, 1000)
        self.assertEqual(len(urls), 10)

    def test_bad_xml_raises_gscqueryerror(self):
        with (
            patch("urllib.request.urlopen", return_value=FakeHttpResponse(b"not xml")),
            self.assertRaisesRegex(gsc_client.GSCQueryError, "parse"),
        ):
            gsc_client.fetch_sitemap_urls("https://example.com/sitemap.xml", cap=25)


if __name__ == "__main__":
    unittest.main()
