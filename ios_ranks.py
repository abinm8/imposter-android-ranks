#!/usr/bin/env python3
"""iPhone chart tracker for Imposter Game: Malayalam Party.

Reads Apple's Top Free iPhone chart for the Word games genre in each country,
finds the app's position, and saves:
  ios_ranks_readings.json  every reading (time, date, code, rank), last 90 days
  ios_ranks.json           one row per day per country (latest + best rank of
                           the day, plus ratings count) - read by the dashboard
"""
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

APP_ID = "6773430796"
GENRE = "7019"  # Games > Word
TZ = ZoneInfo("America/Chicago")  # same "day" as the dashboard
KEEP_DAYS = 90

# (name, App Store code, market). Add more rows here to track more countries.
COUNTRIES = [
    ("India", "in", "Home"),
    ("UAE", "ae", "Gulf"), ("Saudi Arabia", "sa", "Gulf"), ("Qatar", "qa", "Gulf"),
    ("Kuwait", "kw", "Gulf"), ("Oman", "om", "Gulf"), ("Bahrain", "bh", "Gulf"),
    ("United States", "us", "Diaspora"), ("United Kingdom", "gb", "Diaspora"),
    ("Canada", "ca", "Diaspora"), ("Australia", "au", "Diaspora"),
    ("New Zealand", "nz", "Diaspora"), ("Ireland", "ie", "Diaspora"),
    ("Singapore", "sg", "Diaspora"), ("Malaysia", "my", "Diaspora"),
    ("Germany", "de", "Diaspora"),
    # Countries where Toplify has seen the app chart
    ("Sri Lanka", "lk", "Other"), ("Afghanistan", "af", "Other"),
    ("Belize", "bz", "Other"), ("Malta", "mt", "Other"), ("Latvia", "lv", "Other"),
    ("Austria", "at", "Other"), ("Armenia", "am", "Other"),
]

UA = {"User-Agent": "Mozilla/5.0 (rank-tracker; +https://github.com/abinm8)"}


def get_json(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except (urllib.error.URLError, json.JSONDecodeError, TimeoutError) as e:
            last = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(f"{url}: {last}")


def chart_rank(code):
    """Return (rank or None, chart length). Raises if the chart can't be read."""
    err = None
    for limit in (200, 100):
        url = (f"https://itunes.apple.com/{code}/rss/topfreeapplications/"
               f"limit={limit}/genre={GENRE}/json")
        try:
            data = get_json(url)
        except RuntimeError as e:
            err = e
            continue
        entries = data.get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        for i, e in enumerate(entries, 1):
            if e.get("id", {}).get("attributes", {}).get("im:id") == APP_ID:
                return i, len(entries)
        return None, len(entries)
    raise RuntimeError(str(err))


def ratings_count(code):
    try:
        d = get_json(f"https://itunes.apple.com/lookup?id={APP_ID}&country={code}")
        res = d.get("results") or []
        return int(res[0].get("userRatingCount", 0)) if res else 0
    except Exception:
        return None


def load(path, default):
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def main():
    now = datetime.now(timezone.utc)
    today = now.astimezone(TZ).date().isoformat()
    stamp = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")

    readings = load("ios_ranks_readings.json", [])
    daily = load("ios_ranks.json", [])
    meta = {c: (n, r) for n, c, r in COUNTRIES}
    ratings = {}
    ok = 0

    for name, code, region in COUNTRIES:
        try:
            rank, n = chart_rank(code)
            readings.append({"time": stamp, "date": today, "code": code, "rank": rank})
            ok += 1
            print(f"{code}: {'#' + str(rank) if rank else '-'} (chart has {n})")
        except RuntimeError as e:
            print(f"{code}: FAILED {e}", file=sys.stderr)
        ratings[code] = ratings_count(code)
        time.sleep(1)

    cutoff = (now - timedelta(days=KEEP_DAYS)).astimezone(TZ).date().isoformat()
    readings = [r for r in readings if r["date"] >= cutoff]

    # Rebuild today's daily rows from today's readings.
    todays = [r for r in readings if r["date"] == today]
    rows = {(d["date"], d["code"]): d for d in daily}
    for code in {r["code"] for r in todays}:
        rs = sorted((r for r in todays if r["code"] == code), key=lambda r: r["time"])
        ranks = [r["rank"] for r in rs if r["rank"] is not None]
        name, region = meta.get(code, (code, "Other"))
        prev = rows.get((today, code), {})
        rows[(today, code)] = {
            "date": today, "store": "App Store", "country": name, "code": code,
            "region": region,
            "rank": rs[-1]["rank"],            # latest reading of the day
            "best_rank": min(ranks) if ranks else None,
            "readings": len(rs),
            "ratings": ratings.get(code) if ratings.get(code) is not None
                       else prev.get("ratings", 0),
            "updated": stamp,
        }
    daily = sorted(rows.values(), key=lambda d: (d["date"], d["code"]))

    with open("ios_ranks_readings.json", "w") as f:
        json.dump(readings, f, indent=0)
    with open("ios_ranks.json", "w") as f:
        json.dump(daily, f, indent=1)

    print(f"{ok}/{len(COUNTRIES)} charts read at {stamp}")
    if ok == 0:
        sys.exit("No chart could be read - Apple's feed may be down or blocked.")


if __name__ == "__main__":
    main()
