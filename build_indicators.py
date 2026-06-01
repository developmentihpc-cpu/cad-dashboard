#!/usr/bin/env python3
"""
build_indicators.py — bakes World Bank indicator data into a static JSON snapshot.

Why: the dashboard used to fire ~40 live World Bank API calls per country on every
page load. One failed request (network / CORS / rate-limit / sandbox) silently wiped
out the whole panel. This script pulls everything once, up front, into
docs/data/indicators.json, which the dashboard loads instantly. A monthly GitHub
Action re-runs it to keep the snapshot fresh (WB indicators update ~annually).

Single source of truth: the country list (COUNTRY_ISO) and the indicator IDs
(CA_INDICATORS) are parsed directly out of docs/index.html, so this script can never
drift from what the dashboard actually displays.

Efficiency: instead of country x indicator individual calls, it makes ONE request per
indicator against country/all (mrv=5), then keeps the most recent non-null value per
country. ~70 requests total.

Output shape (matches the dashboard's countryDataCache exactly):
    {
      "_meta": { "generated": "...", "source": "...", "countries": N, "indicators": M },
      "Ethiopia": { "NY.GDP.MKTP.KD.ZG": {"value": 6.1, "year": "2023"}, ... },
      ...
    }
"""
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
INDEX_HTML = ROOT / "docs" / "index.html"
OUT_PATH = ROOT / "docs" / "data" / "indicators.json"

WB_BASE = "https://api.worldbank.org/v2"
MRV = 5            # most-recent 5 values per country; we keep the newest non-null
PER_PAGE = 20000   # one page covers ~260 economies x 5 = ~1,300 rows comfortably
TIMEOUT = 30
RETRIES = 3


def _read_index() -> str:
    if not INDEX_HTML.exists():
        sys.exit(f"ERROR: {INDEX_HTML} not found")
    return INDEX_HTML.read_text(encoding="utf-8")


def parse_country_iso(html: str) -> dict:
    """Extract the COUNTRY_ISO map (display name -> ISO3) from index.html."""
    m = re.search(r"const COUNTRY_ISO\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
    if not m:
        sys.exit("ERROR: could not locate COUNTRY_ISO in index.html")
    block = m.group(1)
    pairs = re.findall(r"'((?:[^'\\]|\\.)*)'\s*:\s*'([A-Z]{3})'", block)
    out = {}
    for name, iso3 in pairs:
        out[name.replace("\\'", "'")] = iso3
    if not out:
        sys.exit("ERROR: parsed 0 countries from COUNTRY_ISO")
    return out


def parse_indicator_ids(html: str) -> list:
    """Extract unique World Bank indicator IDs from CA_INDICATORS in index.html.

    WB ids are uppercase letters / digits / dots (e.g. NY.GDP.MKTP.KD.ZG). The
    OEC special rows use lowercase '__oec_*' ids and are naturally excluded.
    """
    m = re.search(r"const CA_INDICATORS\s*=\s*\{(.*?)\n\};", html, re.DOTALL)
    if not m:
        sys.exit("ERROR: could not locate CA_INDICATORS in index.html")
    block = m.group(1)
    ids = re.findall(r"id\s*:\s*'([A-Z0-9.]+)'", block)
    seen, ordered = set(), []
    for i in ids:
        if i not in seen:
            seen.add(i)
            ordered.append(i)
    if not ordered:
        sys.exit("ERROR: parsed 0 indicator IDs from CA_INDICATORS")
    return ordered


def fetch_indicator_all_countries(indicator_id: str) -> dict:
    """Return {iso3: {'value': float, 'year': 'YYYY'}} for one indicator, all countries.

    Keeps the most recent non-null observation per country.
    """
    url = f"{WB_BASE}/country/all/indicator/{indicator_id}"
    params = {"format": "json", "mrv": MRV, "per_page": PER_PAGE}
    last_err = None
    for attempt in range(1, RETRIES + 1):
        try:
            resp = requests.get(url, params=params, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if not isinstance(data, list) or len(data) < 2 or not data[1]:
                return {}
            best: dict = {}
            for row in data[1]:
                iso3 = row.get("countryiso3code")
                val = row.get("value")
                year = row.get("date")
                if not iso3 or val is None or year is None:
                    continue
                cur = best.get(iso3)
                # rows usually arrive newest-first; keep the newest year we see
                if cur is None or year > cur["year"]:
                    best[iso3] = {"value": val, "year": str(year)}
            return best
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(1.5 * attempt)
    print(f"  ! {indicator_id}: failed after {RETRIES} attempts ({last_err})")
    return {}


def main() -> None:
    html = _read_index()
    country_iso = parse_country_iso(html)
    indicator_ids = parse_indicator_ids(html)
    iso3_to_name = {iso: name for name, iso in country_iso.items()}

    print(f"Countries: {len(country_iso)} | Indicators: {len(indicator_ids)}")
    print(f"Fetching from {WB_BASE} (one request per indicator)...")

    out: dict = {name: {} for name in country_iso}
    filled = 0
    for n, ind in enumerate(indicator_ids, 1):
        by_iso = fetch_indicator_all_countries(ind)
        hits = 0
        for iso3, rec in by_iso.items():
            name = iso3_to_name.get(iso3)
            if name is not None:
                out[name][ind] = rec
                hits += 1
                filled += 1
        print(f"  [{n:>2}/{len(indicator_ids)}] {ind:<22} {hits} countries")

    out = {name: vals for name, vals in out.items()}
    payload = {
        "_meta": {
            "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "World Bank Open Data API (api.worldbank.org)",
            "countries": len(country_iso),
            "indicators": len(indicator_ids),
            "datapoints": filled,
        },
        **out,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")
    size_kb = OUT_PATH.stat().st_size / 1024
    print(f"\nWrote {OUT_PATH} ({size_kb:.0f} KB, {filled} datapoints)")


if __name__ == "__main__":
    main()
