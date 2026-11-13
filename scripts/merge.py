"""Build the free proxy list without checking it.

Downloads the public lists from update.py's SOURCES (all MIT licensed, see THIRD_PARTY_NOTICES.md),
merges them without duplicates and writes proxies/ by protocol, plus JSON, CSV, shields.io badges
and the stats block in README.md. No proxy is connected to: they are published as the sources list them.
To build a checked list instead (working proxies only, with speed, country and anonymity), run scripts/update.py.

Run: python scripts/merge.py
"""
import collections
import csv
import json
import re
import shutil
from datetime import datetime, timezone

from update import OUT, PROTOCOLS, ROOT, badge, download, write_lines


def main() -> None:
    proxies, used = download()
    if not proxies:
        raise SystemExit("no proxies, keeping the previous list")
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    rows = []
    for p in proxies:
        proto, rest = p.split("://", 1)
        ip, port = rest.rsplit(":", 1)
        rows.append({"proxy": p, "protocol": proto, "ip": ip, "port": int(port)})
    print(f"merged: {len(rows)} proxies from {len(used)} lists")

    write_lines(OUT / "all.txt", proxies)
    for proto in PROTOCOLS:
        write_lines(OUT / f"{proto}.txt", [f"{r['ip']}:{r['port']}" for r in rows if r["protocol"] == proto])
    # files only a checked build can fill (see update.py); removed so nothing stale stays online
    for stale in ("anonymity", "countries"):
        shutil.rmtree(OUT / stale, ignore_errors=True)
    for stale in (OUT / "https.txt", OUT / "badges" / "countries.json", ROOT / "data" / "anonymity.json"):
        stale.unlink(missing_ok=True)
    (OUT / "proxies.json").write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8", newline="\n")
    with open(OUT / "proxies.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    per_proto = collections.Counter(r["protocol"] for r in rows)
    badge("total", "proxies", f"{len(rows):,}", "1784f5")
    badge("updated", "updated", stamp, "14213d")

    table = ["| Protocol | Proxies | File |", "|---|---|---|"]
    for proto in PROTOCOLS:
        table.append(f"| {proto.upper()} | {per_proto.get(proto, 0):,} | [`proxies/{proto}.txt`](proxies/{proto}.txt) |")
    table.append(f"| **All** | **{len(rows):,}** | [`proxies/all.txt`](proxies/all.txt) |")
    block = (f"Last update: **{stamp}**. {len(rows):,} proxies from {len(used)} public lists, "
             f"merged without duplicates (not re-checked here).\n\n" + "\n".join(table))
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    text = re.sub(r"<!-- stats:start -->.*?<!-- stats:end -->", f"<!-- stats:start -->\n{block}\n<!-- stats:end -->", text, flags=re.S)
    readme.write_text(text, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
