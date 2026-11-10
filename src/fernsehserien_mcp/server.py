"""MCP server: unofficial read-only access to fernsehserien.de,
Germany's TV-series database (~9–10M visits/month). No key, no
login, no wall — plain GETs. Search, series details, episode
guides and upcoming air dates (Sendetermine). NOTE: no site-wide
"tonight on TV" tool — fernsehserien.de has no /tv-programm
section; per-series Sendetermine is the real data."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import domain as _dom
from . import http as _http

INSTRUCTIONS = """\
Unofficial read-only MCP server for fernsehserien.de (no key, no \
login): search TV series by name, series details with seasons, \
episode guides for one season (number, title, runtime, airings), \
and upcoming air dates (Sendetermine) for a series. NOTE: no \
site-wide "tonight on TV" tool — the site has no TV-programme \
section; per-series Sendetermine is the real data. Built by \
Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Germany MCP factory.\
"""

_SOURCE = "fernsehserien.de"
_DISCLAIMER = ("Unofficial read-only data from fernsehserien.de; "
               "verify on the site before acting on it.")


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


mcp = FastMCP("fernsehserien-mcp", instructions=INSTRUCTIONS)


@mcp.tool()
def fs_search_series(query: str, limit: int = 10) -> str:
    """Search TV series by name on fernsehserien.de. query: e.g.
    babylon, tatort, breaking bad. limit: 1..20 (default 10).
    Films are not returned — series only."""
    try:
        q = _dom.validate_query(query)
        lim = _dom.validate_limit(limit)
        items = _dom.parse_search_results(
            _http.fetch_text(_dom.search_url(q)))
    except (_http.FernsehserienMcpError, ValueError) as e:
        return _err(e)
    return _ok({"query": q, "total_results": len(items),
                "count": min(lim, len(items)), "items": items[:lim]})


@mcp.tool()
def fs_series_detail(series: str) -> str:
    """Series details: description, seasons and links to the episode
    guide, air dates and streams. series: a slug (babylon-berlin)
    or a fernsehserien.de series URL."""
    try:
        slug = _dom.resolve_series(series)
        out = _dom.parse_series_detail(
            _http.fetch_text(f"{_dom.BASE}/{slug}"), slug)
    except (_http.FernsehserienMcpError, ValueError) as e:
        return _err(e)
    return _ok(out)


@mcp.tool()
def fs_episodes(series: str, season: int = 1, limit: int = 10) -> str:
    """Episode guide for one season: episode number, title, runtime
    and airings (type, date, channel). series: a slug or URL.
    season: the season number (default 1). limit: 1..20
    (default 10)."""
    try:
        slug = _dom.resolve_series(series)
        s = _dom.validate_season(season)
        lim = _dom.validate_limit(limit)
        detail = _dom.parse_series_detail(
            _http.fetch_text(f"{_dom.BASE}/{slug}"), slug)
        url = _dom.season_guide_url(detail, s)
        items = _dom.parse_episodes(_http.fetch_text(url))
    except (_http.FernsehserienMcpError, ValueError) as e:
        return _err(e)
    return _ok({"series": detail["name"], "slug": slug, "season": s,
                "guide_url": url, "total_results": len(items),
                "count": min(lim, len(items)), "items": items[:lim]})


@mcp.tool()
def fs_air_dates(series: str, limit: int = 10) -> str:
    """Upcoming air dates (Sendetermine) for a series: start/end,
    channel, episode code and title. series: a slug or URL.
    limit: 1..20 (default 10)."""
    try:
        slug = _dom.resolve_series(series)
        lim = _dom.validate_limit(limit)
        items = _dom.parse_air_dates(_http.fetch_text(
            f"{_dom.BASE}/{slug}/sendetermine"))
    except (_http.FernsehserienMcpError, ValueError) as e:
        return _err(e)
    return _ok({"series": slug, "total_results": len(items),
                "count": min(lim, len(items)), "items": items[:lim]})


@mcp.tool()
def fs_health() -> str:
    """Check whether fernsehserien.de is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    One polite request; it does not fetch any listings."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    sys.exit(main())
