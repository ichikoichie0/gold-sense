#!/usr/bin/env python3
"""
Gold Sense — data fetcher.

Pulls the latest available (prior trading day) values for the gold-analysis
framework from FRED's public CSV endpoints. No API key required.

Design principle: NEVER fabricate data. If a series can't be fetched or has no
recent value, that field is written as null and the front-end shows "data
unavailable" rather than inventing a number.
"""

import csv
import io
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

# FRED public "fredgraph.csv" endpoint — no API key required.
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
# Optional: if a FRED_API_KEY env var is set (free from fredaccount.stlouisfed.org),
# the official JSON API is used as a fallback when the CSV endpoint is blocked.
FRED_API = ("https://api.stlouisfed.org/fred/series/observations"
            "?series_id={series}&api_key={key}&file_type=json&sort_order=desc&limit=10")

# Series we track. Each maps to a FRED series ID.
SERIES = {
    "real_2y":   "DFII2",     # 2Y TIPS real yield  (noise detector)
    "real_5y":   "DFII5",     # 5Y TIPS real yield
    "real_10y":  "DFII10",    # 10Y TIPS real yield (structural anchor)
    "breakeven_10y": "T10YIE",# 10Y breakeven inflation
    "dxy":       "DTWEXBGS",  # Broad USD index
    "vix":       "VIXCLS",    # VIX close
    "gold":      "GOLDPMGBD228NLBM",  # Gold fixing price, London PM, USD/oz
}

REQUEST_HEADERS = {"User-Agent": "gold-sense-data-fetcher/1.0"}


def fetch_latest(series_id):
    """Return (date_str, value_float) for the most recent non-empty observation,
    or (None, None) if it cannot be fetched / parsed. Never raises.
    Tries the public CSV endpoint first, then the JSON API if a key is set."""
    # Attempt 1: public CSV endpoint (no key).
    result = _fetch_csv(series_id)
    if result[1] is not None:
        return result

    # Attempt 2: official JSON API, only if a free key is available.
    key = os.environ.get("FRED_API_KEY", "").strip()
    if key:
        result = _fetch_json_api(series_id, key)
        if result[1] is not None:
            return result

    return (None, None)


def _fetch_csv(series_id):
    url = FRED_CSV.format(series=series_id)
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ! CSV fetch failed for {series_id}: {e}", file=sys.stderr)
        return (None, None)
    try:
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        for row in reversed(rows[1:]):
            if len(row) < 2:
                continue
            date_str, raw = row[0].strip(), row[1].strip()
            if raw in ("", ".", "NaN", "null"):
                continue
            try:
                return (date_str, float(raw))
            except ValueError:
                continue
    except Exception as e:
        print(f"  ! CSV parse failed for {series_id}: {e}", file=sys.stderr)
    return (None, None)


def _fetch_json_api(series_id, key):
    url = FRED_API.format(series=series_id, key=key)
    try:
        req = urllib.request.Request(url, headers=REQUEST_HEADERS)
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"  ! JSON API fetch failed for {series_id}: {e}", file=sys.stderr)
        return (None, None)
    for obs in payload.get("observations", []):
        raw = str(obs.get("value", "")).strip()
        if raw in ("", ".", "NaN", "null"):
            continue
        try:
            return (obs.get("date"), float(raw))
        except ValueError:
            continue
    return (None, None)


def main():
    print("Fetching Gold Sense data from FRED ...")
    out = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "source": "FRED (Federal Reserve Bank of St. Louis) — public data",
        "note": "Values are the latest available daily observations (typically the prior trading day). Fields that could not be fetched are null and must be shown as 'unavailable', never as a guessed number.",
        "series": {},
    }

    for key, series_id in SERIES.items():
        date_str, value = fetch_latest(series_id)
        if value is None:
            print(f"  - {key} ({series_id}): UNAVAILABLE")
        else:
            print(f"  - {key} ({series_id}): {value} as of {date_str}")
        out["series"][key] = {
            "fred_id": series_id,
            "value": value,        # float or null
            "as_of": date_str,     # date string or null
        }

    # Compute 1-day changes where we have two consecutive points (best-effort).
    # For simplicity we only store the latest value here; the front-end can
    # display level + as_of. Daily change is left for a future enhancement to
    # avoid fetching full history. We DO NOT fabricate a change figure.

    # Central bank demand: no free real-time series exists. We deliberately do
    # NOT put a number here. The front-end treats this as a qualitative,
    # structural factor per the framework — not a live data point.
    out["central_bank"] = {
        "value": None,
        "as_of": None,
        "note": "No reliable free real-time series for central-bank gold buying (verified: FRED has no clean tonnes series for China). Treated qualitatively as a structural support factor per the framework. Deliberately not a number, to avoid false precision.",
    }

    with open("data/data.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    fetched = sum(1 for s in out["series"].values() if s["value"] is not None)
    total = len(out["series"])
    print(f"Done. {fetched}/{total} series fetched. Wrote data/data.json")

    # Exit non-zero only if we got nothing at all (so the Action surfaces a real failure).
    if fetched == 0:
        print("ERROR: no series could be fetched.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
