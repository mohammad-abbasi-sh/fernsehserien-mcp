"""Domain logic: shape fernsehserien.de's server-rendered HTML into
compact dicts (stdlib only, regex parsers).

Data source: https://www.fernsehserien.de — free, no key, no login,
no wall (plain GETs, 200).

Pages (verified 2026-11-10):
- GET /suche/<query> — search results: series rows are
  <li class="ep-hover suchergebnisse-sendung"><a title="<name>"
  href="/<slug>">…<dl><dt><name></dt><dd><abbr
  title="<country>">X</abbr> <years></dd></dl>; films are
  suchergebnisse-film (not returned — this server is series-only).
  No match -> 0 suchergebnisse-sendung rows.
- GET /<slug> — series page: <title> "<name> – fernsehserien.de",
  meta description = synopsis, season menu links
  /<slug>/episodenguide/staffel-<N>/<series-id>, plus
  /<slug>/sendetermine and /<slug>/streams.
- GET /<slug>/episodenguide/staffel-<N>/<series-id> — episode
  blocks id="episode-<id>": <a href="/<slug>/folgen/<code>-<title>-<id>">
  <span><abs-no></span>. <span itemprop="name"><title></span></a>,
  "Staffel N (NN Min.)", airings as <ea-angabe> rows:
  <ea-angabe-titel><type></ea-angabe-titel>
  <ea-angabe-datum>Do. 10.09.2026</ea-angabe-datum>
  <ea-angabe-sender><channel></ea-angabe-sender>.
- GET /<slug>/sendetermine — upcoming air dates, one row per
  BroadcastEvent: <time itemprop="startDate"
  datetime="2026-11-10T20:15:00+01:00">, endDate likewise,
  channel <span itemprop="name" title="<ch>" content="<ch>">,
  episode code <span class="…sendetermine-2019-staffel-und-episode">
  2.05</span>, title <span class="…episodentitel">Episode 5</span>,
  episode link on the row's <a href="/<slug>/folgen/…">.

No site-wide "tonight on TV" programme exists on fernsehserien.de
(no /tv-programm section — the programme lives on sister sites);
tonight_tv / channel_schedule from the research draft are therefore
NOT built — per-series Sendetermine is the real data.
"""
from __future__ import annotations

import html as _html
import re
from urllib.parse import quote

BASE = "https://www.fernsehserien.de"

_SEARCH_RE = re.compile(
    r'<li class="ep-hover suchergebnisse-sendung">.*?</li>', re.S)
_SEARCH_LINK_RE = re.compile(
    r'<a[^>]+title="([^"]+)" href="(/[^"]+)"')
_SEARCH_DT_RE = re.compile(r'<dt>(.*?)</dt>', re.S)
_SEARCH_DD_RE = re.compile(r'<dd>(.*?)</dd>', re.S)

_SEASON_RE = re.compile(
    r'href="(/[^"/]+/episodenguide/staffel-(\d+)/(\d+))"')

_EPISODE_RE = re.compile(
    r'id="episode-(\d+)"[^>]*>\s*<a[^>]+href="(/[^"/]+/folgen/([^"]+))"'
    r'[^>]*>\s*<span>(\d+)</span>\.\s*<span itemprop="name">([^<]+)</span>',
    re.S)
_EP_RUNTIME_RE = re.compile(r'Staffel \d+ \((\d+)(?:&nbsp;|\s)*Min\.\)')
_EP_AIRING_RE = re.compile(
    r'<ea-angabe-titel>([^<]+)</ea-angabe-titel>\s*'
    r'<ea-angabe-datum>([^<]+)</ea-angabe-datum>\s*'
    r'<ea-angabe-sender>([^<]+)</ea-angabe-sender>')

_AIR_ROW_RE = re.compile(
    r'<a[^>]+href="(/[^"/]+/folgen/[^"]+)"[^>]*>.*?'
    r'<time itemprop="startDate" datetime="([^"]+)">.*?'
    r'<time itemprop="endDate" datetime="([^"]+)">.*?'
    r'itemprop="name" title="([^"]+)" content="([^"]+)".*?'
    r'sendetermine-2019-staffel-und-episode">([^<]+)</span>.*?'
    r'sendetermine-2019-episodentitel">([^<]+)</span>',
    re.S)


def validate_query(query: str) -> str:
    q = (query or "").strip()
    if not q:
        raise ValueError("query must not be empty")
    if len(q) > 100:
        raise ValueError("query too long (max 100 characters)")
    return q


def validate_limit(limit: int, maximum: int = 20) -> int:
    if not 1 <= limit <= maximum:
        raise ValueError(
            f"limit out of range: {limit} (expected 1..{maximum})")
    return limit


def validate_season(season: int) -> int:
    if not 1 <= season <= 99:
        raise ValueError(
            f"season out of range: {season} (expected 1..99)")
    return season


def search_url(query: str) -> str:
    q = query.replace("/", " ").replace("?", " ")
    return f"{BASE}/suche/{quote(q)}"


def resolve_series(series: str) -> str:
    """Slug or fernsehserien.de URL -> slug (first path segment)."""
    s = (series or "").strip().strip("/")
    if not s:
        raise ValueError("series must not be empty")
    if s.startswith("http"):
        if "fernsehserien.de/" not in s:
            raise ValueError(
                "series URL must be a fernsehserien.de series URL")
        s = s.split("fernsehserien.de/", 1)[1].strip("/")
    slug = s.split("/")[0]
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", slug):
        raise ValueError(f"invalid series slug: {slug!r}")
    return slug


def _clean(text: str) -> str:
    return _html.unescape(re.sub(r"<[^>]+>", "", text)).replace(
        "\xa0", " ").strip()


def parse_search_results(page_html: str) -> list[dict]:
    out: list[dict] = []
    for m in _SEARCH_RE.finditer(page_html):
        chunk = m.group(0)
        link = _SEARCH_LINK_RE.search(chunk)
        dt = _SEARCH_DT_RE.search(chunk)
        dd = _SEARCH_DD_RE.search(chunk)
        if not link:
            continue
        out.append({
            "name": _clean(dt.group(1)) if dt else link.group(1),
            "url": BASE + link.group(2),
            "info": _clean(dd.group(1)) if dd else None,
        })
    return out


def parse_series_detail(page_html: str, slug: str) -> dict:
    title_m = re.search(r"<title>(.*?)</title>", page_html, re.S)
    desc_m = re.search(
        r'<meta name="description" content="([^"]+)"', page_html)
    title = _clean(title_m.group(1)) if title_m else slug
    title = re.sub(r"\s*– fernsehserien\.de\s*$", "", title)
    seasons: list[dict] = []
    seen: set[int] = set()
    for m in _SEASON_RE.finditer(page_html):
        n = int(m.group(2))
        if n in seen:
            continue
        seen.add(n)
        seasons.append({"season": n, "url": BASE + m.group(1),
                        "series_id": m.group(3)})
    seasons.sort(key=lambda s: s["season"])
    return {
        "slug": slug,
        "name": title,
        "url": f"{BASE}/{slug}",
        "description": (_html.unescape(desc_m.group(1)).strip()
                        if desc_m else None),
        "seasons": seasons,
        "air_dates_url": f"{BASE}/{slug}/sendetermine",
        "streams_url": f"{BASE}/{slug}/streams",
    }


def season_guide_url(detail: dict, season: int) -> str:
    for s in detail["seasons"]:
        if s["season"] == season:
            return s["url"]
    raise ValueError(
        f"season {season} not found for {detail['slug']} "
        f"(available: {[s['season'] for s in detail['seasons']]})")


def parse_episodes(page_html: str) -> list[dict]:
    out: list[dict] = []
    for m in _EPISODE_RE.finditer(page_html):
        chunk = page_html[m.start():m.start() + 9000]
        runtime_m = _EP_RUNTIME_RE.search(chunk)
        airings = [{
            "type": _clean(a.group(1)),
            "date": _clean(a.group(2)),
            "channel": _clean(a.group(3)),
        } for a in _EP_AIRING_RE.finditer(chunk)]
        out.append({
            "episode_id": m.group(1),
            "url": BASE + m.group(2),
            "code": m.group(3).split("-")[0],
            "absolute_number": int(m.group(4)),
            "title": _clean(m.group(5)),
            "runtime_minutes": (int(runtime_m.group(1))
                                if runtime_m else None),
            "airings": airings,
        })
    return out


def parse_air_dates(page_html: str) -> list[dict]:
    out: list[dict] = []
    for m in _AIR_ROW_RE.finditer(page_html):
        out.append({
            "starts": m.group(2),
            "ends": m.group(3),
            "channel": m.group(4),
            "episode_code": _clean(m.group(6)),
            "episode_title": _clean(m.group(7)),
            "episode_url": BASE + m.group(1),
        })
    return out
