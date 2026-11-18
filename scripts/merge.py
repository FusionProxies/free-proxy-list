"""Build the free proxy list without checking it.

Downloads the public lists from update.py's SOURCES (all MIT licensed, see THIRD_PARTY_NOTICES.md),
merges them without duplicates and writes proxies/:

- by protocol (TXT), as JSON and CSV, and by country (TXT);
- which source lists named each proxy, and when it first appeared here;
- the country of each listed IP from the DB-IP Lite database (a lookup, not a test);
- counts per protocol, country and source in proxies/stats.json, shields.io badges and the
  stats block in README.md.

No proxy is connected to: every entry has the status "collected" (listed by a source in the
latest run). To build a checked list instead (working proxies only, with speed, exit country
and anonymity), run scripts/update.py. Field definitions are in docs/SCHEMA.md.

Run: python scripts/merge.py
Env: STATE_DIR (default .cache/ in the repo, ignored by git, never published) holds the monthly
     GeoIP database and history.json (first and last time each proxy was listed);
     HISTORY_HOURS (default 72) keeps proxies that left the sources this long in history.json;
     FORCE=1 publishes even when the sanity checks below would refuse.
"""
from __future__ import annotations

import collections
import csv
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Optional

import geoip
from update import PROTOCOLS, ROOT, SOURCES, download_with_sources

SCHEMA_VERSION = 2
STATUS = "collected"
FIELDS = ["proxy", "protocol", "ip", "port", "status", "country", "sources", "source_count", "first_seen"]
HISTORY_HOURS = int(os.environ.get("HISTORY_HOURS", "72"))
MIN_SOURCES = 3  # fewer lists answering means an outage, not a smaller internet
MIN_RATIO = 0.4  # a list less than 40% of the previous one is a source failure, not churn
TOP_COUNTRIES = 12


def iso(t: datetime) -> str:
    return t.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def source_names() -> list[str]:
    names = []
    for name, _, _ in SOURCES:
        if name not in names:
            names.append(name)
    return names


def read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def refusal(total: int, used: list[str], previous_total: int) -> Optional[str]:
    """Why this run must not replace the published list, or None when it may."""
    if total == 0:
        return "no proxies"
    if len(used) < MIN_SOURCES:
        return f"only {len(used)} of {len(source_names())} source lists answered"
    if previous_total and total < MIN_RATIO * previous_total:
        return f"{total:,} proxies against {previous_total:,} in the previous run"
    return None


def build(proxies: list[str], provenance: dict[str, list[str]], now: datetime,
          history: dict, country_of: Callable[[str], str]) -> tuple[list[dict], dict]:
    """Rows for the outputs, and the history to save for the next run."""
    stamp = iso(now)
    old = history.get("proxies") if isinstance(history.get("proxies"), dict) else {}
    seen = {}
    rows = []
    order = {p: i for i, p in enumerate(proxies)}
    for p in proxies:
        proto, rest = p.split("://", 1)
        ip, port = rest.rsplit(":", 1)
        prev = old.get(p)
        first = prev[0] if isinstance(prev, list) and len(prev) == 3 and parse_iso(prev[0]) else stamp
        runs = prev[2] + 1 if isinstance(prev, list) and len(prev) == 3 and isinstance(prev[2], int) else 1
        seen[p] = [first, stamp, runs]
        srcs = provenance.get(p) or []
        rows.append({
            "proxy": p, "protocol": proto, "ip": ip, "port": int(port), "status": STATUS,
            "country": country_of(ip), "sources": list(srcs), "source_count": len(srcs), "first_seen": first,
        })
    # proxies listed by more sources first; otherwise the order the sources gave
    rows.sort(key=lambda r: (-r["source_count"], order[r["proxy"]]))

    cutoff = now - timedelta(hours=HISTORY_HOURS)
    for p, entry in old.items():
        if p in seen or not (isinstance(entry, list) and len(entry) == 3):
            continue
        last = parse_iso(entry[1])
        if last and last >= cutoff:
            seen[p] = entry  # gone from the sources for now; free proxies often come back
    started = history.get("started_at")
    new_history = {
        "schema_version": 1,
        "started_at": started if parse_iso(started) else stamp,
        "updated_at": stamp,
        "retention_hours": HISTORY_HOURS,
        "proxies": dict(sorted(seen.items())),
    }
    return rows, new_history


def stats(rows: list[dict], used: list[str], now: datetime, previous: set[str],
          db: Optional[geoip.CountryDB], history_started: Optional[str] = None) -> dict:
    per_proto = collections.Counter(r["protocol"] for r in rows)
    per_country = collections.Counter(r["country"] or "XX" for r in rows)
    per_source = {name: {"listed": 0, "only_here": 0} for name in source_names()}
    for r in rows:
        for s in r["sources"]:
            per_source.setdefault(s, {"listed": 0, "only_here": 0})["listed"] += 1
        if r["source_count"] == 1:
            per_source[r["sources"][0]]["only_here"] += 1
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": iso(now),
        "status": STATUS,
        "tested": False,
        "total": len(rows),
        "protocols": {p: per_proto.get(p, 0) for p in PROTOCOLS},
        "countries": dict(sorted(per_country.items(), key=lambda kv: (-kv[1], kv[0]))),
        "sources": per_source,
        "sources_answered": len(used),
        "sources_total": len(source_names()),
        "listed_by_2_or_more": sum(1 for r in rows if r["source_count"] >= 2),
        "new_since_previous_run": sum(1 for r in rows if r["proxy"] not in previous) if previous else None,
        "first_seen_tracked_since": history_started,
        "geoip": {"database": db.label if db else None, "license": geoip.LICENSE if db else None,
                  "located": sum(1 for r in rows if r["country"])},
    }


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")


def badge(out: Path, name: str, label: str, message: str, color: str) -> None:
    data = {"schemaVersion": 1, "label": label, "message": message, "color": color}
    write_lines(out / "badges" / f"{name}.json", [json.dumps(data)])


def readme_block(st: dict, stamp: str) -> str:
    total = st["total"]
    lines = [f"Last update: **{stamp}**. {total:,} proxies from {st['sources_answered']} public lists, merged "
             f"without duplicates. **Collected, not tested:** these are the proxies the sources list, "
             f"not proxies we found working. {st['listed_by_2_or_more']:,} of them are listed by two or more "
             f"sources.", "",
             "| Protocol | Proxies | File |", "|---|---|---|"]
    for p in PROTOCOLS:
        lines.append(f"| {p.upper()} | {st['protocols'][p]:,} | [`proxies/{p}.txt`](proxies/{p}.txt) |")
    lines.append(f"| **All** | **{total:,}** | [`proxies/all.txt`](proxies/all.txt) |")
    countries = [(cc, n) for cc, n in st["countries"].items() if cc != "XX"]
    if countries:
        lines += ["", f"Top countries of the listed IPs (GeoIP lookup, all {len(countries)} in "
                      f"[`proxies/countries/`](proxies/countries)):", "",
                  "| Country | Proxies | File |", "|---|---|---|"]
        for cc, n in countries[:TOP_COUNTRIES]:
            lines.append(f"| {cc} | {n:,} | [`proxies/countries/{cc}.txt`](proxies/countries/{cc}.txt) |")
    lines += ["", "| Source | Listed | Only in this source |", "|---|---|---|"]
    for name, s in st["sources"].items():
        lines.append(f"| [{name}](https://github.com/{name}) | {s['listed']:,} | {s['only_here']:,} |")
    return "\n".join(lines)


def main(root: Path = ROOT, now: Optional[datetime] = None,
         fetch=download_with_sources, load_db=geoip.load) -> None:
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    out = root / "proxies"
    proxies, provenance, used = fetch()
    previous_stats = read_json(out / "stats.json")
    previous_total = previous_stats.get("total") or 0
    if not previous_total:  # first run of this version: fall back to the badge of the old one
        msg = read_json(out / "badges" / "total.json").get("message", "")
        previous_total = int(re.sub(r"\D", "", msg) or 0)
    why = refusal(len(proxies), used, previous_total)
    if why and os.environ.get("FORCE") != "1":
        raise SystemExit(f"not publishing: {why}; keeping the previous list (FORCE=1 overrides)")

    state = Path(os.environ.get("STATE_DIR", root / ".cache"))
    history_path = state / "history.json"
    history = read_json(history_path)
    previous = set()
    if isinstance(history.get("proxies"), dict):
        last_run = history.get("updated_at")
        previous = {p for p, e in history["proxies"].items() if isinstance(e, list) and len(e) == 3 and e[1] == last_run}
    db = load_db(state, now)
    rows, new_history = build(proxies, provenance, now, history, db.lookup if db else (lambda ip: ""))
    st = stats(rows, used, now, previous, db, new_history["started_at"])
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    print(f"merged: {len(rows)} proxies from {len(used)} lists, "
          f"{st['geoip']['located']} located, {len(new_history['proxies'])} in history")

    write_lines(out / "all.txt", [r["proxy"] for r in rows])
    for proto in PROTOCOLS:
        write_lines(out / f"{proto}.txt", [f"{r['ip']}:{r['port']}" for r in rows if r["protocol"] == proto])
    shutil.rmtree(out / "countries", ignore_errors=True)
    by_country = collections.defaultdict(list)
    for r in rows:
        if r["country"]:
            by_country[r["country"]].append(r["proxy"])
    for cc, lines in by_country.items():
        write_lines(out / "countries" / f"{cc}.txt", lines)
    # files only a checked build can fill (see update.py); removed so nothing stale stays online
    shutil.rmtree(out / "anonymity", ignore_errors=True)
    for stale in (out / "https.txt", root / "data" / "anonymity.json", out / "history.json"):
        stale.unlink(missing_ok=True)

    (out / "proxies.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8", newline="\n")
    with open(out / "proxies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({**r, "sources": ";".join(r["sources"])})
    (out / "stats.json").write_text(json.dumps(st, indent=1) + "\n", encoding="utf-8", newline="\n")
    state.mkdir(parents=True, exist_ok=True)
    history_path.write_text(json.dumps(new_history, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")

    badge(out, "total", "proxies", f"{len(rows):,}", "1784f5")
    badge(out, "countries", "countries", str(len(by_country)), "2ea44f")
    badge(out, "updated", "updated", stamp, "14213d")

    readme = root / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!-- stats:start -->.*?<!-- stats:end -->",
                  lambda _: f"<!-- stats:start -->\n{readme_block(st, stamp)}\n<!-- stats:end -->", text, flags=re.S)
    readme.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
