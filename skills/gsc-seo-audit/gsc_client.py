"""Read-only Google Search Console API client: auth, reports, and sitemap parsing.

Google client libraries are imported lazily (inside the functions that need
them) so Settings, validation, and sitemap parsing can be imported and tested
without installing credentials or Google dependencies.
"""

from __future__ import annotations

import gzip
import os
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Any

READONLY_SCOPES = ("https://www.googleapis.com/auth/webmasters.readonly",)
SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
USER_AGENT = "gsc-seo-audit-skill/1.0 (+https://github.com/anthropics/claude-code)"

# Google-documented limits this client designs around:
# - Search Analytics data is only retained for the trailing 16 months.
# - URL Inspection: 2,000 requests/day and 600/minute per property.
# - Search Analytics query: 1,200 requests/minute per property (not rate-limited here).
SEARCH_ANALYTICS_RETENTION_DAYS = 16 * 30
DEFAULT_INSPECT_PACE_SECONDS = 1.0
DEFAULT_SITEMAP_URL_CAP = 25
MAX_BATCH_URLS = 100
MAX_SITEMAP_RECURSION = 2
MAX_CHILD_SITEMAPS = 20


class GSCError(RuntimeError):
    """Base class for errors that can be shown safely to the user."""


class GSCConfigurationError(GSCError):
    """Raised when local configuration (credentials, site allowlist) is incomplete or invalid."""


class GSCQueryError(GSCError):
    """Raised when a request can't be built safely, or the API itself rejects it."""


@dataclass(frozen=True)
class Settings:
    """Runtime settings read from environment variables."""

    credentials_path: Path | None
    default_site_url: str | None
    allowed_site_urls: frozenset[str] = frozenset()
    max_limit: int = 1000

    @classmethod
    def from_env(cls) -> Settings:
        credentials_value = os.getenv("GSC_CREDENTIALS_PATH", "").strip()
        default_site = os.getenv("GSC_SITE_URL", "").strip() or None
        allowed_value = os.getenv("GSC_ALLOWED_SITE_URLS", "")
        allowed = frozenset(v.strip() for v in allowed_value.split(",") if v.strip())
        max_limit = _positive_env_int("GSC_MAX_LIMIT", 1000)
        return cls(
            credentials_path=Path(credentials_value) if credentials_value else None,
            default_site_url=default_site,
            allowed_site_urls=allowed,
            max_limit=max_limit,
        )


def _positive_env_int(name: str, fallback: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return fallback
    try:
        parsed = int(value)
    except ValueError as exc:
        raise GSCConfigurationError(f"{name} must be a positive integer.") from exc
    if parsed < 1:
        raise GSCConfigurationError(f"{name} must be a positive integer.")
    return parsed


def resolve_site_url(site_url: str | None, settings: Settings | None = None) -> str:
    settings = settings or Settings.from_env()
    candidate = site_url.strip() if site_url else settings.default_site_url
    if not candidate:
        raise GSCConfigurationError(
            "No site URL given. Pass site_url, set GSC_SITE_URL, or call the 'properties' "
            "report first to see which ones the credential can access."
        )
    if settings.allowed_site_urls and candidate not in settings.allowed_site_urls:
        raise GSCConfigurationError(f"{candidate} is not in GSC_ALLOWED_SITE_URLS.")
    return candidate


def validate_limit(limit: int | None, settings: Settings, fallback: int = 20) -> int:
    value = fallback if limit is None else limit
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise GSCQueryError("limit must be a positive integer.")
    if value > settings.max_limit:
        raise GSCQueryError(f"limit cannot exceed the configured limit of {settings.max_limit}.")
    return value


@dataclass
class SearchAnalyticsRow:
    keys: list[str]
    clicks: int
    impressions: int
    ctr: float
    position: float


@dataclass
class InspectionResult:
    page_url: str
    verdict: str = "UNKNOWN"
    coverage_state: str = "Unknown"
    robots_txt_state: str = ""
    indexing_state: str = ""
    page_fetch_state: str = ""
    last_crawl_time: str = ""
    google_canonical: str = ""
    user_canonical: str = ""
    inspection_link: str = ""
    referring_urls: list[str] = field(default_factory=list)
    rich_result_verdict: str = ""
    rich_result_types: list[str] = field(default_factory=list)
    error: str = ""


def even_sample(items: list, k: int) -> list:
    """Pick k items spread evenly across the list, rather than just the first k.

    A flat prefix would bias toward whatever the sitemap happens to list first
    (often one section of the site); spreading the sample keeps it representative.
    """
    if k <= 0 or not items:
        return []
    if len(items) <= k:
        return list(items)
    step = len(items) / k
    return [items[int(i * step)] for i in range(k)]


def default_date_range(days: int, end: str | None = None, start: str | None = None) -> tuple[str, str]:
    # GSC dates are plain calendar days, not instants — the user's local "today" is what
    # they mean by "last N days", not a UTC-shifted one, so date.today() is intentional here.
    end_date = end or date.today().isoformat()  # noqa: DTZ011
    if start:
        return start, end_date
    end_d = date.fromisoformat(end_date)
    return (end_d - timedelta(days=days)).isoformat(), end_date


def _wrap_http_error(err: Any, context: str) -> GSCError:
    from googleapiclient.errors import HttpError

    if not isinstance(err, HttpError):
        return GSCQueryError(f"{context}: {err}")

    status = err.resp.status if err.resp else None
    reason = ""
    try:
        reason = err.error_details[0].get("reason", "") if err.error_details else ""
    except (AttributeError, IndexError, TypeError):
        pass

    if status == 403:
        return GSCConfigurationError(
            f"{context}: permission denied (403). The credential must be added as a 'Full' "
            "user (not Restricted) on this exact property in Search Console "
            "(Settings > Users and permissions), and the Search Console API must be enabled "
            "on its Google Cloud project."
        )
    if status == 404:
        return GSCQueryError(
            f"{context}: property not found (404). Check the site URL matches exactly what "
            "Search Console shows, including the 'sc-domain:' prefix for domain properties."
        )
    if status == 429 or reason in ("rateLimitExceeded", "quotaExceeded", "userRateLimitExceeded"):
        return GSCQueryError(
            f"{context}: quota or rate limit exceeded. URL Inspection allows 2,000 "
            "requests/day and 600/minute per property; Search Analytics allows 1,200/minute. "
            "Wait before retrying, or reduce the batch size."
        )
    return GSCQueryError(f"{context}: {err}")


def _retry_transient(fn: Callable[[], Any], *, attempts: int = 3, base_delay: float = 2.0) -> Any:
    from googleapiclient.errors import HttpError

    last_err: Exception | None = None
    for attempt in range(attempts):
        try:
            return fn()
        except HttpError as err:
            status = err.resp.status if err.resp else None
            if status not in (429, 500, 502, 503, 504) or attempt == attempts - 1:
                raise
            last_err = err
            time.sleep(base_delay * (2**attempt))
    raise last_err  # pragma: no cover - unreachable, satisfies type checkers


def create_service(settings: Settings | None = None) -> Any:
    settings = settings or Settings.from_env()
    if settings.credentials_path is None:
        raise GSCConfigurationError(
            "No credentials configured. Set GSC_CREDENTIALS_PATH to the absolute path of "
            "your service account JSON key."
        )
    if not settings.credentials_path.is_file():
        raise GSCConfigurationError(f"Credentials file not found: {settings.credentials_path}")

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise GSCConfigurationError(
            "Google dependencies are not installed. Run: python3 -m pip install -r requirements.txt"
        ) from exc

    try:
        creds = service_account.Credentials.from_service_account_file(
            str(settings.credentials_path), scopes=list(READONLY_SCOPES)
        )
    except ValueError as err:
        raise GSCConfigurationError(f"Credentials file is not a valid service account key: {err}") from err
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def service_account_email(settings: Settings | None = None) -> str:
    import json

    settings = settings or Settings.from_env()
    if settings.credentials_path is None:
        raise GSCConfigurationError("GSC_CREDENTIALS_PATH is not set.")
    with open(settings.credentials_path) as f:
        return json.load(f).get("client_email", "unknown")


# -- Sites --------------------------------------------------------------


def list_sites(*, service: Any = None, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    service = service or create_service(settings)
    try:
        resp = _retry_transient(lambda: service.sites().list().execute())
    except Exception as err:
        raise _wrap_http_error(err, "Listing properties") from err

    sites = [
        {"site_url": s.get("siteUrl", ""), "permission_level": s.get("permissionLevel", "")}
        for s in resp.get("siteEntry", [])
        if not settings.allowed_site_urls or s.get("siteUrl", "") in settings.allowed_site_urls
    ]
    return {"sites": sites}


# -- Search Analytics -----------------------------------------------------


def search_analytics(
    *,
    site_url: str,
    dimensions: list[str],
    days: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
    filters: list[dict[str, str]] | None = None,
    data_state: str = "final",
    search_type: str = "web",
    service: Any = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    resolved_site = resolve_site_url(site_url, settings)
    start, end = default_date_range(days if days is not None else 28, end_date, start_date)
    row_limit = validate_limit(limit, settings)

    body: dict[str, Any] = {
        "startDate": start,
        "endDate": end,
        "dimensions": dimensions,
        "rowLimit": row_limit,
        "dataState": data_state,
        "type": search_type,
    }
    if filters:
        body["dimensionFilterGroups"] = [{"filters": filters}]

    service = service or create_service(settings)
    try:
        resp = _retry_transient(
            lambda: service.searchanalytics().query(siteUrl=resolved_site, body=body).execute()
        )
    except Exception as err:
        raise _wrap_http_error(err, f"Search analytics query for {resolved_site}") from err

    rows = [
        SearchAnalyticsRow(
            keys=row.get("keys", []),
            clicks=row.get("clicks", 0),
            impressions=row.get("impressions", 0),
            ctr=row.get("ctr", 0.0),
            position=row.get("position", 0.0),
        )
        for row in resp.get("rows", [])
    ]
    return {
        "site_url": resolved_site,
        "start_date": start,
        "end_date": end,
        "dimensions": dimensions,
        "rows": [_row_to_record(r, dimensions) for r in rows],
    }


def _row_to_record(row: SearchAnalyticsRow, dimensions: list[str]) -> dict[str, Any]:
    record = dict(zip(dimensions, row.keys))
    record.update(clicks=row.clicks, impressions=row.impressions, ctr=row.ctr, position=row.position)
    return record


# -- Sitemaps -------------------------------------------------------------


def list_sitemaps(*, site_url: str, service: Any = None, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    resolved_site = resolve_site_url(site_url, settings)
    service = service or create_service(settings)
    try:
        resp = _retry_transient(lambda: service.sitemaps().list(siteUrl=resolved_site).execute())
    except Exception as err:
        raise _wrap_http_error(err, f"Listing sitemaps for {resolved_site}") from err

    out = []
    for sm in resp.get("sitemap", []):
        url_count = next((c.get("submitted", 0) for c in sm.get("contents", []) if c.get("type") == "web"), None)
        out.append(
            {
                "path": sm.get("path", ""),
                "last_downloaded": sm.get("lastDownloaded", ""),
                "last_submitted": sm.get("lastSubmitted", ""),
                "is_pending": sm.get("isPending", False),
                "is_sitemap_index": sm.get("isSitemapsIndex", False),
                "url_count": url_count,
                "errors": sm.get("errors", 0),
                "warnings": sm.get("warnings", 0),
            }
        )
    return {"site_url": resolved_site, "sitemaps": out}


def fetch_sitemap_urls(sitemap_url: str, cap: int = DEFAULT_SITEMAP_URL_CAP) -> tuple[list[str], int]:
    """Download and parse a sitemap (or sitemap index) via plain HTTP — no Google API involved.

    Returns (urls, total_seen). total_seen may exceed len(urls) when the sitemap has more
    entries than `cap`; urls are sampled evenly across the file rather than truncated from
    the start, so a capped audit still reflects the whole site.
    """
    all_urls = _collect_sitemap_urls(sitemap_url, depth=0, child_budget=[MAX_CHILD_SITEMAPS])
    return even_sample(all_urls, cap), len(all_urls)


def _collect_sitemap_urls(sitemap_url: str, depth: int, child_budget: list[int]) -> list[str]:
    root = _fetch_sitemap_xml(sitemap_url)
    tag = root.tag.replace(SITEMAP_NS, "")

    if tag == "urlset":
        return [
            loc.text.strip()
            for url_el in root.findall(f"{SITEMAP_NS}url")
            if (loc := url_el.find(f"{SITEMAP_NS}loc")) is not None and loc.text
        ]

    if tag == "sitemapindex":
        if depth >= MAX_SITEMAP_RECURSION:
            return []
        urls: list[str] = []
        for sm_el in root.findall(f"{SITEMAP_NS}sitemap"):
            if child_budget[0] <= 0:
                break
            loc = sm_el.find(f"{SITEMAP_NS}loc")
            if loc is None or not loc.text:
                continue
            child_budget[0] -= 1
            try:
                urls.extend(_collect_sitemap_urls(loc.text.strip(), depth + 1, child_budget))
            except GSCError:
                continue
        return urls

    raise GSCQueryError(f"Unrecognized sitemap format at {sitemap_url} (root tag: {tag})")


def _fetch_sitemap_xml(url: str) -> ET.Element:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = resp.read()
    except Exception as err:
        raise GSCQueryError(f"Could not download sitemap {url}: {err}") from err

    if url.endswith(".gz") or raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError as err:
            raise GSCQueryError(f"Could not decompress gzipped sitemap {url}: {err}") from err

    try:
        return ET.fromstring(raw)
    except ET.ParseError as err:
        raise GSCQueryError(f"Could not parse sitemap XML at {url}: {err}") from err


# -- URL Inspection ---------------------------------------------------------


def inspect_url(
    *, site_url: str, page_url: str, service: Any = None, settings: Settings | None = None
) -> InspectionResult:
    settings = settings or Settings.from_env()
    resolved_site = resolve_site_url(site_url, settings)
    service = service or create_service(settings)
    body = {"inspectionUrl": page_url, "siteUrl": resolved_site}
    try:
        resp = _retry_transient(
            lambda: service.urlInspection().index().inspect(body=body).execute()
        )
    except Exception as err:
        raise _wrap_http_error(err, f"Inspecting {page_url}") from err

    return _parse_inspection(page_url, resp)


def _parse_inspection(page_url: str, resp: dict[str, Any]) -> InspectionResult:
    result = resp.get("inspectionResult", {})
    idx = result.get("indexStatusResult", {})
    rich = result.get("richResultsResult", {})
    return InspectionResult(
        page_url=page_url,
        verdict=idx.get("verdict", "UNKNOWN"),
        coverage_state=idx.get("coverageState", "Unknown"),
        robots_txt_state=idx.get("robotsTxtState", ""),
        indexing_state=idx.get("indexingState", ""),
        page_fetch_state=idx.get("pageFetchState", ""),
        last_crawl_time=idx.get("lastCrawlTime", ""),
        google_canonical=idx.get("googleCanonical", ""),
        user_canonical=idx.get("userCanonical", ""),
        inspection_link=result.get("inspectionResultLink", ""),
        referring_urls=idx.get("referringUrls", []),
        rich_result_verdict=rich.get("verdict", ""),
        rich_result_types=[item.get("richResultType", "") for item in rich.get("detectedItems", [])],
    )


def batch_inspect(
    *,
    site_url: str,
    urls: list[str],
    pace_seconds: float = DEFAULT_INSPECT_PACE_SECONDS,
    service: Any = None,
    settings: Settings | None = None,
) -> tuple[list[InspectionResult], str | None]:
    """Inspect URLs sequentially, pacing calls to stay well under quota.

    Returns (results, stopped_reason). stopped_reason is set (and the loop stops
    early, keeping whatever was gathered so far) only on a quota/rate error — a
    single URL failing for any other reason is recorded as an InspectionResult
    with `.error` set, and the batch continues.
    """
    settings = settings or Settings.from_env()
    resolved_site = resolve_site_url(site_url, settings)
    service = service or create_service(settings)

    results: list[InspectionResult] = []
    for i, url in enumerate(urls):
        try:
            results.append(inspect_url(site_url=resolved_site, page_url=url, service=service, settings=settings))
        except GSCError as err:
            if "quota or rate limit" in str(err):
                return results, str(err)
            results.append(InspectionResult(page_url=url, error=str(err)))
        if i < len(urls) - 1:
            time.sleep(pace_seconds)
    return results, None


def summarize_inspections(site_url: str, results: list[InspectionResult], stopped_reason: str | None) -> dict[str, Any]:
    coverage_breakdown: dict[str, int] = {}
    verdict_breakdown: dict[str, int] = {}
    for r in results:
        coverage_breakdown[r.coverage_state] = coverage_breakdown.get(r.coverage_state, 0) + 1
        verdict_breakdown[r.verdict] = verdict_breakdown.get(r.verdict, 0) + 1

    return {
        "site_url": site_url,
        "checked": len(results),
        "coverage_breakdown": coverage_breakdown,
        "verdict_breakdown": verdict_breakdown,
        "stopped_early_reason": stopped_reason,
        "results": [vars(r) for r in results],
    }


# -- Higher-level reports ---------------------------------------------------
# These combine the primitives above into the answers Claude and the CLI/MCP
# layers actually ask for, so gsc_query.py and gsc_mcp_server.py stay thin
# argument-mapping wrappers around one shared implementation.

DEFAULT_AUDIT_LOOKBACK_DAYS = 90
DEFAULT_AUDIT_ANALYTICS_ROW_LIMIT = 5000


def performance_report(
    *,
    site_url: str | None = None,
    days: int = 28,
    start_date: str | None = None,
    end_date: str | None = None,
    data_state: str = "final",
    settings: Settings | None = None,
    service: Any = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    service = service or create_service(settings)
    start, end = default_date_range(days, end_date, start_date)
    day_span = (date.fromisoformat(end) - date.fromisoformat(start)).days + 1

    totals = search_analytics(
        site_url=site_url, dimensions=[], start_date=start, end_date=end, limit=1,
        data_state=data_state, service=service, settings=settings,
    )
    daily = search_analytics(
        site_url=site_url, dimensions=["date"], start_date=start, end_date=end, limit=day_span,
        data_state=data_state, service=service, settings=settings,
    )
    zero = {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}
    total_row = totals["rows"][0] if totals["rows"] else zero
    return {
        "site_url": totals["site_url"],
        "start_date": start,
        "end_date": end,
        "totals": {k: total_row[k] for k in ("clicks", "impressions", "ctr", "position")},
        "daily": sorted(daily["rows"], key=lambda r: r["date"]),
    }


def compare_periods(
    *,
    site_url: str | None,
    p1_start: str,
    p1_end: str,
    p2_start: str,
    p2_end: str,
    dimensions: list[str] | None = None,
    limit: int = 20,
    data_state: str = "final",
    settings: Settings | None = None,
    service: Any = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    service = service or create_service(settings)
    dims = dimensions or ["query"]

    p1 = search_analytics(
        site_url=site_url, dimensions=dims, start_date=p1_start, end_date=p1_end,
        limit=1000, data_state=data_state, service=service, settings=settings,
    )
    p2 = search_analytics(
        site_url=site_url, dimensions=dims, start_date=p2_start, end_date=p2_end,
        limit=1000, data_state=data_state, service=service, settings=settings,
    )

    def key_of(record: dict[str, Any]) -> tuple:
        return tuple(record[d] for d in dims)

    p1_by_key = {key_of(r): r for r in p1["rows"]}
    p2_by_key = {key_of(r): r for r in p2["rows"]}
    zero = {"clicks": 0, "impressions": 0, "ctr": 0.0, "position": 0.0}

    comparisons = []
    for key in set(p1_by_key) | set(p2_by_key):
        r1 = p1_by_key.get(key, zero)
        r2 = p2_by_key.get(key, zero)
        record = dict(zip(dims, key))
        record.update(
            p1_clicks=r1["clicks"], p2_clicks=r2["clicks"], clicks_change=r2["clicks"] - r1["clicks"],
            p1_impressions=r1["impressions"], p2_impressions=r2["impressions"],
            p1_position=round(r1["position"], 1), p2_position=round(r2["position"], 1),
        )
        comparisons.append(record)
    comparisons.sort(key=lambda r: abs(r["clicks_change"]), reverse=True)

    return {
        "site_url": p1["site_url"],
        "dimensions": dims,
        "period1": {"start": p1_start, "end": p1_end},
        "period2": {"start": p2_start, "end": p2_end},
        "rows": comparisons[:limit],
    }


def check_indexing(
    *,
    site_url: str | None,
    urls: list[str],
    settings: Settings | None = None,
    service: Any = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    resolved_site = resolve_site_url(site_url, settings)
    if len(urls) > MAX_BATCH_URLS:
        raise GSCQueryError(
            f"{len(urls)} URLs given, max {MAX_BATCH_URLS} per call (URL Inspection has a "
            "2,000/day quota per property). Split into multiple calls."
        )
    service = service or create_service(settings)
    results, stopped_reason = batch_inspect(site_url=resolved_site, urls=urls, service=service, settings=settings)
    return summarize_inspections(resolved_site, results, stopped_reason)


def run_site_audit(
    *,
    site_url: str | None,
    sitemap_url: str | None = None,
    limit: int = DEFAULT_SITEMAP_URL_CAP,
    lookback_days: int = DEFAULT_AUDIT_LOOKBACK_DAYS,
    data_state: str = "final",
    settings: Settings | None = None,
    service: Any = None,
) -> dict[str, Any]:
    settings = settings or Settings.from_env()
    resolved_site = resolve_site_url(site_url, settings)
    service = service or create_service(settings)

    sitemap_path = sitemap_url
    if not sitemap_path:
        sitemaps = list_sitemaps(site_url=resolved_site, service=service, settings=settings)["sitemaps"]
        if not sitemaps:
            raise GSCQueryError(
                f"No sitemaps are submitted for {resolved_site}. Pass sitemap_url explicitly "
                "(e.g. https://example.com/sitemap.xml), or use check_indexing with an "
                "explicit list of URLs instead."
            )
        sitemap_path = sitemaps[0]["path"]

    all_urls, total_seen = fetch_sitemap_urls(sitemap_path, cap=10_000)

    analytics = search_analytics(
        site_url=resolved_site, dimensions=["page"], days=lookback_days,
        limit=min(DEFAULT_AUDIT_ANALYTICS_ROW_LIMIT, settings.max_limit),
        data_state=data_state, service=service, settings=settings,
    )
    pages_with_impressions = {r["page"] for r in analytics["rows"]}
    zero_impression = [u for u in all_urls if u not in pages_with_impressions]

    inspect_limit = min(limit, MAX_BATCH_URLS)
    priority = even_sample(zero_impression, inspect_limit)
    remaining_slots = inspect_limit - len(priority)
    if remaining_slots > 0:
        others = [u for u in all_urls if u not in set(priority)]
        priority += even_sample(others, remaining_slots)

    results, stopped_reason = batch_inspect(site_url=resolved_site, urls=priority, service=service, settings=settings)
    summary = summarize_inspections(resolved_site, results, stopped_reason)
    summary.update(
        sitemap_source=sitemap_path,
        total_sitemap_urls=total_seen,
        sampled_sitemap_urls=len(all_urls),
        lookback_days=lookback_days,
        zero_impression_count=len(zero_impression),
        zero_impression_sample=zero_impression[:50],
        inspected_count=len(priority),
    )
    return summary
