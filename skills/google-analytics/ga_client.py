"""Read-only Google Analytics 4 Data/Admin API helpers.

Google client libraries are imported lazily so validation and offline tests can
run without installing credentials or Google dependencies.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


READONLY_SCOPES = ("https://www.googleapis.com/auth/analytics.readonly",)
PROPERTY_ID_RE = re.compile(r"^(?:properties/)?([0-9]+)$")
API_NAME_RE = re.compile(r"^[^\s,]+$")


class GA4Error(RuntimeError):
    """Base class for errors that can be shown safely to the user."""


class GA4ConfigurationError(GA4Error):
    """Raised when local configuration is incomplete or invalid."""


class GA4QueryError(GA4Error):
    """Raised when a report request cannot be built safely."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings read from environment variables."""

    credentials_path: Path | None
    default_property_id: str | None
    allowed_property_ids: frozenset[str]
    default_days: int = 30
    max_days: int = 3650
    max_limit: int = 1000

    @classmethod
    def from_env(cls) -> "Settings":
        credentials_value = os.getenv("GA4_CREDENTIALS_PATH", "").strip()
        default_property = os.getenv("GA4_PROPERTY_ID", "").strip() or None
        allowed_value = os.getenv("GA4_ALLOWED_PROPERTY_IDS", "")
        allowed = frozenset(
            normalize_property_id(value.strip())
            for value in allowed_value.split(",")
            if value.strip()
        )
        default_days = _positive_env_int("GA4_DEFAULT_DAYS", 30)
        max_days = _positive_env_int("GA4_MAX_DAYS", 3650)
        max_limit = _positive_env_int("GA4_MAX_LIMIT", 1000)
        if default_days > max_days:
            raise GA4ConfigurationError(
                "GA4_DEFAULT_DAYS cannot be greater than GA4_MAX_DAYS."
            )
        return cls(
            credentials_path=Path(credentials_value) if credentials_value else None,
            default_property_id=(
                normalize_property_id(default_property) if default_property else None
            ),
            allowed_property_ids=allowed,
            default_days=default_days,
            max_days=max_days,
            max_limit=max_limit,
        )


def _positive_env_int(name: str, fallback: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return fallback
    try:
        parsed = int(value)
    except ValueError as exc:
        raise GA4ConfigurationError(f"{name} must be a positive integer.") from exc
    if parsed < 1:
        raise GA4ConfigurationError(f"{name} must be a positive integer.")
    return parsed


def normalize_property_id(value: str) -> str:
    """Return a numeric property ID from ``123`` or ``properties/123``."""

    match = PROPERTY_ID_RE.fullmatch(value.strip())
    if not match:
        raise GA4QueryError(
            "GA4 property_id must be a numeric ID such as '123456789' "
            "or 'properties/123456789'."
        )
    return match.group(1)


def resolve_property_id(property_id: str | None, settings: Settings | None = None) -> str:
    settings = settings or Settings.from_env()
    candidate = property_id.strip() if property_id else settings.default_property_id
    if not candidate:
        raise GA4ConfigurationError(
            "No GA4 property was selected. Call ga_list_properties or set "
            "GA4_PROPERTY_ID, then pass property_id for the requested property."
        )
    normalized = normalize_property_id(candidate)
    if settings.allowed_property_ids and normalized not in settings.allowed_property_ids:
        raise GA4ConfigurationError(
            f"Property {normalized} is not in GA4_ALLOWED_PROPERTY_IDS."
        )
    return normalized


def _validate_days(days: int | None, settings: Settings) -> int:
    value = settings.default_days if days is None else days
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GA4QueryError("days must be a positive integer.")
    if value > settings.max_days:
        raise GA4QueryError(f"days cannot exceed the configured limit of {settings.max_days}.")
    return value


def _validate_limit(limit: int | None, settings: Settings, fallback: int = 100) -> int:
    value = fallback if limit is None else limit
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GA4QueryError("limit must be a positive integer.")
    if value > settings.max_limit:
        raise GA4QueryError(f"limit cannot exceed the configured limit of {settings.max_limit}.")
    return value


def _validate_offset(offset: int) -> int:
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise GA4QueryError("offset must be a non-negative integer.")
    return offset


def _validate_names(values: Sequence[str] | None, label: str, maximum: int) -> list[str]:
    normalized = [value.strip() for value in (values or [])]
    if any(not value or not API_NAME_RE.fullmatch(value) for value in normalized):
        raise GA4QueryError(f"{label} must contain non-empty API names without whitespace.")
    if len(normalized) > maximum:
        raise GA4QueryError(f"A report supports at most {maximum} {label}.")
    if len(set(normalized)) != len(normalized):
        raise GA4QueryError(f"{label} must not contain duplicates.")
    return normalized


def _date_range(
    *,
    days: int | None,
    start_date: str | None,
    end_date: str | None,
    settings: Settings,
) -> dict[str, str]:
    if (start_date is None) != (end_date is None):
        raise GA4QueryError("start_date and end_date must be provided together.")
    if start_date is not None and end_date is not None:
        start = start_date.strip()
        end = end_date.strip()
        if not start or not end:
            raise GA4QueryError("start_date and end_date cannot be empty.")
        return {"start_date": start, "end_date": end}
    lookback = _validate_days(days, settings)
    return {"start_date": f"{lookback}daysAgo", "end_date": "today"}


def _validated_filter(value: Mapping[str, Any] | None, label: str) -> dict[str, Any] | None:
    if value is None:
        return None
    if not isinstance(value, Mapping) or not value:
        raise GA4QueryError(f"{label} must be a non-empty FilterExpression object.")
    return dict(value)


def build_run_report_request(
    *,
    property_id: str,
    dimensions: Sequence[str],
    metrics: Sequence[str],
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    dimension_filter: Mapping[str, Any] | None = None,
    metric_filter: Mapping[str, Any] | None = None,
    order_by: Sequence[Mapping[str, Any]] | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    normalized_property = resolve_property_id(property_id, settings)
    normalized_dimensions = _validate_names(dimensions, "dimensions", 8)
    normalized_metrics = _validate_names(metrics, "metrics", 10)
    if not normalized_metrics:
        raise GA4QueryError("metrics must contain at least one API name.")
    request: dict[str, Any] = {
        "property": f"properties/{normalized_property}",
        "date_ranges": [
            _date_range(
                days=days,
                start_date=start_date,
                end_date=end_date,
                settings=settings,
            )
        ],
        "dimensions": [{"name": name} for name in normalized_dimensions],
        "metrics": [{"name": name} for name in normalized_metrics],
        "limit": _validate_limit(limit, settings),
        "offset": _validate_offset(offset),
    }
    dimension_expression = _validated_filter(dimension_filter, "dimension_filter")
    metric_expression = _validated_filter(metric_filter, "metric_filter")
    if dimension_expression is not None:
        request["dimension_filter"] = dimension_expression
    if metric_expression is not None:
        request["metric_filter"] = metric_expression
    if order_by is not None:
        if not isinstance(order_by, Sequence) or isinstance(order_by, (str, bytes)):
            raise GA4QueryError("order_by must be a list of Google Analytics OrderBy objects.")
        if any(not isinstance(item, Mapping) or not item for item in order_by):
            raise GA4QueryError("order_by must contain non-empty JSON objects.")
        request["order_bys"] = [dict(item) for item in order_by]
    return request


def _load_credentials(settings: Settings) -> Any | None:
    if settings.credentials_path is None:
        return None
    if not settings.credentials_path.is_file():
        raise GA4ConfigurationError(
            f"GA4_CREDENTIALS_PATH does not point to a file: {settings.credentials_path}"
        )
    try:
        from google.oauth2 import service_account
    except ImportError as exc:
        raise GA4ConfigurationError(
            "Google dependencies are not installed. Run: python -m pip install -r requirements.txt"
        ) from exc
    return service_account.Credentials.from_service_account_file(
        str(settings.credentials_path), scopes=list(READONLY_SCOPES)
    )


def create_data_client(settings: Settings | None = None) -> Any:
    settings = settings or Settings.from_env()
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
    except ImportError as exc:
        raise GA4ConfigurationError(
            "google-analytics-data is not installed. Run: python -m pip install -r requirements.txt"
        ) from exc
    credentials = _load_credentials(settings)
    if credentials is None:
        return BetaAnalyticsDataClient()
    return BetaAnalyticsDataClient(credentials=credentials)


def create_admin_client(settings: Settings | None = None) -> Any:
    settings = settings or Settings.from_env()
    try:
        from google.analytics.admin import AnalyticsAdminServiceClient
    except ImportError as exc:
        raise GA4ConfigurationError(
            "google-analytics-admin is not installed. Run: "
            "python -m pip install -r requirements.txt"
        ) from exc
    credentials = _load_credentials(settings)
    if credentials is None:
        return AnalyticsAdminServiceClient()
    return AnalyticsAdminServiceClient(credentials=credentials)


def _field(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(name, default)
    return getattr(value, name, default)


def _items(value: Any) -> list[Any]:
    if value is None:
        return []
    return list(value)


def _name(value: Any) -> str:
    return str(value) if value is not None else ""


def report_response_to_dict(response: Any) -> dict[str, Any]:
    """Convert a Data API Core report response to stable JSON-compatible data."""

    dimension_headers = _items(_field(response, "dimension_headers", []))
    metric_headers = _items(_field(response, "metric_headers", []))
    dimensions = [_name(_field(header, "name", "")) for header in dimension_headers]
    metrics = [
        {
            "name": _name(_field(header, "name", "")),
            "type": _name(_field(header, "type_", _field(header, "type", ""))),
        }
        for header in metric_headers
    ]
    rows: list[dict[str, str]] = []
    for row in _items(_field(response, "rows", [])):
        row_values: dict[str, str] = {}
        for header, value in zip(dimensions, _items(_field(row, "dimension_values", []))):
            row_values[header] = _name(_field(value, "value", ""))
        metric_names = (item["name"] for item in metrics)
        for header, value in zip(metric_names, _items(_field(row, "metric_values", []))):
            row_values[header] = _name(_field(value, "value", ""))
        rows.append(row_values)
    metadata = _field(response, "metadata", None)
    result: dict[str, Any] = {
        "dimension_headers": dimensions,
        "metric_headers": metrics,
        "rows": rows,
        "row_count": int(_field(response, "row_count", len(rows)) or 0),
    }
    if metadata is not None:
        result["metadata"] = {
            "currency_code": _name(_field(metadata, "currency_code", "")),
            "time_zone": _name(_field(metadata, "time_zone", "")),
        }
    return result


def run_report(
    *,
    property_id: str,
    dimensions: Sequence[str],
    metrics: Sequence[str],
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    offset: int = 0,
    dimension_filter: Mapping[str, Any] | None = None,
    metric_filter: Mapping[str, Any] | None = None,
    order_by: Sequence[Mapping[str, Any]] | None = None,
    client: Any | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    request = build_run_report_request(
        property_id=property_id,
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
        settings=settings,
    )
    client = client or create_data_client(settings)
    response = client.run_report(request=request)
    result = report_response_to_dict(response)
    result["property_id"] = request["property"].removeprefix("properties/")
    result["date_range"] = request["date_ranges"][0]
    return result


def run_realtime_report(
    *,
    property_id: str,
    dimensions: Sequence[str] = ("deviceCategory",),
    metrics: Sequence[str] = ("activeUsers",),
    limit: int | None = None,
    client: Any | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    normalized_property = resolve_property_id(property_id, settings)
    normalized_dimensions = _validate_names(dimensions, "dimensions", 9)
    normalized_metrics = _validate_names(metrics, "metrics", 10)
    if not normalized_metrics:
        raise GA4QueryError("metrics must contain at least one API name.")
    request: dict[str, Any] = {
        "property": f"properties/{normalized_property}",
        "dimensions": [{"name": name} for name in normalized_dimensions],
        "metrics": [{"name": name} for name in normalized_metrics],
        "limit": _validate_limit(limit, settings),
    }
    client = client or create_data_client(settings)
    response = client.run_realtime_report(request=request)
    result = report_response_to_dict(response)
    result["property_id"] = normalized_property
    result["report"] = "realtime"
    return result


def list_properties(
    *, client: Any | None = None, settings: Settings | None = None
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    client = client or create_admin_client(settings)
    properties: list[dict[str, Any]] = []
    for account in client.list_account_summaries():
        account_name = _name(_field(account, "account", ""))
        account_id = account_name.removeprefix("accounts/")
        for summary in _items(_field(account, "property_summaries", [])):
            property_name = _name(_field(summary, "property", ""))
            property_id = property_name.removeprefix("properties/")
            if settings.allowed_property_ids and property_id not in settings.allowed_property_ids:
                continue
            properties.append(
                {
                    "account_id": account_id,
                    "account_name": _name(_field(account, "display_name", "")),
                    "property_id": property_id,
                    "property_name": _name(_field(summary, "display_name", "")),
                    "property_type": _name(_field(summary, "property_type", "")),
                    "can_edit": bool(_field(summary, "can_edit", False)),
                }
            )
    return {"properties": properties, "property_count": len(properties)}


def get_metadata(
    *, property_id: str, client: Any | None = None, settings: Settings | None = None
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    normalized_property = resolve_property_id(property_id, settings)
    client = client or create_data_client(settings)
    response = client.get_metadata(name=f"properties/{normalized_property}/metadata")

    def metadata_items(field_name: str) -> list[dict[str, str]]:
        result = []
        for item in _items(_field(response, field_name, [])):
            result.append(
                {
                    "api_name": _name(_field(item, "api_name", "")),
                    "ui_name": _name(_field(item, "ui_name", "")),
                    "description": _name(_field(item, "description", "")),
                    "category": _name(_field(item, "category", "")),
                }
            )
        return result

    return {
        "property_id": normalized_property,
        "dimensions": metadata_items("dimensions"),
        "metrics": metadata_items("metrics"),
    }


def overview(**kwargs: Any) -> dict[str, Any]:
    return run_report(
        dimensions=[],
        metrics=[
            "activeUsers",
            "sessions",
            "screenPageViews",
            "bounceRate",
            "newUsers",
            "totalRevenue",
        ],
        **kwargs,
    )


def pages(**kwargs: Any) -> dict[str, Any]:
    return run_report(
        dimensions=["pagePath", "pageTitle"],
        metrics=["screenPageViews", "activeUsers", "averageSessionDuration"],
        order_by=[{"metric": {"metric_name": "screenPageViews"}, "desc": True}],
        **kwargs,
    )


def sources(**kwargs: Any) -> dict[str, Any]:
    return run_report(
        dimensions=["sessionSource", "sessionMedium"],
        metrics=["sessions", "activeUsers", "engagedSessions"],
        order_by=[{"metric": {"metric_name": "sessions"}, "desc": True}],
        **kwargs,
    )


def countries(**kwargs: Any) -> dict[str, Any]:
    return run_report(
        dimensions=["country"],
        metrics=["activeUsers", "sessions"],
        order_by=[{"metric": {"metric_name": "activeUsers"}, "desc": True}],
        **kwargs,
    )


def devices(**kwargs: Any) -> dict[str, Any]:
    return run_report(
        dimensions=["deviceCategory"],
        metrics=["activeUsers", "sessions"],
        order_by=[{"metric": {"metric_name": "activeUsers"}, "desc": True}],
        **kwargs,
    )


def daily(**kwargs: Any) -> dict[str, Any]:
    return run_report(
        dimensions=["date"],
        metrics=["activeUsers", "sessions", "screenPageViews", "totalRevenue"],
        order_by=[{"dimension": {"dimension_name": "date"}, "desc": False}],
        **kwargs,
    )


def realtime(**kwargs: Any) -> dict[str, Any]:
    return run_realtime_report(**kwargs)
