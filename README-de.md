# fernsehserien-mcp 📺

mcp-name: io.github.mohammad-abbasi-sh/fernsehserien-mcp

Inoffizieller **nur lesender** MCP-Server für **[fernsehserien.de](https://www.fernsehserien.de)** — Deutsche TV-Serien von fernsehserien.de (kostenlos, kein Schlüssel, kein Login): Serien suchen, Seriendetails, Episodenguides und Sendetermine. Kein Schlüssel, keine Anmeldung.

> Gebaut von Mohammad Abbasi als Teil der "Germany MCP factory". Nicht mit fernsehserien.de verbunden.

## Für KI-Agenten

Zur MCP-Client-Konfiguration hinzufügen (stdio):

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

Oder lokal starten: `python -m fernsehserien_mcp.server` (benötigt `mcp<2`, `httpx`).

## Tools

| Tool | Beschreibung |
|------|-------------|
| `fs_search_series` | TV-Serien nach Namen suchen |
| `fs_series_detail` | Seriendetails und Staffeln |
| `fs_episodes` | Episodenguide einer Staffel |
| `fs_air_dates` | Kommende Sendetermine einer Serie |
| `fs_health` | Erreichbarkeitsprüfung (ok / blocked / error) — eine höfliche Anfrage |

## Entwicklung

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## Lizenz

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
