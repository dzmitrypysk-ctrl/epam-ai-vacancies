"""HTML pages for /test and /stats (no template engine)."""

from __future__ import annotations

import html
import json
import os
from typing import Any


def _esc(s: str) -> str:
    return html.escape(s or "")


def _base_url() -> str:
    """Prefer explicit PUBLIC_BASE_URL; on Render use RENDER_EXTERNAL_URL."""
    for key in ("PUBLIC_BASE_URL", "RENDER_EXTERNAL_URL"):
        val = (os.environ.get(key) or "").strip().rstrip("/")
        if val:
            return val
    return ""


def _cf_beacon() -> str:
    token = os.environ.get("CF_ANALYTICS_TOKEN", "").strip()
    if not token:
        return ""
    return f"""
<script defer src='https://static.cloudflareinsights.com/beacon.min.js'
  data-cf-beacon='{{"token": "{_esc(token)}"}}'></script>
"""


def test_page(meta: dict[str, Any] | None = None) -> str:
    base = _base_url() or "(public URL not set)"
    job_count = (meta or {}).get("job_count", "?")
    ingested = (meta or {}).get("ingested_at", "?")

    smoke_links = [
        ("/health", "Health check"),
        ("/llms.txt", "Agent index (llms.txt)"),
        ("/openapi.json", "OpenAPI spec"),
        ("/jobs?q=java&country=Poland&remote=true&limit=5", "Search: Java remote Poland"),
        ("/jobs?q=python&country=India&limit=5", "Search: Python India"),
        ("/locations", "Countries list"),
        ("/stats", "Analytics dashboard"),
    ]

    links_html = "\n".join(
        f'    <li><a href="{_esc(base + path if base.startswith("http") else path)}">'
        f'{_esc(label)}</a> <code>{_esc(path)}</code></li>'
        for path, label in smoke_links
    )

    curl_base = base if base.startswith("http") else "https://YOUR-APP.onrender.com"
    curl_block = f"""curl -s "{curl_base}/health" | jq .
curl -s "{curl_base}/llms.txt" | head -20
curl -s "{curl_base}/jobs?q=java&country=Poland&remote=true&limit=3" | jq '.total, .results[].title'
curl -s -A GPTBot "{curl_base}/llms.txt" | head -5"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>EPAM AI Vacancy API — Test Guide</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 820px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    .banner {{ background: #fff3cd; border: 1px solid #ffc107; padding: 0.75rem 1rem; border-radius: 6px; margin-bottom: 1.5rem; }}
    code, pre {{ background: #f4f4f4; padding: 0.15rem 0.35rem; border-radius: 4px; font-size: 0.9em; }}
    pre {{ padding: 1rem; overflow-x: auto; }}
    h2 {{ margin-top: 2rem; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem; text-align: left; }}
    th {{ background: #f8f8f8; }}
  </style>
  {_cf_beacon()}
</head>
<body>
  <div class="banner">
    <strong>PROTOTYPE</strong> — not an official EPAM service.
    Data from public careers feed snapshot. For testing AI discovery only.
  </div>

  <h1>EPAM AI-native vacancy API — test guide</h1>
  <p>Jobs in index: <strong>{_esc(str(job_count))}</strong> |
     Last ingest: <code>{_esc(str(ingested))}</code></p>
  <p>Base URL: <code>{_esc(base)}</code></p>

  <h2>1. Quick smoke links</h2>
  <ul>
{links_html}
  </ul>

  <h2>2. curl (terminal)</h2>
  <pre>{_esc(curl_block)}</pre>

  <h2>3. Test with AI tools</h2>
  <table>
    <tr><th>Tool</th><th>What to do</th><th>Success signal in /stats</th></tr>
    <tr>
      <td>Perplexity</td>
      <td>
        <p><strong>If onrender.com fetch fails</strong> (cold start or tool blocks Render), use GitHub raw mirror:</p>
        <pre style="white-space:pre-wrap;margin:0.5rem 0">Fetch these URLs and list titles, locations, apply URLs:
1) https://raw.githubusercontent.com/dzmitrypysk-ctrl/epam-ai-vacancies/main/static-mirror/llms.txt
2) https://raw.githubusercontent.com/dzmitrypysk-ctrl/epam-ai-vacancies/main/static-mirror/jobs-java-poland.json</pre>
        <p>Live API (warm service first — open {_esc(curl_base)}/health ):</p>
        <pre style="white-space:pre-wrap;margin:0.5rem 0">Use only this machine-readable job API (do not fall back to careers.epam.com):
1) GET {_esc(curl_base)}/llms.txt
2) Then GET {_esc(curl_base)}/jobs?q=java&amp;country=Poland&amp;limit=5
List titles, locations, and apply URLs from the JSON results.</pre>
      </td>
      <td><code>perplexitybot</code> on /llms.txt+/jobs (GitHub raw will not show in /stats)</td>
    </tr>
    <tr>
      <td>ChatGPT</td>
      <td>Custom GPT Action → import {_esc(curl_base)}/openapi.json</td>
      <td><code>gptbot</code> or API calls to /jobs</td>
    </tr>
    <tr>
      <td>Bot simulation</td>
      <td><code>curl -A GPTBot …/llms.txt</code> and <code>curl -I …/llms.txt</code> (HEAD must be 200)</td>
      <td><code>gptbot</code> in client_classes</td>
    </tr>
    <tr>
      <td>Claude</td>
      <td>Paste llms.txt URL in chat; ask to search Java Poland via /jobs</td>
      <td><code>claudebot</code> or browser</td>
    </tr>
  </table>

  <h2>4. Read analytics</h2>
  <p>Open <a href="/stats">/stats</a> after tests. Look for:</p>
  <ul>
    <li><strong>client_classes</strong> — which bots/agents hit the API</li>
    <li><strong>endpoints</strong> — /llms.txt and /jobs should appear first</li>
    <li><strong>search_queries</strong> — your test filters (q, country, remote)</li>
    <li><strong>recent</strong> — last 50 requests with User-Agent</li>
  </ul>
  <p>Page views on this guide are tracked via Cloudflare Web Analytics (if CF_ANALYTICS_TOKEN is set).</p>

  <h2>5. Refresh data</h2>
  <ol>
    <li>Local: <code>python _scripts/ingest_feed.py --fetch</code> (EPAM network)</li>
    <li><code>python _scripts/build_gzip_store.py</code></li>
    <li>Push <code>data/jobs.json.gz</code> → redeploy on Render</li>
  </ol>

  <p><a href="/docs">Swagger UI</a> | <a href="/">API root</a></p>
</body>
</html>"""


def stats_page(summary: dict[str, Any], *, token_query: str = "") -> str:
    base = _base_url()
    token_suffix = f"?token={_esc(token_query)}" if token_query else ""

    client_rows = "\n".join(
        f"<tr><td><code>{_esc(k)}</code></td><td>{v}</td></tr>"
        for k, v in (summary.get("client_classes") or {}).items()
    ) or "<tr><td colspan=2>No data yet</td></tr>"

    endpoint_rows = "\n".join(
        f"<tr><td><code>{_esc(k)}</code></td><td>{v}</td></tr>"
        for k, v in (summary.get("endpoints") or {}).items()
    ) or "<tr><td colspan=2>No data yet</td></tr>"

    search_rows = "\n".join(
        f"<tr><td><code>{_esc(item.get('query', ''))}</code></td><td>{item.get('count', 0)}</td></tr>"
        for item in (summary.get("search_queries") or [])
    ) or "<tr><td colspan=2>No /jobs searches yet</td></tr>"

    recent_rows = "\n".join(
        f"""<tr>
          <td>{_esc(r.get('time', ''))}</td>
          <td><code>{_esc(r.get('client_class', ''))}</code></td>
          <td>{_esc(r.get('method', ''))} {_esc(r.get('path', ''))}{('?' + _esc(r.get('query', ''))) if r.get('query') else ''}</td>
          <td>{r.get('status', '')}</td>
          <td><small>{_esc(r.get('user_agent', ''))}</small></td>
        </tr>"""
        for r in (summary.get("recent") or [])
    ) or "<tr><td colspan=5>No requests yet — run smoke tests from <a href='/test'>/test</a></td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>API Analytics — EPAM Vacancy Prototype</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem; }}
    .banner {{ background: #fff3cd; border: 1px solid #ffc107; padding: 0.75rem; border-radius: 6px; margin-bottom: 1rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; font-size: 0.9rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.4rem 0.5rem; text-align: left; vertical-align: top; }}
    th {{ background: #f0f0f0; }}
    h2 {{ margin-top: 1.5rem; }}
    .metric {{ font-size: 1.5rem; font-weight: bold; }}
  </style>
  {_cf_beacon()}
</head>
<body>
  <div class="banner">PROTOTYPE analytics — in-memory (resets on redeploy). Not official EPAM.</div>
  <h1>Request analytics</h1>
  <p class="metric">Total requests: {summary.get('total_requests', 0)}</p>
  <p>Base: <code>{_esc(base or 'n/a')}</code> |
     JSON: <a href="/stats.json{token_suffix}">/stats.json</a> |
     <a href="/test">Test guide</a></p>

  <h2>Client classes (bots vs browsers)</h2>
  <table><tr><th>Class</th><th>Count</th></tr>{client_rows}</table>

  <h2>Top endpoints</h2>
  <table><tr><th>Endpoint</th><th>Count</th></tr>{endpoint_rows}</table>

  <h2>Search queries (/jobs)</h2>
  <table><tr><th>Params</th><th>Count</th></tr>{search_rows}</table>

  <h2>Recent requests (newest first)</h2>
  <table>
    <tr><th>Time</th><th>Client</th><th>Request</th><th>Status</th><th>User-Agent</th></tr>
    {recent_rows}
  </table>
</body>
</html>"""
