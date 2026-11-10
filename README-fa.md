# fernsehserien-mcp 📺

mcp-name: io.github.mohammad-abbasi-sh/fernsehserien-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **[fernsehserien.de](https://www.fernsehserien.de)** — سریال‌های تلویزیونی آلمان از fernsehserien.de (رایگان، بدون کلید): جست‌وجوی سریال، جزئیات سریال، راهنمای قسمت‌ها و زمان‌های پخش آینده. بدون کلید، بدون ورود.

> ساختهٔ محمد عباسی، بخشی از «کارخانهٔ MCP آلمان». وابسته به fernsehserien.de نیست.

## برای ایجنت‌های هوش مصنوعی

به پیکربندی MCP کلاینت اضافه کنید (stdio):

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

یا به‌صورت محلی اجرا کنید: `python -m fernsehserien_mcp.server` (نیازمند `mcp<2` و `httpx`).

## ابزارها

| ابزار | توضیح |
|------|-------|
| `fs_search_series` | جست‌وجوی سریال‌های تلویزیونی بر اساس نام |
| `fs_series_detail` | جزئیات سریال و فصل‌ها |
| `fs_episodes` | راهنمای قسمت‌های یک فصل |
| `fs_air_dates` | زمان‌های پخش آیندهٔ یک سریال |
| `fs_health` | بررسی دسترس‌پذیری (ok / blocked / error) — یک درخواست مؤدبانه |

## توسعه

```bash
python3 -m venv .venv && .venv/bin/pip install "mcp<2" httpx pytest
.venv/bin/pip install -e .
.venv/bin/python -m pytest tests/ -q
```

## لایسنس

MIT

---

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
