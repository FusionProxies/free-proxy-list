"""Build the free proxy list.

1. Download candidate proxies from the public lists below (all MIT licensed, see THIRD_PARTY_NOTICES.md)
   and merge them without duplicates.
2. Check every candidate with proxy-checker (github.com/FusionProxies/proxy-checker).
3. Keep the ones that work and write them to proxies/ by protocol and country,
   plus JSON, CSV, shields.io badges and the stats block in README.md.
4. Label every working proxy elite, anonymous or transparent with a plain-HTTP request
   to a judge that echoes the headers back (each proxy at most once a day, cache in data/).

Run: python scripts/update.py   (proxy-checker must be on PATH, or set PROXY_CHECKER)
"""
import collections
import concurrent.futures
import csv
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "proxies"
CHECKER = os.environ.get("PROXY_CHECKER", "proxy-checker")
WORKERS = os.environ.get("CHECK_WORKERS", "500")  # proxies checked at once; lower spreads the connections over the run
TARGET = "https://www.cloudflare.com/cdn-cgi/trace"
JUDGE = "http://httpbin.org/get"  # plain HTTP on purpose: inside an HTTPS tunnel a proxy cannot add headers
CACHE = ROOT / "data" / "anonymity.json"
LEVELS = ["elite", "anonymous", "transparent"]
# headers that proxies add and that give them away (as in github.com/FusionProxies/proxy-anonymity-test)
PROXY_HEADERS = ["Via", "X-Forwarded-For", "Forwarded", "X-Real-Ip", "X-Proxy-Id", "Proxy-Connection",
                 "X-Forwarded-Host", "X-Forwarded-Proto", "Client-Ip", "X-Client-Ip", "X-Originating-Ip",
                 "Cache-Control-Proxy"]
RETEST_HOURS = {"unknown": 1}  # a known level is tested again after 24 hours
JUDGE_BUDGET = 300  # seconds per run; proxies not reached are tested in the next runs
IPV4 = re.compile(r"\d{1,3}(?:\.\d{1,3}){3}")
UNKNOWN_WHY = collections.Counter()  # why a test gave no answer, printed in the job log
# "https" in public lists means an HTTP proxy that can open HTTPS sites (CONNECT), so it is checked as http
PROTOCOLS = ["http", "socks4", "socks5"]

GH = "https://raw.githubusercontent.com/"
SOURCES = [
    # name, url, scheme for lines that are only ip:port (None: every line carries its own scheme)
    ("iplocate/free-proxy-list", GH + "iplocate/free-proxy-list/main/all-proxies.txt", None),
    ("monosans/proxy-list", GH + "monosans/proxy-list/main/proxies/all.txt", None),
    ("ProxyScrape/free-proxy-list", GH + "ProxyScrape/free-proxy-list/main/proxies/all/data.txt", None),
    ("vakhov/fresh-proxy-list", GH + "vakhov/fresh-proxy-list/master/http.txt", "http"),
    ("vakhov/fresh-proxy-list", GH + "vakhov/fresh-proxy-list/master/https.txt", "http"),
    ("vakhov/fresh-proxy-list", GH + "vakhov/fresh-proxy-list/master/socks4.txt", "socks4"),
    ("vakhov/fresh-proxy-list", GH + "vakhov/fresh-proxy-list/master/socks5.txt", "socks5"),
    ("Zaeem20/FREE_PROXIES_LIST", GH + "Zaeem20/FREE_PROXIES_LIST/master/http.txt", "http"),
    ("Zaeem20/FREE_PROXIES_LIST", GH + "Zaeem20/FREE_PROXIES_LIST/master/https.txt", "http"),
    ("Zaeem20/FREE_PROXIES_LIST", GH + "Zaeem20/FREE_PROXIES_LIST/master/socks4.txt", "socks4"),
    ("Zaeem20/FREE_PROXIES_LIST", GH + "Zaeem20/FREE_PROXIES_LIST/master/socks5.txt", "socks5"),
]

# Cloudflare marks Tor exits as T1; XX means unknown
COUNTRY_ALIAS = {"T1": "TOR", "": "XX"}

LINE = re.compile(r"^(?:(https?|socks4|socks5)://)?(\d{1,3}(?:\.\d{1,3}){3}):(\d{1,5})$")


def download() -> tuple[list[str], list[str]]:
    """Return the merged candidates without duplicates, and the names of the lists that answered."""
    seen, out, used = set(), [], []
    for name, url, default in SOURCES:
        req = urllib.request.Request(url, headers={"User-Agent": "FusionProxies/free-proxy-list"})
        try:
            text = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", "replace")
        except Exception as e:  # one dead source must not stop the update
            print(f"source {url} failed: {e}")
            continue
        n = 0
        for line in text.splitlines():
            m = LINE.match(line.strip())
            if not m or not 0 < int(m.group(3)) < 65536:
                continue
            scheme = m.group(1) or default
            if scheme is None:
                continue
            if scheme == "https":
                scheme = "http"
            key = (scheme, m.group(2), int(m.group(3)))
            if key not in seen:
                seen.add(key)
                out.append(f"{key[0]}://{key[1]}:{key[2]}")
                n += 1
        if name not in used:
            used.append(name)
        print(f"source {url}: {n} new candidates")
    return out, used


def check(candidates: list[str]) -> list[dict]:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write("\n".join(candidates))
        path = f.name
    try:
        run = subprocess.run([CHECKER, "-f", path, "-c", WORKERS, "-t", "10s", "-target", TARGET, "-o", "json"],
                             capture_output=True, text=True, timeout=1800)
    finally:
        os.unlink(path)
    if not run.stdout.strip():
        raise SystemExit("proxy-checker returned nothing: " + run.stderr[-500:])
    return json.loads(run.stdout)


def real_ips() -> set[str]:
    """Public IPs of this machine, to catch proxies that pass them on to the website."""
    ips = set()
    for url in ("https://api.ipify.org", "https://api64.ipify.org"):
        try:
            ips.add(urllib.request.urlopen(url, timeout=15).read().decode().strip())
        except Exception:
            pass
    return {ip for ip in ips if ip}


def judge(proxy: str, mine: set[str]) -> str:
    import requests  # the workflow installs requests[socks]

    url = proxy.replace("socks5://", "socks5h://", 1)
    try:
        for attempt in range(2):
            r = requests.get(JUDGE, proxies={"http": url, "https": url}, timeout=10,
                             headers={"User-Agent": "FusionProxies/free-proxy-list"})
            if r.status_code != 429 or attempt:
                break
            time.sleep(10)  # rate limited: wait once and try again
        if r.status_code != 200:
            UNKNOWN_WHY[f"HTTP {r.status_code}"] += 1
            return "unknown"
        data = r.json()
        headers = {str(k).title(): str(v) for k, v in (data.get("headers") or {}).items()}
        seen = " ".join([str(data.get("origin", ""))] + list(headers.values()))
    except Exception as e:
        UNKNOWN_WHY[type(e).__name__] += 1
        return "unknown"
    found = set(IPV4.findall(seen))
    if any(ip in found if "." in ip else ip.lower() in seen.lower() for ip in mine):
        return "transparent"  # the website sees the real IP of whoever uses the proxy
    if any(h.title() in headers for h in PROXY_HEADERS):
        return "anonymous"  # the real IP is hidden, but the headers show that a proxy is used
    return "elite"


def label_anonymity(alive: list[dict], now: datetime) -> None:
    """Add "anonymity" to every working proxy, testing each one at most once a day."""
    try:
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        cache = {}

    def fresh(entry: dict) -> bool:
        try:
            age = now - datetime.fromisoformat(entry["checked_at"].replace("Z", "+00:00"))
        except (KeyError, AttributeError, TypeError, ValueError):
            return False
        return age.total_seconds() < RETEST_HOURS.get(entry.get("level"), 24) * 3600

    todo = [a for a in alive if not fresh(cache.get(a["proxy"]) or {})]
    mine = real_ips() if todo else set()
    if todo and not mine:
        print("anonymity: own IP unknown, test skipped")
    elif todo:
        # many free proxies are ports of one machine; the judge rate-limits per IP, so each exit IP goes one at a time
        groups = collections.defaultdict(list)
        for a in todo:
            groups[a["exit_ip"] or a["ip"]].append(a["proxy"])

        deadline = time.monotonic() + JUDGE_BUDGET

        def run(group: list[str]) -> list[tuple[str, str]]:
            out = []
            for x in group:
                if time.monotonic() > deadline:
                    break
                out.append((x, judge(x, mine)))
            return out

        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as pool:
            done = [r for g in pool.map(run, sorted(groups.values(), key=len, reverse=True)) for r in g]
        if len(done) < len(todo):
            print(f"anonymity: time budget used, {len(todo) - len(done)} left for the next runs")
        todo = [x for x, _ in done]
        levels = [lvl for _, lvl in done]
        print(f"anonymity: tested {len(todo)}: " + ", ".join(f"{levels.count(x)} {x}" for x in LEVELS + ["unknown"]))
        if UNKNOWN_WHY:
            print("anonymity: no answer because " + ", ".join(f"{k} {n}" for k, n in UNKNOWN_WHY.most_common()))
        if len(levels) >= 20 and levels.count("unknown") > 0.9 * len(levels):
            print("anonymity: the judge looks down, results not saved")
        else:
            stamp = now.isoformat().replace("+00:00", "Z")
            for proxy, level in zip(todo, levels):
                cache[proxy] = {"level": level, "checked_at": stamp}
    for a in alive:
        a["anonymity"] = (cache.get(a["proxy"]) or {}).get("level", "unknown")
    # keep results until they are due again: free proxies drop out of one run and come back in the next
    cache = {k: v for k, v in cache.items() if fresh(v)}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")


def badge(name: str, label: str, message: str, color: str) -> None:
    (OUT / "badges").mkdir(parents=True, exist_ok=True)
    data = {"schemaVersion": 1, "label": label, "message": message, "color": color}
    (OUT / "badges" / f"{name}.json").write_text(json.dumps(data) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    candidates, used = download()
    if not candidates:
        raise SystemExit("no candidates, keeping the previous list")
    results = check(candidates)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")

    alive = []
    for r in results:
        if not r.get("ok"):
            continue
        proto, rest = r["proxy"].split("://", 1)
        ip, port = rest.rsplit(":", 1)
        alive.append({
            "proxy": r["proxy"], "protocol": proto, "ip": ip, "port": int(port),
            "exit_ip": r.get("ip", ""), "country": COUNTRY_ALIAS.get(r.get("country", ""), r.get("country", "") or "XX"),
            "latency_ms": r.get("latency_ms", 0), "checked_at": now.isoformat().replace("+00:00", "Z"),
        })
    alive.sort(key=lambda x: x["latency_ms"])
    print(f"working: {len(alive)} of {len(candidates)}")
    if not alive:
        raise SystemExit("no working proxies, keeping the previous list")
    label_anonymity(alive, now)

    # files: all, by protocol, by country
    write_lines(OUT / "all.txt", [a["proxy"] for a in alive])
    for p in PROTOCOLS:
        write_lines(OUT / f"{p}.txt", [f"{a['ip']}:{a['port']}" for a in alive if a["protocol"] == p])
    # every HTTP proxy here passed an HTTPS request (CONNECT), so https.txt holds the same proxies
    write_lines(OUT / "https.txt", [f"{a['ip']}:{a['port']}" for a in alive if a["protocol"] == "http"])
    for level in LEVELS:
        write_lines(OUT / "anonymity" / f"{level}.txt", [a["proxy"] for a in alive if a["anonymity"] == level])
    for old in (OUT / "countries").glob("*.txt"):
        old.unlink()
    by_country = collections.defaultdict(list)
    for a in alive:
        by_country[a["country"]].append(a["proxy"])
    for cc, lines in by_country.items():
        write_lines(OUT / "countries" / f"{cc}.txt", lines)
    (OUT / "proxies.json").write_text(json.dumps(alive, indent=1) + "\n", encoding="utf-8", newline="\n")
    with open(OUT / "proxies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(alive[0].keys()))
        w.writeheader()
        w.writerows(alive)

    # badges and README stats
    per_proto = collections.Counter(a["protocol"] for a in alive)
    badge("total", "working proxies", f"{len(alive):,}", "1784f5")
    badge("countries", "countries", str(len(by_country)), "2ea44f")
    badge("updated", "updated", stamp, "14213d")

    rows = ["| Protocol | Working | File |", "|---|---|---|"]
    for p in PROTOCOLS:
        rows.append(f"| {p.upper()} | {per_proto.get(p, 0):,} | [`proxies/{p}.txt`](proxies/{p}.txt) |")
        if p == "http":
            rows.append(f"| HTTPS (the HTTP proxies, all passed an HTTPS request) | {per_proto.get(p, 0):,} "
                        f"| [`proxies/https.txt`](proxies/https.txt) |")
    rows.append(f"| **All** | **{len(alive):,}** | [`proxies/all.txt`](proxies/all.txt) |")
    per_level = collections.Counter(a["anonymity"] for a in alive)
    arow = ["| Anonymity | Working | File |", "|---|---|---|",
            f"| Elite (no proxy headers) | {per_level['elite']:,} | [`proxies/anonymity/elite.txt`](proxies/anonymity/elite.txt) |",
            f"| Anonymous (your IP hidden, proxy visible) | {per_level['anonymous']:,} "
            f"| [`proxies/anonymity/anonymous.txt`](proxies/anonymity/anonymous.txt) |",
            f"| Transparent (your IP visible on HTTP sites) | {per_level['transparent']:,} "
            f"| [`proxies/anonymity/transparent.txt`](proxies/anonymity/transparent.txt) |"]
    if per_level["unknown"]:
        arow.append(f"| Not labelled yet | {per_level['unknown']:,} | |")
    top = collections.Counter({cc: len(v) for cc, v in by_country.items()}).most_common(12)
    crow = ["| Country | Working | File |", "|---|---|---|"]
    for cc, n in top:
        crow.append(f"| {cc} | {n:,} | [`proxies/countries/{cc}.txt`](proxies/countries/{cc}.txt) |")
    block = (
        f"Last update: **{stamp}**. {len(alive):,} of {len(candidates):,} candidates from {len(used)} public lists "
        f"passed the check ({len(by_country)} countries).\n\n" + "\n".join(rows) + "\n\n"
        + "\n".join(arow) + "\n\n"
        f"Top countries (all {len(by_country)} are in [`proxies/countries/`](proxies/countries)):\n\n" + "\n".join(crow)
    )
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!-- stats:start -->.*?<!-- stats:end -->", f"<!-- stats:start -->\n{block}\n<!-- stats:end -->", text, flags=re.S)
    readme.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
