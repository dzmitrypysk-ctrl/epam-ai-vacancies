#!/usr/bin/env python3
"""Smoke scenarios for REST (+ in-process MCP tool functions).

Usage:
  # API must be running on 127.0.0.1:8977
  .venv/bin/python _scripts/smoke_demo.py
  .venv/bin/python _scripts/smoke_demo.py --base http://127.0.0.1:8977
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def http_get(base: str, path: str, params: dict | None = None) -> tuple[int, object]:
    qs = ""
    if params:
        cleaned = {k: v for k, v in params.items() if v is not None}
        qs = "?" + urllib.parse.urlencode(cleaned)
    url = base.rstrip("/") + path + qs
    req = urllib.request.Request(url, headers={"User-Agent": "epam-vacancy-smoke/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            ctype = resp.headers.get("Content-Type", "")
            if "json" in ctype or body.lstrip().startswith(("{", "[")):
                return resp.status, json.loads(body)
            return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")


def print_section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def show_results(label: str, payload: object) -> None:
    print(f"\n--- {label} ---")
    if isinstance(payload, dict) and "results" in payload:
        print(f"total={payload.get('total')} returned={len(payload.get('results') or [])}")
        for i, r in enumerate(payload.get("results") or [], 1):
            print(
                f"  {i}. {r.get('title')} | {r.get('city') or '-'}, {r.get('country')} | "
                f"{'remote' if r.get('is_remote') else r.get('workplace_type')} | id={r.get('id')}"
            )
            print(f"     {r.get('careers_url')}")
    elif isinstance(payload, str):
        print(payload[:1200])
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2)[:1500])


SCENARIOS = [
    {
        "name": "Java remote Poland",
        "params": {"q": "java", "country": "Poland", "remote": "true", "limit": "5"},
    },
    {
        "name": "JavaScript Argentina",
        "params": {"q": "javascript", "country": "Argentina", "limit": "5"},
    },
    {
        "name": "Business Analyst LatAm (Mexico)",
        "params": {"q": "business analyst", "country": "Mexico", "limit": "5"},
    },
    {
        "name": "Python India",
        "params": {"skill": "python", "country": "India", "limit": "5"},
    },
    {
        "name": "Salesforce Romania",
        "params": {"q": "salesforce", "country": "Romania", "limit": "5"},
    },
]


def run_rest(base: str) -> list[str]:
    failures: list[str] = []
    print_section("REST smoke")
    code, health = http_get(base, "/health")
    print(f"/health → {code} {health}")
    if code != 200 or not (isinstance(health, dict) and health.get("ok")):
        failures.append("health")

    code, llms = http_get(base, "/llms.txt")
    print(f"/llms.txt → {code} chars={len(llms) if isinstance(llms, str) else 'n/a'}")
    if code != 200:
        failures.append("llms.txt")

    code, openapi = http_get(base, "/openapi.json")
    print(f"/openapi.json → {code} keys={list(openapi)[:5] if isinstance(openapi, dict) else type(openapi)}")
    if code != 200:
        failures.append("openapi")

    first_id = None
    for sc in SCENARIOS:
        code, payload = http_get(base, "/jobs", sc["params"])
        show_results(f"REST: {sc['name']} ({code})", payload)
        if code != 200:
            failures.append(sc["name"])
            continue
        if isinstance(payload, dict) and payload.get("results"):
            if first_id is None:
                first_id = payload["results"][0].get("id")
        elif isinstance(payload, dict) and payload.get("total", 0) == 0:
            print("  (zero hits — ok if inventory lacks that combo)")

    if first_id:
        code, detail = http_get(base, f"/jobs/{urllib.parse.quote(first_id, safe='')}", {"format": "both"})
        print(f"\nDetail {first_id} → {code}")
        if isinstance(detail, dict):
            jld = detail.get("jsonld") or {}
            print(f"  jsonld @type={jld.get('@type')} directApply={jld.get('directApply')} url={jld.get('url')}")
            print(f"  has baseSalary placeholder: {'baseSalary' in jld}")
        if code != 200:
            failures.append("detail")
    return failures


def run_mcp_inprocess() -> list[str]:
    """Call MCP tool functions directly (same code path as stdio server)."""
    failures: list[str] = []
    print_section("MCP tools (in-process)")
    # Import after path setup
    from mcp_server import server as mcp_mod

    raw = mcp_mod.search_vacancies(q="java", country="Poland", remote=True, limit=5)
    data = json.loads(raw)
    show_results("MCP search_vacancies Java remote Poland", data)
    if "results" not in data:
        failures.append("mcp_search")

    locs = json.loads(mcp_mod.list_locations())
    print(f"list_locations countries={len(locs.get('countries') or [])} meta_jobs={locs.get('meta', {}).get('job_count')}")

    if data.get("results"):
        jid = data["results"][0]["id"]
        detail = json.loads(mcp_mod.get_vacancy(jid))
        if detail.get("error"):
            failures.append("mcp_get")
        else:
            print(f"get_vacancy ok title={detail['job'].get('title')} jsonld={detail['jsonld'].get('@type')}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8977")
    parser.add_argument("--skip-mcp", action="store_true")
    parser.add_argument("--skip-rest", action="store_true")
    args = parser.parse_args()

    out_dir = ROOT / "runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    failures: list[str] = []
    if not args.skip_rest:
        failures.extend(run_rest(args.base))
    if not args.skip_mcp:
        failures.extend(run_mcp_inprocess())

    print_section("Summary")
    if failures:
        print("FAILURES:", ", ".join(failures))
        return 1
    print("All smoke checks passed.")
    (out_dir / "smoke-demo-latest.txt").write_text(
        "smoke ok\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
