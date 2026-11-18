"""Tests for the collected list (scripts/merge.py, scripts/geoip.py, update.download_with_sources).

No network: the source lists and the GeoIP database are fakes.
Run: python -m unittest discover -s tests -v
"""
import csv
import io
import json
import shutil
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import geoip  # noqa: E402
import merge  # noqa: E402
import update  # noqa: E402

NOW = datetime(2026, 11, 18, 10, 35, tzinfo=timezone.utc)
ALL_SOURCES = ["iplocate/free-proxy-list", "monosans/proxy-list", "ProxyScrape/free-proxy-list",
               "vakhov/fresh-proxy-list", "Zaeem20/FREE_PROXIES_LIST"]

DB_ROWS = [
    ("1.0.0.0", "1.0.0.255", "AU"),
    ("8.8.8.0", "8.8.8.255", "US"),
    ("10.0.0.0", "10.255.255.255", "ZZ"),
    ("2001:db8::", "2001:db8::ffff", "DE"),
    ("45.0.0.0", "45.255.255.255", "IN"),
    ("bad", "row", "XX"),
]


def fake_db() -> geoip.CountryDB:
    return geoip.CountryDB.from_rows([list(r) for r in DB_ROWS], "test db")


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()


class DownloadWithSources(unittest.TestCase):
    def test_merges_dedupes_and_keeps_provenance(self):
        bodies = {
            "iplocate/free-proxy-list/main/all-proxies.txt":
                "http://8.8.8.8:80\nhttps://8.8.8.8:80\nsocks5://1.0.0.1:1080\njunk\nhttp://8.8.8.9:70000\n",
            "monosans/proxy-list/main/proxies/all.txt": "socks5://1.0.0.1:1080\nhttp://45.1.1.1:3128\n",
            "vakhov/fresh-proxy-list/master/http.txt": "8.8.8.8:80\n",
            "vakhov/fresh-proxy-list/master/socks4.txt": "45.1.1.2:4145\n",
        }

        def urlopen(req, timeout=0):
            for suffix, body in bodies.items():
                if req.full_url.endswith(suffix):
                    return FakeResponse(body.encode())
            raise OSError("down")

        with mock.patch.object(update.urllib.request, "urlopen", urlopen), mock.patch("builtins.print"):
            proxies, provenance, used = update.download_with_sources()

        self.assertEqual(proxies, ["http://8.8.8.8:80", "socks5://1.0.0.1:1080", "http://45.1.1.1:3128",
                                   "socks4://45.1.1.2:4145"])
        # "https" in a list is an HTTP proxy that can open HTTPS sites: same entry as http
        self.assertEqual(provenance["http://8.8.8.8:80"], ["iplocate/free-proxy-list", "vakhov/fresh-proxy-list"])
        self.assertEqual(provenance["socks5://1.0.0.1:1080"], ["iplocate/free-proxy-list", "monosans/proxy-list"])
        self.assertEqual(used, ["iplocate/free-proxy-list", "monosans/proxy-list", "vakhov/fresh-proxy-list"])

    def test_download_keeps_its_old_signature(self):
        with mock.patch.object(update, "download_with_sources", return_value=(["http://8.8.8.8:80"], {}, ["a"])):
            self.assertEqual(update.download(), (["http://8.8.8.8:80"], ["a"]))


class CountryLookup(unittest.TestCase):
    def test_lookup(self):
        db = fake_db()
        self.assertEqual(len(db), 3)  # IPv6, ZZ and malformed rows are skipped
        self.assertEqual(db.lookup("1.0.0.0"), "AU")
        self.assertEqual(db.lookup("1.0.0.255"), "AU")
        self.assertEqual(db.lookup("1.0.1.0"), "")
        self.assertEqual(db.lookup("8.8.8.8"), "US")
        self.assertEqual(db.lookup("10.1.2.3"), "")  # ZZ: reserved range
        self.assertEqual(db.lookup("45.200.0.1"), "IN")
        self.assertEqual(db.lookup("255.255.255.255"), "")
        self.assertEqual(db.lookup("not an ip"), "")
        self.assertEqual(db.lookup("0.0.0.0"), "")

    def test_reads_gzipped_csv(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "db.csv.gz"
            path.write_bytes(geoip.gzip_rows(DB_ROWS[:2]))
            db = geoip.CountryDB.from_csv_gz(path)
            self.assertEqual(db.lookup("8.8.8.8"), "US")

    def test_load_uses_cache_and_falls_back_to_previous_month(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d)
            calls = []

            def fetch(url, dest):
                calls.append(url)
                if "2026-11" in url:
                    raise OSError("404 not published yet")
                dest.write_bytes(geoip.gzip_rows(DB_ROWS[:2]))

            with mock.patch("builtins.print"):
                db = geoip.load(cache, NOW, fetch)
                self.assertEqual(db.lookup("8.8.8.8"), "US")
                self.assertIn("2026-10", db.label)
                self.assertEqual(len(calls), 2)
                db = geoip.load(cache, NOW, fetch)  # cached: only this month is tried again
                self.assertEqual(len(calls), 3)
                self.assertEqual([p.name for p in cache.iterdir()], ["dbip-country-lite-2026-10.csv.gz"])

    def test_load_replaces_a_corrupt_file_and_returns_none_without_a_database(self):
        with tempfile.TemporaryDirectory() as d:
            cache = Path(d)
            (cache / "dbip-country-lite-2026-11.csv.gz").write_bytes(b"not gzip")

            def fetch(url, dest):
                raise OSError("offline")

            with mock.patch("builtins.print"):
                self.assertIsNone(geoip.load(cache, NOW, fetch))
            self.assertEqual(list(cache.iterdir()), [])

    def test_january_falls_back_to_december(self):
        self.assertEqual(geoip._months(datetime(2027, 1, 2, tzinfo=timezone.utc)), ["2027-01", "2026-12"])


class Build(unittest.TestCase):
    def test_history_first_seen_runs_and_retention(self):
        earlier = merge.iso(NOW - timedelta(hours=5))
        stale = merge.iso(NOW - timedelta(hours=merge.HISTORY_HOURS + 1))
        history = {"started_at": earlier, "updated_at": merge.iso(NOW - timedelta(minutes=30)), "proxies": {
            "http://8.8.8.8:80": [earlier, earlier, 4],
            "socks5://1.0.0.1:1080": [earlier, merge.iso(NOW - timedelta(hours=2)), 2],  # gone for now, kept
            "socks4://45.9.9.9:4145": [stale, stale, 1],  # gone too long, dropped
            "http://45.1.1.1:3128": "garbage",
        }}
        proxies = ["http://45.1.1.1:3128", "http://8.8.8.8:80"]
        provenance = {"http://8.8.8.8:80": ["a", "b"], "http://45.1.1.1:3128": ["a"]}
        rows, new = merge.build(proxies, provenance, NOW, history, fake_db().lookup)

        self.assertEqual([r["proxy"] for r in rows], ["http://8.8.8.8:80", "http://45.1.1.1:3128"])
        r = rows[0]
        self.assertEqual(list(r), merge.FIELDS)
        self.assertEqual((r["status"], r["country"], r["sources"], r["source_count"], r["first_seen"]),
                         ("collected", "US", ["a", "b"], 2, earlier))
        self.assertEqual(rows[1]["first_seen"], merge.iso(NOW))  # garbage history entry: treated as new
        self.assertEqual(new["proxies"]["http://8.8.8.8:80"], [earlier, merge.iso(NOW), 5])
        self.assertIn("socks5://1.0.0.1:1080", new["proxies"])
        self.assertNotIn("socks4://45.9.9.9:4145", new["proxies"])
        self.assertEqual(new["started_at"], earlier)

    def test_refusal(self):
        five = ALL_SOURCES
        self.assertIsNone(merge.refusal(5000, five, 5300))
        self.assertIsNone(merge.refusal(5000, five, 0))
        self.assertIn("no proxies", merge.refusal(0, five, 5300))
        self.assertIn("2 of 5", merge.refusal(5000, five[:2], 5300))
        self.assertIn("previous run", merge.refusal(1000, five, 5300))


class EndToEnd(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        (self.root / "proxies" / "badges").mkdir(parents=True)
        (self.root / "proxies" / "anonymity").mkdir()
        (self.root / "proxies" / "anonymity" / "elite.txt").write_text("x\n")
        (self.root / "proxies" / "https.txt").write_text("x\n")
        (self.root / "proxies" / "badges" / "total.json").write_text(json.dumps({"message": "5"}))
        (self.root / "README.md").write_text("intro\n<!-- stats:start -->\nold\n<!-- stats:end -->\noutro\n")
        self.proxies = ["http://8.8.8.8:80", "socks5://1.0.0.1:1080", "socks4://45.1.1.2:4145", "http://9.9.9.9:8080"]
        self.provenance = {"http://8.8.8.8:80": ALL_SOURCES[:1], "socks5://1.0.0.1:1080": ALL_SOURCES[:2],
                           "socks4://45.1.1.2:4145": ALL_SOURCES[3:4], "http://9.9.9.9:8080": ALL_SOURCES[4:]}

    def tearDown(self):
        shutil.rmtree(self.root)

    def run_main(self, now, proxies=None, used=ALL_SOURCES):
        proxies = self.proxies if proxies is None else proxies
        fetch = lambda: (proxies, {p: self.provenance[p] for p in proxies}, used)  # noqa: E731
        with mock.patch("builtins.print"):
            merge.main(self.root, now, fetch, lambda cache, now: fake_db())

    def test_outputs_and_schema(self):
        self.run_main(NOW)
        out = self.root / "proxies"
        self.assertEqual((out / "all.txt").read_text().split()[0], "socks5://1.0.0.1:1080")  # 2 sources first
        self.assertEqual(sorted((out / "http.txt").read_text().split()), ["8.8.8.8:80", "9.9.9.9:8080"])
        self.assertEqual((out / "countries" / "US.txt").read_text(), "http://8.8.8.8:80\n")
        self.assertEqual(sorted(p.name for p in (out / "countries").iterdir()), ["AU.txt", "IN.txt", "US.txt"])
        self.assertFalse((out / "anonymity").exists())
        self.assertFalse((out / "https.txt").exists())

        rows = json.loads((out / "proxies.json").read_text())
        self.assertEqual(len(rows), 4)
        self.assertTrue(all(list(r) == merge.FIELDS and r["status"] == "collected" for r in rows))
        with open(out / "proxies.csv", newline="") as f:
            reader = csv.DictReader(f)
            self.assertEqual(reader.fieldnames, merge.FIELDS)
            first = next(reader)
        self.assertEqual(first["sources"], "iplocate/free-proxy-list;monosans/proxy-list")

        st = json.loads((out / "stats.json").read_text())
        self.assertEqual(st["schema_version"], merge.SCHEMA_VERSION)
        self.assertEqual((st["status"], st["tested"], st["total"]), ("collected", False, 4))
        self.assertEqual(st["protocols"], {"http": 2, "socks4": 1, "socks5": 1})
        self.assertEqual(st["countries"], {"AU": 1, "IN": 1, "US": 1, "XX": 1})
        self.assertEqual(st["sources"]["iplocate/free-proxy-list"], {"listed": 2, "only_here": 1})
        self.assertEqual(st["listed_by_2_or_more"], 1)
        self.assertIsNone(st["new_since_previous_run"])
        self.assertEqual(st["geoip"]["located"], 3)
        self.assertEqual(json.loads((out / "badges" / "countries.json").read_text())["message"], "3")

        readme = (self.root / "README.md").read_text()
        self.assertTrue(readme.startswith("intro\n<!-- stats:start -->\nLast update: **2026-11-18 10:35 UTC**"))
        self.assertIn("Collected, not tested", readme)
        self.assertIn("| US | 1 | [`proxies/countries/US.txt`]", readme)
        self.assertTrue(readme.endswith("<!-- stats:end -->\noutro\n"))

    def test_second_run_tracks_new_proxies(self):
        self.run_main(NOW)
        later = NOW + timedelta(minutes=30)
        self.run_main(later, proxies=self.proxies[:3])
        st = json.loads((self.root / "proxies" / "stats.json").read_text())
        self.assertEqual(st["new_since_previous_run"], 0)
        self.assertEqual(st["first_seen_tracked_since"], merge.iso(NOW))
        rows = {r["proxy"]: r for r in json.loads((self.root / "proxies" / "proxies.json").read_text())}
        self.assertEqual(rows["http://8.8.8.8:80"]["first_seen"], merge.iso(NOW))
        history = json.loads((self.root / ".cache" / "history.json").read_text())
        self.assertFalse((self.root / "proxies" / "history.json").exists())  # never published
        self.assertEqual(history["proxies"]["http://9.9.9.9:8080"][1], merge.iso(NOW))  # left, still in history
        self.assertEqual(history["proxies"]["http://8.8.8.8:80"][2], 2)

    def test_refuses_a_collapsed_list_and_keeps_the_previous_files(self):
        self.run_main(NOW)
        before = (self.root / "proxies" / "all.txt").read_text()
        with self.assertRaises(SystemExit) as e:
            self.run_main(NOW + timedelta(minutes=30), proxies=self.proxies[:1])
        self.assertIn("not publishing", str(e.exception))
        self.assertEqual((self.root / "proxies" / "all.txt").read_text(), before)
        with mock.patch.dict("os.environ", {"FORCE": "1"}):
            self.run_main(NOW + timedelta(minutes=30), proxies=self.proxies[:1])
        self.assertEqual((self.root / "proxies" / "all.txt").read_text(), "http://8.8.8.8:80\n")

    def test_publishes_without_a_geoip_database(self):
        fetch = lambda: (self.proxies, self.provenance, ALL_SOURCES)  # noqa: E731
        with mock.patch("builtins.print"):
            merge.main(self.root, NOW, fetch, lambda cache, now: None)
        st = json.loads((self.root / "proxies" / "stats.json").read_text())
        self.assertEqual((st["total"], st["geoip"]["located"], st["geoip"]["database"]), (4, 0, None))
        self.assertFalse((self.root / "proxies" / "countries").exists())


if __name__ == "__main__":
    unittest.main()
