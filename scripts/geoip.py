"""Country of an IPv4 address from the DB-IP "IP to Country Lite" database.

The database is published monthly by DB-IP (https://db-ip.com) under the Creative Commons
Attribution 4.0 International license; see THIRD_PARTY_NOTICES.md. It is downloaded once a
month into a cache directory outside the published files and read with the standard library.

A lookup gives the country the address is registered or announced in. It says nothing about
whether the proxy works, and the traffic can exit somewhere else (a proxy may forward through
another IP), so the result is published as the country of the listed IP, nothing more.
"""
from __future__ import annotations

import bisect
import csv
import gzip
import io
import ipaddress
import os
import urllib.request
from array import array
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

URL = "https://download.db-ip.com/free/dbip-country-lite-{month}.csv.gz"
NAME = "DB-IP IP to Country Lite"
LICENSE = "CC BY 4.0"
UNKNOWN = {"", "ZZ"}  # DB-IP marks reserved and unassigned ranges with ZZ


class CountryDB:
    """IPv4 ranges sorted by start address, looked up with a binary search."""

    def __init__(self, starts: array, ends: array, codes: list[str], label: str = NAME):
        self.starts, self.ends, self.codes, self.label = starts, ends, codes, label

    @classmethod
    def from_rows(cls, rows, label: str = NAME) -> "CountryDB":
        ranges = []
        for row in rows:
            if len(row) < 3 or ":" in row[0]:
                continue  # IPv6 ranges: the merged lists hold IPv4 proxies only
            try:
                start = int(ipaddress.IPv4Address(row[0].strip()))
                end = int(ipaddress.IPv4Address(row[1].strip()))
            except ValueError:
                continue
            code = row[2].strip().upper()
            if start <= end and code not in UNKNOWN:
                ranges.append((start, end, code))
        ranges.sort()
        starts, ends, codes = array("L"), array("L"), []
        for start, end, code in ranges:
            starts.append(start)
            ends.append(end)
            codes.append(code)
        return cls(starts, ends, codes, label)

    @classmethod
    def from_csv_gz(cls, path: Path, label: str = NAME) -> "CountryDB":
        with gzip.open(path, "rt", encoding="utf-8", newline="") as f:
            return cls.from_rows(csv.reader(f), label)

    def __len__(self) -> int:
        return len(self.codes)

    def lookup(self, ip: str) -> str:
        """Two-letter country code of an IPv4 address, or "" when the database does not know it."""
        try:
            n = int(ipaddress.IPv4Address(ip))
        except ValueError:
            return ""
        i = bisect.bisect_right(self.starts, n) - 1
        if i >= 0 and self.starts[i] <= n <= self.ends[i]:
            return self.codes[i]
        return ""


def _months(now: datetime) -> list[str]:
    """This month and the one before: a new month's file appears a few days into the month."""
    prev = (now.year - 1, 12) if now.month == 1 else (now.year, now.month - 1)
    return [f"{now.year:04d}-{now.month:02d}", f"{prev[0]:04d}-{prev[1]:02d}"]


def _download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "FusionProxies/free-proxy-list"})
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(req, timeout=120) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    os.replace(tmp, dest)


def load(cache_dir: Path, now: datetime,
         fetch: Callable[[str, Path], None] = _download) -> Optional[CountryDB]:
    """The newest database available: a cached file when there is one, otherwise a download.

    Returns None when no database can be had; the list is then published without countries
    rather than not at all. Older monthly files are deleted, so the cache holds one file.
    """
    cache_dir.mkdir(parents=True, exist_ok=True)
    for month in _months(now):
        path = cache_dir / f"dbip-country-lite-{month}.csv.gz"
        if not path.exists():
            try:
                fetch(URL.format(month=month), path)
            except Exception as e:  # not published yet, or the site is down: try the previous month
                print(f"geoip: {month} not available ({e})")
                path.with_suffix(path.suffix + ".part").unlink(missing_ok=True)
                continue
        try:
            db = CountryDB.from_csv_gz(path, f"{NAME} {month}")
        except (OSError, EOFError, ValueError, csv.Error) as e:
            print(f"geoip: {path.name} unreadable ({e}), deleting it")
            path.unlink(missing_ok=True)
            continue
        if not len(db):
            print(f"geoip: {path.name} holds no IPv4 ranges, deleting it")
            path.unlink(missing_ok=True)
            continue
        for old in cache_dir.glob("dbip-country-lite-*.csv.gz"):
            if old != path:
                old.unlink(missing_ok=True)
        print(f"geoip: {db.label}, {len(db):,} IPv4 ranges")
        return db
    print("geoip: no database, countries left empty in this run")
    return None


def gzip_rows(rows: list[tuple[str, str, str]]) -> bytes:
    """A gzipped CSV in the DB-IP layout, for tests."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write("".join(f"{a},{b},{c}\n" for a, b, c in rows).encode())
    return buf.getvalue()
