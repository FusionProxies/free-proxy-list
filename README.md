<p align="center">
  <a href="https://fusionproxy.net/?utm_source=github&utm_medium=free-proxy-list">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-dark.png">
      <img src="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-light.png" alt="Fusion Proxy" height="52">
    </picture>
  </a>
</p>

# Free Proxy List: HTTP, SOCKS4 and SOCKS5 proxies, updated every 30 minutes

A free proxy list of HTTP, HTTPS, SOCKS4 and SOCKS5 proxies, merged from five public lists and **re-checked every 30 minutes**. Only proxies that answered the check are published, sorted from fastest to slowest, with their country, response time and anonymity level: **elite**, **anonymous** or **transparent** (the ones that pass your real IP on to the website).

[![Working proxies](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Ftotal.json)](proxies/all.txt)
[![Countries](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Fcountries.json)](proxies/countries)
[![Updated](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Fupdated.json)](https://github.com/FusionProxies/free-proxy-list/commits/main)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

If this list saves you time, a ⭐ helps other developers find it.

## Current list

<!-- stats:start -->
Last update: **2026-11-12 11:44 UTC**. 1,580 of 6,384 candidates from 5 public lists passed the check (88 countries).

| Protocol | Working | File |
|---|---|---|
| HTTP | 592 | [`proxies/http.txt`](proxies/http.txt) |
| HTTPS (the HTTP proxies, all passed an HTTPS request) | 592 | [`proxies/https.txt`](proxies/https.txt) |
| SOCKS4 | 183 | [`proxies/socks4.txt`](proxies/socks4.txt) |
| SOCKS5 | 805 | [`proxies/socks5.txt`](proxies/socks5.txt) |
| **All** | **1,580** | [`proxies/all.txt`](proxies/all.txt) |

| Anonymity | Working | File |
|---|---|---|
| Elite (no proxy headers) | 537 | [`proxies/anonymity/elite.txt`](proxies/anonymity/elite.txt) |
| Anonymous (your IP hidden, proxy visible) | 5 | [`proxies/anonymity/anonymous.txt`](proxies/anonymity/anonymous.txt) |
| Transparent (your IP visible on HTTP sites) | 158 | [`proxies/anonymity/transparent.txt`](proxies/anonymity/transparent.txt) |
| Not labelled yet | 880 | |

Top countries (all 88 are in [`proxies/countries/`](proxies/countries)):

| Country | Working | File |
|---|---|---|
| US | 415 | [`proxies/countries/US.txt`](proxies/countries/US.txt) |
| ID | 359 | [`proxies/countries/ID.txt`](proxies/countries/ID.txt) |
| FR | 65 | [`proxies/countries/FR.txt`](proxies/countries/FR.txt) |
| IN | 50 | [`proxies/countries/IN.txt`](proxies/countries/IN.txt) |
| CN | 50 | [`proxies/countries/CN.txt`](proxies/countries/CN.txt) |
| VN | 42 | [`proxies/countries/VN.txt`](proxies/countries/VN.txt) |
| PH | 39 | [`proxies/countries/PH.txt`](proxies/countries/PH.txt) |
| BD | 35 | [`proxies/countries/BD.txt`](proxies/countries/BD.txt) |
| MX | 33 | [`proxies/countries/MX.txt`](proxies/countries/MX.txt) |
| BR | 33 | [`proxies/countries/BR.txt`](proxies/countries/BR.txt) |
| SG | 31 | [`proxies/countries/SG.txt`](proxies/countries/SG.txt) |
| RU | 31 | [`proxies/countries/RU.txt`](proxies/countries/RU.txt) |
<!-- stats:end -->

## Download the free proxy list (TXT, JSON, CSV)

| File | Format | Direct link |
|---|---|---|
| All proxies | `scheme://ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/all.txt |
| HTTP | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/http.txt |
| HTTPS (the HTTP proxies, all passed an HTTPS request) | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/https.txt |
| SOCKS4 | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/socks4.txt |
| SOCKS5 | `ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/socks5.txt |
| Elite | `scheme://ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/anonymity/elite.txt |
| Anonymous | `scheme://ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/anonymity/anonymous.txt |
| Transparent | `scheme://ip:port` | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/anonymity/transparent.txt |
| By country | `scheme://ip:port` | `https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/countries/US.txt` (two-letter code; `TOR` for Tor exits, `XX` unknown) |
| With details | JSON | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/proxies.json |
| With details | CSV | https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/proxies/proxies.csv |

The same files are on the jsDelivr CDN: replace `https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/` with `https://cdn.jsdelivr.net/gh/FusionProxies/free-proxy-list@main/`.

Each JSON and CSV row has `proxy`, `protocol`, `ip`, `port`, `exit_ip`, `country`, `latency_ms`, `checked_at` and `anonymity` (`elite`, `anonymous`, `transparent`, or `unknown` until the first test).

## How to use a free proxy list (cURL and Python)

```bash
# fetch the SOCKS5 list and try the fastest proxy
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

To check proxies yourself, use [proxy-checker](https://github.com/FusionProxies/proxy-checker) (command line) or the [online proxy checker](https://fusionproxy.net/tools/proxy-checker?utm_source=github&utm_medium=free-proxy-list).

## How the proxies are checked

1. Every 30 minutes a job collects candidate proxies from five public lists (see [Sources](#sources)) and merges them without duplicates. The time of the last update is at the top of the list.
2. [proxy-checker](https://github.com/FusionProxies/proxy-checker) connects through every candidate to `https://www.cloudflare.com/cdn-cgi/trace` with a 10 second limit.
3. A proxy is published only if the request succeeded. Lists often call an HTTP proxy that can open HTTPS sites an "HTTPS proxy"; those are checked as HTTP. Every HTTP proxy here passed an HTTPS request, so `https.txt` holds the same proxies as `http.txt`. Proxies that present a forged HTTPS certificate fail the check and are dropped, because they read or change the traffic that passes through them.
4. The country is the one Cloudflare sees for the exit IP, and the files are sorted by response time.
5. Every working proxy then sends one plain-HTTP request to `http://httpbin.org/get`, a "judge" that echoes back the IP and headers it received, and gets its anonymity level (see below). A proxy is tested again after 24 hours.

Free proxies come and go within hours, so expect a part of the list to fail by the time you use it.

## Elite, anonymous and transparent proxies

| Level | Your real IP | The site can tell a proxy is used | File |
|---|---|---|---|
| **Elite** (high anonymity) | Hidden | No | [`proxies/anonymity/elite.txt`](proxies/anonymity/elite.txt) |
| **Anonymous** | Hidden | Yes, from headers such as `Via` or `X-Forwarded-For` | [`proxies/anonymity/anonymous.txt`](proxies/anonymity/anonymous.txt) |
| **Transparent** | **Visible** | Yes | [`proxies/anonymity/transparent.txt`](proxies/anonymity/transparent.txt) |

A transparent proxy tells every plain-HTTP website the IP address of whoever uses it, so it hides nothing. Many public lists still publish them as anonymous; here they are labelled and kept apart. The level only matters for plain `http://` sites: inside an `https://` connection the proxy cannot add headers. SOCKS proxies relay the connection without adding headers, so they come out elite unless they forward through another proxy.

To test any proxy yourself, use [proxy-anonymity-test](https://github.com/FusionProxies/proxy-anonymity-test).

## Are free proxies safe?

Public proxies are run by unknown people. Treat everything you send through them as visible to the operator:

- never log in to accounts or send passwords, cookies or payment details through them;
- prefer HTTPS sites, and use `socks5h://` so DNS is resolved on the proxy side;
- expect slow answers, frequent timeouts and IPs that many sites already block.

For logins, scraping at scale or anything that has to keep working, use proxies with a known source. [Fusion Proxy residential proxies](https://fusionproxy.net/proxies/residential?utm_source=github&utm_medium=free-proxy-list) give you real household IPs in the country, state or city you choose, with rotating or sticky sessions, from $2.95/GB and down to $0.65/GB at volume. [Try it free](https://fusionproxy.net/free-trial?utm_source=github&utm_medium=free-proxy-list).

## Sources

Candidates come from these public lists, all MIT licensed, and every one is re-checked before it is published here:

- [iplocate/free-proxy-list](https://github.com/iplocate/free-proxy-list)
- [monosans/proxy-list](https://github.com/monosans/proxy-list)
- [ProxyScrape/free-proxy-list](https://github.com/ProxyScrape/free-proxy-list)
- [vakhov/fresh-proxy-list](https://github.com/vakhov/fresh-proxy-list)
- [Zaeem20/FREE_PROXIES_LIST](https://github.com/Zaeem20/FREE_PROXIES_LIST)

Their licenses are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

The scripts and the published lists are MIT licensed, see [LICENSE](LICENSE).
