"""SSR HTML for independent GEO vacancy surface (catalog + detail + hubs)."""

from __future__ import annotations

import html
import json
import os
from typing import Any

from service.store import job_to_jsonld, public_base_url, vacancy_path, vacancy_public_url


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _base() -> str:
    return public_base_url()


def _cf_beacon() -> str:
    token = os.environ.get("CF_ANALYTICS_TOKEN", "").strip()
    if not token:
        return ""
    return f"""
<script defer src='https://static.cloudflareinsights.com/beacon.min.js'
  data-cf-beacon='{{"token": "{_esc(token)}"}}'></script>
"""


_CSS = """
  :root { --fg:#1a1a1a; --muted:#555; --border:#ddd; --accent:#039; --bg:#fafafa; }
  body { font-family: system-ui, -apple-system, sans-serif; color: var(--fg);
         max-width: 920px; margin: 0 auto; padding: 1.25rem 1rem 3rem; line-height: 1.5; }
  .banner { background: #fff3cd; border: 1px solid #ffc107; padding: 0.65rem 0.9rem;
            border-radius: 6px; margin-bottom: 1.25rem; font-size: 0.92rem; }
  a { color: var(--accent); }
  h1 { font-size: 1.55rem; margin: 0.4rem 0 0.75rem; }
  h2 { font-size: 1.15rem; margin-top: 1.75rem; }
  .meta { color: var(--muted); font-size: 0.95rem; }
  .job-list { list-style: none; padding: 0; margin: 0; }
  .job-list li { border-bottom: 1px solid var(--border); padding: 0.85rem 0; }
  .job-list a.title { font-weight: 600; text-decoration: none; font-size: 1.05rem; }
  .job-list a.title:hover { text-decoration: underline; }
  .chips { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.75rem 0 1rem; }
  .chip { display: inline-block; border: 1px solid var(--border); border-radius: 999px;
          padding: 0.2rem 0.65rem; font-size: 0.85rem; text-decoration: none; color: var(--fg); }
  .chip:hover { background: var(--bg); }
  .chip.active { background: #e8f0ff; border-color: #8ab; }
  .cta { display: inline-block; margin: 1rem 0; padding: 0.55rem 1rem; background: var(--accent);
         color: #fff !important; text-decoration: none; border-radius: 6px; font-weight: 600; }
  .cta:hover { opacity: 0.92; }
  .desc { margin-top: 1.25rem; }
  .desc p { margin: 0.6rem 0; }
  nav.crumb { font-size: 0.9rem; color: var(--muted); margin-bottom: 0.75rem; }
  footer { margin-top: 2.5rem; padding-top: 1rem; border-top: 1px solid var(--border);
           font-size: 0.85rem; color: var(--muted); }
  .pager { margin: 1.25rem 0; display: flex; gap: 1rem; align-items: center; }
  form.filters { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; align-items: end; }
  form.filters label { font-size: 0.8rem; color: var(--muted); display: flex; flex-direction: column; gap: 0.2rem; }
  form.filters input, form.filters select { padding: 0.35rem 0.5rem; font-size: 0.95rem; }
  form.filters button { padding: 0.4rem 0.85rem; }
"""


def _shell(
    *,
    title: str,
    canonical: str,
    body: str,
    description: str = "",
    json_ld: dict[str, Any] | None = None,
    robots: str = "index,follow",
) -> str:
    desc = description or "Open EPAM roles in a machine-readable vacancy index for AI search and agents."
    ld = ""
    if json_ld:
        ld = (
            '<script type="application/ld+json">'
            + json.dumps(json_ld, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
        )
    canon = f'<link rel="canonical" href="{_esc(canonical)}">' if canonical else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_esc(title)}</title>
  <meta name="description" content="{_esc(desc)}">
  <meta name="robots" content="{_esc(robots)}">
  {canon}
  <style>{_CSS}</style>
  {ld}
  {_cf_beacon()}
</head>
<body>
{body}
<footer>
  Prototype independent GEO vacancy index — not an official EPAM careers site.
  Apply links go to careers.epam.com. <a href="/llms.txt">llms.txt</a> ·
  <a href="/sitemap.xml">sitemap</a> · <a href="/docs">API docs</a>
</footer>
</body>
</html>"""


def _location_line(job: dict[str, Any]) -> str:
    city = (job.get("city") or "").strip()
    country = (job.get("country") or "").strip()
    parts = [p for p in [city, country] if p]
    loc = ", ".join(parts) or "Location TBD"
    remote = "Remote" if job.get("is_remote") else (job.get("workplace_type") or "")
    if remote:
        return f"{loc} · {remote}"
    return loc


def home_page(meta: dict[str, Any], countries: list[dict[str, Any]]) -> str:
    base = _base()
    count = meta.get("job_count", "?")
    ingested = meta.get("ingested_at", "n/a")
    top = countries[:12]
    chips = "\n".join(
        f'<a class="chip" href="/vacancies?country={_esc(c["country"])}">{_esc(c["country"])} ({c["count"]})</a>'
        for c in top
    )
    body = f"""
  <div class="banner"><strong>PROTOTYPE</strong> — independent AI/GEO vacancy index.
  Canonical pages live here; apply on careers.epam.com.</div>
  <h1>EPAM open roles — AI-native vacancy index</h1>
  <p class="meta">{_esc(str(count))} jobs · last ingest {_esc(str(ingested))}</p>
  <p>Browse crawlable vacancy pages with JobPosting structured data, or use the
     <a href="/docs">REST API</a> / <a href="/llms.txt">llms.txt</a> for agents.</p>
  <p><a class="cta" href="/vacancies">Browse all vacancies</a>
     <a class="chip" href="/vacancies?remote=true">Remote only</a></p>
  <h2>Top countries</h2>
  <div class="chips">{chips}</div>
  <h2>For AI systems</h2>
  <ul>
    <li><a href="/llms.txt">/llms.txt</a> — agent discovery index</li>
    <li><a href="/sitemap.xml">/sitemap.xml</a> — all vacancy URLs</li>
    <li><a href="/openapi.json">/openapi.json</a> — ChatGPT Actions / tools</li>
  </ul>
"""
    return _shell(
        title="EPAM AI-native vacancy index",
        canonical=f"{base}/" if base else "/",
        body=body,
        description=f"Browse {count} open EPAM roles with JobPosting markup for AI search.",
    )


def catalog_page(
    jobs_page: list[dict[str, Any]],
    *,
    total: int,
    q: str = "",
    country: str = "",
    remote: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    countries: list[dict[str, Any]] | None = None,
) -> str:
    base = _base()
    items = []
    for job in jobs_page:
        path = vacancy_path(job)
        items.append(
            f"""<li>
  <a class="title" href="{_esc(path)}">{_esc(job.get("title") or "")}</a>
  <div class="meta">{_esc(_location_line(job))} ·
       {_esc(job.get("job_type") or "")} · posted {_esc(job.get("date_posted_iso") or "n/a")}</div>
  <p>{_esc((job.get("description_text") or "")[:220])}…</p>
</li>"""
        )
    list_html = "\n".join(items) or "<li>No matching vacancies.</li>"

    remote_val = ""
    if remote is True:
        remote_val = "true"
    elif remote is False:
        remote_val = "false"

    country_opts = ['<option value="">All countries</option>']
    for c in countries or []:
        name = c["country"]
        sel = " selected" if name == country else ""
        country_opts.append(f'<option value="{_esc(name)}"{sel}>{_esc(name)} ({c["count"]})</option>')

    prev_off = max(0, offset - limit)
    next_off = offset + limit
    pager = f'<div class="pager"><span class="meta">Showing {offset + 1}–{min(offset + limit, total)} of {total}</span>'
    qs_base = []
    if q:
        qs_base.append(f"q={_esc(q)}")
    if country:
        qs_base.append(f"country={_esc(country)}")
    if remote_val:
        qs_base.append(f"remote={remote_val}")
    qs_base.append(f"limit={limit}")
    join = "&".join(qs_base)
    if offset > 0:
        pager += f' <a href="/vacancies?{join}&offset={prev_off}">Previous</a>'
    if next_off < total:
        pager += f' <a href="/vacancies?{join}&offset={next_off}">Next</a>'
    pager += "</div>"

    hub_note = ""
    if country:
        hub_note = f'<p class="meta">Country hub: <strong>{_esc(country)}</strong></p>'
    if remote is True:
        hub_note += '<p class="meta">Filter: <strong>Remote</strong></p>'

    body = f"""
  <nav class="crumb"><a href="/">Home</a> · Vacancies</nav>
  <div class="banner"><strong>PROTOTYPE</strong> — crawlable catalog. Apply CTA opens careers.epam.com.</div>
  <h1>Open vacancies</h1>
  {hub_note}
  <form class="filters" method="get" action="/vacancies">
    <label>Query <input type="search" name="q" value="{_esc(q)}" placeholder="java, devops…"></label>
    <label>Country <select name="country">{"".join(country_opts)}</select></label>
    <label>Remote
      <select name="remote">
        <option value="">Any</option>
        <option value="true"{" selected" if remote is True else ""}>Remote only</option>
        <option value="false"{" selected" if remote is False else ""}>Not remote</option>
      </select>
    </label>
    <button type="submit">Filter</button>
  </form>
  {pager}
  <ul class="job-list">
  {list_html}
  </ul>
  {pager}
"""
    # Faceted catalog pages: indexable hubs for country/remote; plain search q = noindex
    robots = "noindex,follow" if q else "index,follow"
    canon_path = "/vacancies"
    params = []
    if country:
        params.append(f"country={country}")
    if remote is True:
        params.append("remote=true")
    if params and not q:
        canon_path = "/vacancies?" + "&".join(params)
    canonical = f"{base}{canon_path}" if base else canon_path
    title_bits = ["EPAM vacancies"]
    if country:
        title_bits.append(country)
    if remote is True:
        title_bits.append("Remote")
    return _shell(
        title=" · ".join(title_bits),
        canonical=canonical,
        body=body,
        description=f"{total} open EPAM roles" + (f" in {country}" if country else "") + ".",
        robots=robots,
    )


def vacancy_detail_page(job: dict[str, Any]) -> str:
    base = _base()
    path = vacancy_path(job)
    canonical = vacancy_public_url(job, base=base)
    json_ld = job_to_jsonld(job, canonical_url=canonical, base=base)
    apply = (job.get("apply_url") or job.get("careers_url") or "").strip()
    desc_html = job.get("description_html") or ""
    if desc_html:
        # Feed HTML is already markup; keep as trusted-ish prototype content
        desc_block = f'<div class="desc">{desc_html}</div>'
    else:
        text = _esc(job.get("description_text") or "")
        desc_block = f'<div class="desc"><p>{text}</p></div>'

    apply_btn = (
        f'<a class="cta" rel="noopener" href="{_esc(apply)}">Apply on careers.epam.com</a>'
        if apply
        else ""
    )
    body = f"""
  <nav class="crumb"><a href="/">Home</a> · <a href="/vacancies">Vacancies</a> · {_esc(job.get("title") or "")}</nav>
  <div class="banner"><strong>PROTOTYPE</strong> — this page is the canonical JobPosting URL for AI/search.
  Application happens on the EPAM careers site.</div>
  <h1>{_esc(job.get("title") or "")}</h1>
  <p class="meta">{_esc(_location_line(job))} · {_esc(job.get("job_type") or "")} ·
     {_esc(job.get("experience_level") or "")}</p>
  <p class="meta">Posted {_esc(job.get("date_posted_iso") or "n/a")} ·
     ID <code>{_esc(job.get("blt") or job.get("id") or "")}</code></p>
  {apply_btn}
  {desc_block}
  <p class="meta"><a href="{_esc(path)}?format=jsonld">JobPosting JSON-LD</a> ·
     <a href="/jobs/{_esc(job.get("blt") or job.get("id") or "")}">API JSON</a></p>
"""
    snippet = (job.get("description_text") or "")[:155]
    return _shell(
        title=f"{job.get('title') or 'Vacancy'} | EPAM AI vacancy index",
        canonical=canonical,
        body=body,
        description=snippet,
        json_ld=json_ld,
    )


def gone_page(job_id: str) -> str:
    body = f"""
  <nav class="crumb"><a href="/">Home</a> · <a href="/vacancies">Vacancies</a></nav>
  <h1>Vacancy no longer open</h1>
  <p>Role <code>{_esc(job_id)}</code> was removed from the live index (HTTP 410 Gone).</p>
  <p><a href="/vacancies">Browse open vacancies</a></p>
"""
    return _shell(
        title="Vacancy gone | EPAM AI vacancy index",
        canonical="",
        body=body,
        robots="noindex,follow",
    )
