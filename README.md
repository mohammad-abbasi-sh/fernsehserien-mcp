# fernsehserien-mcp 📺

mcp-name: io.github.mohammad-abbasi-sh/fernsehserien-mcp

Unofficial **read-only** MCP server for **[fernsehserien.de](https://www.fernsehserien.de)** — German TV series from fernsehserien.de (free, no key, no login): search series, series details, episode guides and upcoming air dates. No key, no login.

> Built by Mohammad Abbasi as part of the "Germany MCP factory". Not affiliated with fernsehserien.de.

## For AI agents

Add to your MCP client config (stdio):

```json
{
  "mcpServers": {
    "fernsehserien": {
      "command": "uvx",
      "args": ["fernsehserien-mcp==0.1.0"]
    }
  }
}
```

Or run locally: `python -m fernsehserien_mcp.server` (needs `mcp<2`, `httpx`).

## Tools

| Tool | Description |
|------|-------------|
| `fs_search_series` | Search TV series by name — `query`, `limit` 1..20 |
| `fs_series_detail` | Series detail page: description, seasons, links to episode guide / air dates / streams — `series` (slug or fernsehserien.de URL) |
| `fs_episodes` | Episode guide for one season: episode number, title, runtime, airings — `series` (slug or URL), `season` (number), `limit` 1..20 |
| `fs_air_dates` | Upcoming air dates (Sendetermine) for a series: date/time, channel, episode — `series` (slug or URL), `limit` 1..20 |
| `fs_health` | Reachability probe (ok / blocked / error) — one polite request |

## Development

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## License

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
