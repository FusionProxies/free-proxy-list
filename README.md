<p align="center">
  <a href="https://fusionproxy.net/?utm_source=github&utm_medium=free-proxy-list">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-dark.png">
      <img src="https://raw.githubusercontent.com/FusionProxies/.github/main/assets/logo-on-light.png" alt="Fusion Proxy" height="52">
    </picture>
  </a>
</p>

# Free Proxy List: HTTP, SOCKS4 and SOCKS5 proxies, updated every 30 minutes

A free proxy list of HTTP, SOCKS4 and SOCKS5 proxies, merged from five public lists **every 30 minutes** and published without duplicates as TXT, JSON and CSV. The proxies are not re-checked here: free proxies come and go within hours, so check the ones you need before you use them (see [How the list is built](#how-the-list-is-built)).

[![Proxies](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Ftotal.json)](proxies/all.txt)
[![Updated](https://img.shields.io/endpoint?url=https%3A%2F%2Fraw.githubusercontent.com%2FFusionProxies%2Ffree-proxy-list%2Fmain%2Fproxies%2Fbadges%2Fupdated.json)](https://github.com/FusionProxies/free-proxy-list/commits/main)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

If this list saves you time, a ⭐ helps other developers find it.

## Current list

<!-- stats:start -->
Last update: **2026-11-13 16:35 UTC**. 4,062 proxies from 5 public lists, merged without duplicates (not re-checked here).

| Protocol | Proxies | File |
|---|---|---|
| HTTP | 2,298 | [`proxies/http.txt`](proxies/http.txt) |
| SOCKS4 | 662 | [`proxies/socks4.txt`](proxies/socks4.txt) |
| SOCKS5 | 1,102 | [`proxies/socks5.txt`](proxies/socks5.txt) |
| **All** | **4,062** | [`proxies/all.txt`](proxies/all.txt) |
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

The same files are on the jsDelivr CDN: replace `https://raw.githubusercontent.com/FusionProxies/free-proxy-list/main/` with `https://cdn.jsdelivr.net/gh/FusionProxies/free-proxy-list@main/`.

Each JSON and CSV row has `proxy`, `protocol`, `ip` and `port`.

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

To check proxies yourself, use [proxy-checker](https://github.com/FusionProxies/proxy-checker) (command line) or the [online proxy checker](https://fusionproxy.net/tools/proxy-checker?utm_source=github&utm_medium=free-proxy-list).

## How the list is built

1. Every 30 minutes a job downloads the lists of five public sources (see [Sources](#sources)) and merges them without duplicates (`scripts/merge.py`). The time of the last update is at the top of the list.
2. Lists often call an HTTP proxy that can open HTTPS sites an "HTTPS proxy"; those are in `http.txt`.
3. The proxies are not connected to or tested here. To build a checked list yourself (working proxies only, sorted by speed, with country and anonymity level), run `scripts/update.py` with [proxy-checker](https://github.com/FusionProxies/proxy-checker) installed.

Free proxies come and go within hours, so expect a part of the list to fail by the time you use it.

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

For logins, scraping at scale or anything that has to keep working, use proxies with a known source. [Fusion Proxy residential proxies](https://fusionproxy.net/proxies/residential?utm_source=github&utm_medium=free-proxy-list) give you real household IPs in the country, state or city you choose, with rotating or sticky sessions, from $2.95/GB and down to $0.65/GB at volume. [Try it free](https://fusionproxy.net/free-trial?utm_source=github&utm_medium=free-proxy-list).

## Sources

The proxies come from these public lists, all MIT licensed:

- [iplocate/free-proxy-list](https://github.com/iplocate/free-proxy-list)
- [monosans/proxy-list](https://github.com/monosans/proxy-list)
- [ProxyScrape/free-proxy-list](https://github.com/ProxyScrape/free-proxy-list)
- [vakhov/fresh-proxy-list](https://github.com/vakhov/fresh-proxy-list)
- [Zaeem20/FREE_PROXIES_LIST](https://github.com/Zaeem20/FREE_PROXIES_LIST)

Their licenses are in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## License

The scripts and the published lists are MIT licensed, see [LICENSE](LICENSE).
