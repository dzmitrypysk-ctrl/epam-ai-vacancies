#!/usr/bin/env python3
"""stdio MCP server for EPAM AI-native vacancy search.

Run from project root:
  python mcp_server/server.py

Tools:
  search_vacancies — filter by q / skill / country / city / remote
  get_vacancy — full job + JobPosting JSON-LD
  list_locations — country counts
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Import PyPI `mcp` BEFORE putting project root on sys.path (local folder was renamed
# to mcp_server to avoid shadowing the package).
from mcp.server.fastmcp import FastMCP

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from service.store import (
    default_store_path,
    get_job_by_id,
    job_to_jsonld,
    list_countries,
    load_jobs,
    search_jobs,
    summary_card,
)

mcp = FastMCP(
    "epam-ai-native-vacancies",
    instructions=(
        "Search EPAM open vacancies for candidates. "
        "Prefer search_vacancies with country/skill/remote filters, "
        "then get_vacancy for full detail and careers_url to cite."
    ),
)

_CACHE = None


def _jobs():
    global _CACHE
    if _CACHE is None:
        _CACHE = load_jobs(default_store_path())
    return _CACHE


@mcp.tool()
def search_vacancies(
    q: str = "",
    skill: str = "",
    country: str = "",
    city: str = "",
    remote: bool | None = None,
    limit: int = 10,
) -> str:
    """Search EPAM open vacancies.

    Args:
        q: Free-text tokens (all must match title/description/location).
        skill: Skill or technology keyword.
        country: Country name, e.g. Poland, India, Argentina.
        city: City name, e.g. Pune, Krakow.
        remote: If true, only remote; if false, exclude remote; omit for any.
        limit: Max results (1-50).
    """
    data = _jobs()
    page, total = search_jobs(
        data["jobs"],
        q=q or None,
        skill=skill or None,
        country=country or None,
        city=city or None,
        remote=remote,
        limit=min(max(limit, 1), 50),
    )
    payload = {
        "total": total,
        "returned": len(page),
        "results": [summary_card(j) for j in page],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


@mcp.tool()
def get_vacancy(job_id: str) -> str:
    """Get one vacancy by partnerJobId or BLT id, including JobPosting JSON-LD.

    Args:
        job_id: partnerJobId (e.g. anywhere_blt…_en-us__Poland) or blt… id.
    """
    data = _jobs()
    job = get_job_by_id(data["jobs"], job_id)
    if not job:
        return json.dumps({"error": f"not found: {job_id}"})
    return json.dumps(
        {"job": job, "jsonld": job_to_jsonld(job)},
        ensure_ascii=False,
        indent=2,
    )


@mcp.tool()
def list_locations() -> str:
    """List countries with open vacancy counts in the index."""
    data = _jobs()
    return json.dumps(
        {
            "meta": data["meta"],
            "countries": list_countries(data["jobs"]),
        },
        ensure_ascii=False,
        indent=2,
    )


def main() -> None:
    try:
        _jobs()
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1) from exc
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
