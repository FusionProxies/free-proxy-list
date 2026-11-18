# Data schema

Everything in `proxies/` is written by `scripts/merge.py` every 30 minutes. This page is the contract for scripts that read it.

## Versioning

- `stats.json` carries `schema_version` (now **2**).
- New fields may be added at any time without a version change. In the CSV they are added as new columns at the end.
- Renaming or removing a field, or changing what a value means, raises `schema_version`, and the change is listed in this file.
- The TXT files keep their format: one proxy per line, `ip:port` in the protocol files, `scheme://ip:port` in `all.txt` and `countries/*.txt`.

Version history:

| Version | Change |
|---|---|
| 1 | `proxy`, `protocol`, `ip`, `port` (until November 2026; there was no `stats.json`) |
| 2 | added `status`, `country`, `sources`, `source_count`, `first_seen`; added `stats.json` and `countries/*.txt` |

## Status words

| Value | Meaning |
|---|---|
| `collected` | A source list named the proxy in the latest run. Nobody here connected to it. **Every row in this repository has this status.** |
| `tested` | A connection through the proxy was attempted at a known time. |
| `reachable` | The proxy accepted the connection and answered its protocol handshake. |
| `verified` | A full request through the proxy returned the expected answer. |

`tested`, `reachable` and `verified` appear only in output you build yourself with `scripts/update.py`; they are reserved here so the words keep one meaning.

## `proxies.json` and `proxies.csv`

One row per proxy. JSON is an array of objects. The CSV has a header row, the same fields in this order, `;` between source names and `\n` line endings.

| Field | Type | Example | Meaning |
|---|---|---|---|
| `proxy` | string | `socks5://1.2.3.4:1080` | `protocol://ip:port`, unique in the file |
| `protocol` | string | `socks5` | `http`, `socks4` or `socks5`. Sources that say `https` mean an HTTP proxy that can open HTTPS sites (CONNECT); those are `http` here |
| `ip` | string | `1.2.3.4` | IPv4 address as listed |
| `port` | integer | `1080` | 1 to 65535 |
| `status` | string | `collected` | see [Status words](#status-words) |
| `country` | string | `US` | ISO 3166-1 alpha-2 code of the **listed IP** in the DB-IP IP to Country Lite database. Empty string when the database has no country for it, or when no database could be loaded in that run |
| `sources` | array of strings (CSV: `;`-separated) | `["monosans/proxy-list"]` | GitHub `owner/repo` of every source list that named the proxy in this run |
| `source_count` | integer | `1` | length of `sources` |
| `first_seen` | string, UTC, `YYYY-MM-DDTHH:MM:SSZ` | `2026-11-18T10:35:00Z` | first run that listed the proxy since tracking began (`first_seen_tracked_since` in `stats.json`). A proxy that drops out for more than 72 hours and comes back starts again |

Order: rows listed by more sources first, then in the order the sources gave them. The order is not a quality ranking.

## `stats.json`

| Field | Type | Meaning |
|---|---|---|
| `schema_version` | integer | see [Versioning](#versioning) |
| `generated_at` | string, UTC | time of the run |
| `status` | string | `collected` |
| `tested` | boolean | `false`: no proxy was connected to |
| `total` | integer | rows in `proxies.json` |
| `protocols` | object | rows per protocol: `http`, `socks4`, `socks5` |
| `countries` | object | rows per country code, largest first; `XX` counts rows without a country |
| `sources` | object | per source list: `listed` (rows it named) and `only_here` (rows no other source named) |
| `sources_answered`, `sources_total` | integer | source lists that answered in this run, and how many are configured |
| `listed_by_2_or_more` | integer | rows with `source_count >= 2` |
| `new_since_previous_run` | integer or null | rows that were not in the previous run; `null` on the first run |
| `first_seen_tracked_since` | string, UTC | when `first_seen` tracking began |
| `geoip` | object | `database` (name and month, or `null`), `license`, `located` (rows with a country) |

## History (not published)

`first_seen` and `new_since_previous_run` come from a state file the job keeps next to the repo
(`.cache/history.json`, or `STATE_DIR`). It is not published because it changes on every run and
grows with every proxy the sources list. It maps each proxy to `[first_seen, last_seen, runs_listed]`
and keeps proxies that left the sources less than 72 hours ago (`HISTORY_HOURS`), because free
proxies often come back. If the file is lost, tracking starts again and `first_seen_tracked_since`
in `stats.json` moves to that run.

## `countries/XX.txt`

Proxies whose listed IP is in country `XX` (see `country` above), one `scheme://ip:port` per line. Files are rebuilt every run; a country with no proxies has no file.

## Badges

`badges/total.json`, `badges/countries.json` and `badges/updated.json` follow the [shields.io endpoint](https://shields.io/badges/endpoint-badge) format.
