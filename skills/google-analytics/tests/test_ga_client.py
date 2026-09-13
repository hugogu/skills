from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import ga_client


class FakeValue:
    def __init__(self, value: str):
        self.value = value


class FakeHeader:
    def __init__(self, name: str, type_: str = ""):
        self.name = name
        self.type_ = type_


class FakeRow:
    def __init__(self, dimensions: list[str], metrics: list[str]):
        self.dimension_values = [FakeValue(value) for value in dimensions]
        self.metric_values = [FakeValue(value) for value in metrics]


class FakeMetadata:
    currency_code = "USD"
    time_zone = "Asia/Shanghai"


class FakeResponse:
    dimension_headers = [FakeHeader("date"), FakeHeader("country")]
    metric_headers = [FakeHeader("activeUsers", "TYPE_INTEGER")]
    rows = [FakeRow(["20260901", "China"], ["42"])]
    row_count = 1
    metadata = FakeMetadata()


class FakeDataClient:
    def __init__(self):
        self.requests: list[dict] = []

    def run_report(self, *, request):
        self.requests.append(request)
        return FakeResponse()


class FakeRealtimeResponse:
    dimension_headers = [FakeHeader("deviceCategory")]
    metric_headers = [FakeHeader("activeUsers", "TYPE_INTEGER")]
    rows = [FakeRow(["desktop"], ["3"])]
    row_count = 1


class FakeRealtimeClient:
    def __init__(self):
        self.request = None

    def run_realtime_report(self, *, request):
        self.request = request
        return FakeRealtimeResponse()


class FakePropertySummary:
    property = "properties/123"
    display_name = "Example site"
    property_type = "PROPERTY_TYPE_ORDINARY"
    can_edit = False


class FakeAccountSummary:
    account = "accounts/456"
    display_name = "Example account"
    property_summaries = [FakePropertySummary()]


class FakeAdminClient:
    def list_account_summaries(self):
        return [FakeAccountSummary()]


class FakeMetadataItem:
    api_name = "customEvent:plan"
    ui_name = "Plan"
    description = "The selected plan"
    category = "Custom"


class FakeMetadataResponse:
    dimensions = [FakeMetadataItem()]
    metrics = [FakeMetadataItem()]


class FakeMetadataClient:
    def __init__(self):
        self.name = None

    def get_metadata(self, *, name):
        self.name = name
        return FakeMetadataResponse()


class GA4ClientTests(unittest.TestCase):
    def test_normalize_property_id(self):
        self.assertEqual(ga_client.normalize_property_id("properties/123"), "123")
        self.assertEqual(ga_client.normalize_property_id(" 456 "), "456")
        with self.assertRaises(ga_client.GA4QueryError):
            ga_client.normalize_property_id("example.com")

    def test_settings_normalize_allowlist_and_default(self):
        with patch.dict(
            os.environ,
            {
                "GA4_PROPERTY_ID": "properties/123",
                "GA4_ALLOWED_PROPERTY_IDS": "123,456",
                "GA4_DEFAULT_DAYS": "14",
            },
            clear=False,
        ):
            settings = ga_client.Settings.from_env()
        self.assertEqual(settings.default_property_id, "123")
        self.assertEqual(settings.allowed_property_ids, frozenset({"123", "456"}))
        self.assertEqual(settings.default_days, 14)

    def test_build_report_request_contains_relative_range_and_filters(self):
        settings = ga_client.Settings(
            credentials_path=None,
            default_property_id=None,
            allowed_property_ids=frozenset({"123"}),
        )
        request = ga_client.build_run_report_request(
            property_id="123",
            dimensions=["date", "country"],
            metrics=["activeUsers"],
            days=7,
            dimension_filter={"filter": {"field_name": "country"}},
            settings=settings,
        )
        self.assertEqual(request["property"], "properties/123")
        self.assertEqual(request["date_ranges"], [{"start_date": "7daysAgo", "end_date": "today"}])
        self.assertEqual(request["dimensions"], [{"name": "date"}, {"name": "country"}])
        self.assertIn("dimension_filter", request)

    def test_run_report_is_end_to_end_with_fake_client(self):
        client = FakeDataClient()
        settings = ga_client.Settings(None, None, frozenset({"123"}))
        result = ga_client.run_report(
            property_id="123",
            dimensions=["date", "country"],
            metrics=["activeUsers"],
            days=1,
            client=client,
            settings=settings,
        )
        self.assertEqual(
            result["rows"],
            [{"date": "20260901", "country": "China", "activeUsers": "42"}],
        )
        self.assertEqual(result["metric_headers"][0]["type"], "TYPE_INTEGER")
        self.assertEqual(client.requests[0]["limit"], 100)

    def test_realtime_report_is_end_to_end_with_fake_client(self):
        client = FakeRealtimeClient()
        settings = ga_client.Settings(None, None, frozenset({"123"}))
        result = ga_client.realtime(property_id="123", client=client, settings=settings)
        self.assertEqual(result["rows"], [{"deviceCategory": "desktop", "activeUsers": "3"}])
        self.assertEqual(client.request["property"], "properties/123")

    def test_list_properties_only_returns_accessible_api_results(self):
        result = ga_client.list_properties(
            client=FakeAdminClient(),
            settings=ga_client.Settings(None, None, frozenset()),
        )
        self.assertEqual(result["property_count"], 1)
        self.assertEqual(result["properties"][0]["property_id"], "123")
        self.assertEqual(result["properties"][0]["account_name"], "Example account")

    def test_metadata_uses_property_resource_name(self):
        client = FakeMetadataClient()
        result = ga_client.get_metadata(
            property_id="123",
            client=client,
            settings=ga_client.Settings(None, None, frozenset({"123"})),
        )
        self.assertEqual(client.name, "properties/123/metadata")
        self.assertEqual(result["dimensions"][0]["api_name"], "customEvent:plan")

    def test_allowlist_rejects_unlisted_property(self):
        settings = ga_client.Settings(None, None, frozenset({"123"}))
        with self.assertRaises(ga_client.GA4ConfigurationError):
            ga_client.resolve_property_id("456", settings)


if __name__ == "__main__":
    unittest.main()
