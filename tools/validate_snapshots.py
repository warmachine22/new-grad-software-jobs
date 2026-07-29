#!/usr/bin/env python3
"""Validate static job snapshots for duplicate and application-link risks.

This checker deliberately separates URL reachability from application readiness.
An HTTP 200 response is only one signal: a posting can still be a generic board,
a redirect, a filled role, or a JavaScript shell with no job evidence.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
JOBS_DIR = ROOT / "jobs"
TRACKING_KEYS = {"source", "gh_src", "lever-source", "ashby_jid"}
DEAD_MARKERS = (
    "job not found",
    "position has been filled",
    "no longer accepting applications",
    "this job is no longer available",
    "job is no longer available",
    "job no longer exists",
    "the job you are looking for could not be found",
)
GENERIC_TITLES = {"jobs", "careers", "job board", "current openings"}


def normalize_url(raw: str) -> str:
    """Return a stable comparison key without destroying job identity."""

    raw = html.unescape(raw).strip()
    parts = urlsplit(raw)
    host = parts.netloc.lower()
    if host == "boards.greenhouse.io":
        host = "job-boards.greenhouse.io"
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower = key.lower()
        if lower in TRACKING_KEYS or lower.startswith("utm_"):
            continue
        query.append((key, value))
    return urlunsplit(
        (
            parts.scheme.lower(),
            host,
            parts.path.rstrip("/"),
            urlencode(sorted(query)),
            "",
        )
    )


def extract_urls(path: Path) -> list[str]:
    content = path.read_text(encoding="utf-8")
    found = re.findall(r"https?://[^\"'\s<>]+", content, re.I)
    return sorted({html.unescape(url).rstrip(".,") for url in found})


def page_sort_key(page: str) -> tuple[str, int, str]:
    stem = Path(page).stem
    match = re.match(r"(\d{4}-\d{2}-\d{2})(.*)", stem)
    if not match:
        return ("", 0, stem)
    suffix = match.group(2)
    rank = 2 if suffix == "-overhaul" else 1 if suffix == "-baseline" else 0
    return (match.group(1), rank, stem)


def extract_records(path: Path) -> list[dict[str, Any]]:
    """Extract the embedded JSON rows used by newer snapshots."""

    content = path.read_text(encoding="utf-8")
    match = re.search(r"const jobs = (\[.*?\]);\s*const tbody", content, re.S)
    if not match:
        return []
    try:
        rows = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"{path}: embedded jobs JSON is invalid: {exc}") from exc
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError(f"{path}: embedded jobs value must be a list of objects")
    return rows


def text_only(markup: str) -> str:
    markup = re.sub(r"<script\b.*?</script>", " ", markup, flags=re.I | re.S)
    markup = re.sub(r"<style\b.*?</style>", " ", markup, flags=re.I | re.S)
    markup = re.sub(r"<[^>]+>", " ", markup)
    return re.sub(r"\s+", " ", html.unescape(markup)).strip()


def fetch(url: str) -> dict[str, Any]:
    request = Request(
        url,
        headers={
            "User-Agent": "new-grad-job-validator/1.0 (+static archive QA)",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            markup = response.read(1_500_000).decode("utf-8", errors="replace")
            title_match = re.search(
                r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S
            )
            title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else ""
            final_url = response.geturl()
            body = text_only(markup).lower()
            return {
                "url": url,
                "status": response.status,
                "final_url": final_url,
                "title": title,
                "has_apply": bool(re.search(r"\bapply\b", body)),
                "dead_marker": next((marker for marker in DEAD_MARKERS if marker in body), ""),
                "generic_shell": title.lower().strip() in GENERIC_TITLES
                or "enable javascript to run this app" in body,
            }
    except HTTPError as exc:
        return {"url": url, "status": exc.code, "error": str(exc)}
    except (TimeoutError, URLError, OSError) as exc:
        return {"url": url, "status": "ERR", "error": str(exc)}


def validate_row(row: dict[str, Any], source: str) -> list[str]:
    required = (
        "Company",
        "Role",
        "Location",
        "Fit",
        "ResumeMatch",
        "Caveat",
        "DirectJobURL",
        "Source",
        "VerifiedAsOf",
    )
    errors = [f"{source}: missing {key}" for key in required if not row.get(key)]
    if row.get("Fit") not in {"Excellent", "Strong", "Good", "Adjacent"}:
        errors.append(f"{source}: unsupported Fit value {row.get('Fit')!r}")
    if row.get("DirectJobURL") and not row["DirectJobURL"].startswith("https://"):
        errors.append(f"{source}: application URL is not HTTPS")
    if row.get("HTTPStatus") and str(row["HTTPStatus"]) != "200":
        errors.append(f"{source}: recorded HTTPStatus is {row['HTTPStatus']!r}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-live", action="store_true", help="fetch every external job URL")
    parser.add_argument("--limit", type=int, default=0, help="limit live checks for a quick smoke test")
    parser.add_argument("--newest-only", action="store_true", help="live-check only the newest page")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()

    pages = sorted(JOBS_DIR.glob("*.html"))
    page_urls: dict[str, list[str]] = {str(path.relative_to(ROOT)): extract_urls(path) for path in pages}
    newest_page = max(page_urls, key=page_sort_key) if page_urls else ""
    records: list[tuple[str, dict[str, Any]]] = []
    errors: list[str] = []
    for path in pages:
        relative = str(path.relative_to(ROOT))
        try:
            for row in extract_records(path):
                records.append((relative, row))
                if relative == newest_page:
                    errors.extend(validate_row(row, f"{relative}:{row.get('Company', '?')}"))
        except ValueError as exc:
            errors.append(str(exc))

    seen: dict[str, list[str]] = {}
    for page, urls in page_urls.items():
        for url in urls:
            seen.setdefault(normalize_url(url), []).append(f"{page}: {url}")
    duplicate_groups = {key: values for key, values in seen.items() if len(values) > 1}
    newest_keys = {normalize_url(url) for url in page_urls.get(newest_page, [])}
    historical_keys = set(seen) - newest_keys
    newest_overlaps = {
        key: duplicate_groups[key]
        for key in newest_keys & historical_keys
        if key in duplicate_groups
    }

    live: list[dict[str, Any]] = []
    if args.check_live:
        urls = (
            [normalize_url(url) for url in page_urls.get(newest_page, [])]
            if args.newest_only
            else list(seen)
        )
        if args.limit:
            urls = urls[: args.limit]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            live = list(pool.map(fetch, urls))

    result = {
        "checked_on": date.today().isoformat(),
        "snapshot_pages": len(pages),
        "embedded_rows": len(records),
        "external_urls": len(seen),
        "duplicate_groups": duplicate_groups,
        "newest_page": newest_page,
        "newest_overlaps": newest_overlaps,
        "schema_errors": errors,
        "live_checks": live,
        "live_failures": [
            item
            for item in live
            if item.get("status") != 200 or item.get("dead_marker") or item.get("generic_shell")
        ],
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Snapshot pages: {result['snapshot_pages']}")
        print(f"Embedded rows: {result['embedded_rows']}")
        print(f"Unique normalized URLs: {result['external_urls']}")
        print(f"Duplicate URL groups: {len(duplicate_groups)}")
        print(f"Newest page: {newest_page}")
        print(f"Newest-page overlaps: {len(newest_overlaps)}")
        print(f"Schema errors: {len(errors)}")
        if args.check_live:
            print(f"Live checks: {len(live)}")
            print(f"Live failures or manual-review shells: {len(result['live_failures'])}")
            for item in result["live_failures"]:
                print(
                    f"  {item['status']} {item['url']}"
                    f" {item.get('dead_marker') or 'manual-review'}"
                )
    return 1 if errors or newest_overlaps else 0


if __name__ == "__main__":
    sys.exit(main())
