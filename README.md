<p align="center">
  <a href="https://fusionproxy.net/?utm_source=github&utm_medium=referral&utm_campaign=free-proxy-list">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-dark.png">
      <img src="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-light.png" alt="Fusion Proxy" height="52">
    </picture>
  </a>
</p>

# Free Proxy List: HTTP, SOCKS4 and SOCKS5 proxies, updated every 30 minutes

A free proxy list of HTTP, SOCKS4 and SOCKS5 proxies, merged from five public lists **every 30 minutes** and published without duplicates as TXT, JSON and CSV, also split by country. Every entry says which source lists named it, the country of its IP address and when it first appeared here.

The proxies are **collected, not tested**: this job never connects to them. Free proxies come and go within hours, so check the ones you need before you use them (see [What "collected" means](#collected-tested-reachable-verified-what-the-words-mean-here)).

[![Proxies](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Ftotal.json)](proxies/all.txt)
[![Updated](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Fupdated.json)](https://github.com/FusionProxies/free-proxy-list/commits/main)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

If this list saves you time, a ⭐ helps other developers find it.

## Current list

<!-- stats:start -->
Last update: **2026-11-18 11:05 UTC**. 5,685 proxies from 5 public lists, merged without duplicates (not re-checked here).

| Protocol | Proxies | File |
|---|---|---|
| HTTP | 2,681 | [`proxies/http.txt`](proxies/http.txt) |
| SOCKS4 | 691 | [`proxies/socks4.txt`](proxies/socks4.txt) |
| SOCKS5 | 2,313 | [`proxies/socks5.txt`](proxies/socks5.txt) |
| **All** | **5,685** | [`proxies/all.txt`](proxies/all.txt) |
<!-- stats:end -->

## Download the free proxy list (TXT, JSON, CSV)

| File | Format | Direct link |
|---|---|---|
| All proxies | `scheme://ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/all.txt |
| HTTP | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/http.txt |
| SOCKS4 | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/socks4.txt |
| SOCKS5 | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/socks5.txt |
| All proxies | JSON | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/proxies.json |
| All proxies | CSV | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/proxies.csv |
| One country | `scheme://ip:port` | `https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/countries/US.txt` (any [two-letter code](proxies/countries)) |
| Counts per protocol, country and source | JSON | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/stats.json |

The same files are on the jsDelivr CDN: replace `https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/` with `https://cdn.jsdelivr.net/gh/FusionProxies/free-proxy-list@main/`.

### Fields

Each JSON and CSV row has these fields (full definitions and the versioning rules in [docs/SCHEMA.md](docs/SCHEMA.md)):

| Field | Example | Meaning |
|---|---|---|
| `proxy` | `socks5://1.2.3.4:1080` | scheme, IP and port |
| `protocol` | `socks5` | `http`, `socks4` or `socks5` |
| `ip`, `port` | `1.2.3.4`, `1080` | |
| `status` | `collected` | always `collected` here: listed by a source in the latest run, not tested |
| `country` | `US` | country of the listed IP in the DB-IP Lite database; empty when unknown |
| `sources` | `["monosans/proxy-list"]` | the source lists that named it (`;`-separated in the CSV) |
| `source_count` | `1` | how many of them |
| `first_seen` | `2026-11-18T10:35:00Z` | first run that listed it, counted from `first_seen_tracked_since` in `stats.json` |

Rows listed by more sources come first. That is not a quality rating: several lists often copy each other.

## How to use a free proxy list (cURL and Python)

```bash
# fetch the SOCKS5 list and try the first proxy
curl -s https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/socks5.txt | head -1 \
  | xargs -I{} curl -s --max-time 15 -x socks5h://{} https://ipinfo.io/json
```

```python
import random
import requests

url = "https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/http.txt"
proxies = requests.get(url, timeout=30).text.split()

for proxy in random.sample(proxies, 5):
    try:
        r = requests.get("https://ipinfo.io/json", proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, timeout=10)
        print(proxy, r.json()["country"])
        break
    except requests.RequestException:
        print(proxy, "failed, trying the next one")
```

```python
# SOCKS5 proxies in Germany that at least two sources list
import requests

rows = requests.get("https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/proxies.json", timeout=30).json()
picked = [r["proxy"] for r in rows if r["protocol"] == "socks5" and r["country"] == "DE" and r["source_count"] >= 2]
print(len(picked), picked[:5])
```

To check proxies yourself, use [proxy-checker](https://github.com/FusionProxies/proxy-checker) (command line) or the [online proxy checker](https://fusionproxy.net/tools/proxy-checker?utm_source=github&utm_medium=referral&utm_campaign=free-proxy-list).

## Collected, tested, reachable, verified: what the words mean here

| Word | Meaning | In this repo |
|---|---|---|
| **Collected** | A source list named the proxy in the latest run. Nobody here connected to it. | Every file in `proxies/` |
| **Tested** | Someone tried to connect through the proxy at a known time. | Only when you run `scripts/update.py` yourself |
| **Reachable** | The proxy accepted the connection and answered its protocol (HTTP CONNECT, SOCKS4 or SOCKS5). | Only when you run `scripts/update.py` yourself |
| **Verified** | A full request through the proxy to a test page came back correct. "Recently verified" means within the last hour or so, because free proxies die fast. | Only when you run `scripts/update.py` yourself |

A proxy being in this list says nothing about whether it works right now. The sources check their proxies in their own ways and at their own times; we do not repeat or vouch for those checks.

## How the list is built

1. Every 30 minutes a job downloads the lists of five public sources (see [Sources](#sources)) and merges them without duplicates (`scripts/merge.py`). It runs on our own server, not on GitHub Actions. The time of the last update is at the top of the list.
2. Lists often call an HTTP proxy that can open HTTPS sites an "HTTPS proxy"; those are in `http.txt`.
3. Each entry keeps the names of the source lists that listed it and the time it was first listed. The job keeps that history on the server, not in this repo (entries gone for more than 72 hours are dropped).
4. The country is looked up in the free [DB-IP](https://db-ip.com) IP to Country Lite database, downloaded once a month. It is the country of the **listed** IP address. The traffic can leave from somewhere else, because a proxy can forward through another IP, and the database can be wrong.
5. If fewer than three sources answer, or the list shrinks to less than 40% of the previous run, the job keeps the previous list instead of publishing a broken one.
6. The proxies are not connected to or tested here. To build a checked list yourself (working proxies only, sorted by speed, with exit country and anonymity level), run `scripts/update.py` with [proxy-checker](https://github.com/FusionProxies/proxy-checker) installed.

Free proxies come and go within hours, so expect a part of the list to fail by the time you use it.

## Limitations

- **Not tested.** See above. Expect most entries to fail at any given moment; that is normal for public proxies.
- **Country = the listed IP.** It comes from a database lookup, not from a request through the proxy.
- **IPv4 only.** The sources publish IPv4 addresses; lines in other formats are skipped.
- **Duplicates across ports.** One machine often appears with many ports, so 1,000 entries can be far fewer machines.
- **`first_seen` starts with this version of the job.** Proxies listed before that show the start date (`first_seen_tracked_since` in `stats.json`).

## Elite, anonymous and transparent proxies

| Level | Your real IP | The site can tell a proxy is used |
|---|---|---|
| **Elite** (high anonymity) | Hidden | No |
| **Anonymous** | Hidden | Yes, from headers such as `Via` or `X-Forwarded-For` |
| **Transparent** | **Visible** | Yes |

A transparent proxy tells every plain-HTTP website the IP address of whoever uses it, so it hides nothing. Many public lists still publish them as anonymous, and this list does not label them. The level only matters for plain `http://` sites: inside an `https://` connection the proxy cannot add headers. SOCKS proxies relay the connection without adding headers, so they come out elite unless they forward through another proxy.

To test any proxy yourself, use [proxy-anonymity-test](https://github.com/FusionProxies/proxy-anonymity-test).

## Are free proxies safe?

Public proxies are run by unknown people. Treat everything you send through them as visible to the operator:

- never log in to accounts or send passwords, cookies or payment details through them;
- prefer HTTPS sites, and use `socks5h://` so DNS is resolved on the proxy side;
- expect slow answers, frequent timeouts and IPs that many sites already block.

For logins, scraping at scale or anything that has to keep working, use proxies with a known source. [Fusion Proxy residential proxies](https://fusionproxy.net/proxies/residential?utm_source=github&utm_medium=referral&utm_campaign=free-proxy-list) give you real household IPs in the country, state or city you choose, with rotating or sticky sessions, from $2.95/GB and down to $0.65/GB at volume. [Try it free](https://fusionproxy.net/free-trial?utm_source=github&utm_medium=referral&utm_campaign=free-proxy-list).

## Sources

The proxies come from these public lists, all MIT licensed:

- [iplocate/free-proxy-list](https://github.com/iplocate/free-proxy-list)
- [monosans/proxy-list](https://github.com/monosans/proxy-list)
- [ProxyScrape/free-proxy-list](https://github.com/ProxyScrape/free-proxy-list)
- [vakhov/fresh-proxy-list](https://github.com/vakhov/fresh-proxy-list)
- [Zaeem20/FREE_PROXIES_LIST](https://github.com/Zaeem20/FREE_PROXIES_LIST)

Countries: [IP Geolocation by DB-IP](https://db-ip.com), IP to Country Lite database, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Their licenses are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

The scripts and the published lists are MIT licensed, see [LICENSE](LICENSE). The `country` values come from the DB-IP IP to Country Lite database and stay under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): keep the line "IP Geolocation by DB-IP" with a link to https://db-ip.com when you republish them.
