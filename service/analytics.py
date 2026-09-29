"""Request analytics: in-memory ring buffer + bot/client classification."""

from __future__ import annotations

import os
import re
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any
from urllib.parse import parse_qs, urlparse

MAX_EVENTS = 2000
SKIP_PATHS = frozenset({"/health", "/favicon.ico"})

_BOT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("gptbot", re.compile(r"gptbot|chatgpt-user|oai-searchbot", re.I)),
    ("claudebot", re.compile(r"claudebot|anthropic-ai|claude-web", re.I)),
    ("perplexitybot", re.compile(r"perplexitybot|perplexity-user", re.I)),
    ("googlebot", re.compile(r"googlebot|google-extended|google-inspectiontool", re.I)),
    ("bingbot", re.compile(r"bingbot|msnbot", re.I)),
    ("curl", re.compile(r"^curl/", re.I)),
    ("python", re.compile(r"python-requests|python-urllib|aiohttp|httpx", re.I)),
    ("smoke", re.compile(r"epam-vacancy-smoke|epam-ai-native", re.I)),
]


def classify_client(user_agent: str) -> str:
    ua = (user_agent or "").strip()
    if not ua:
        return "unknown"
    for name, pattern in _BOT_PATTERNS:
        if pattern.search(ua):
            return name
    if re.search(r"Mozilla/|Chrome/|Safari/|Firefox/|Edg/", ua):
        return "browser"
    if re.search(r"openapi|swagger|fastapi", ua, re.I):
        return "openapi"
    return "unknown"


def _extract_search_params(query: str) -> dict[str, str]:
    if not query:
        return {}
    parsed = parse_qs(query, keep_blank_values=False)
    out: dict[str, str] = {}
    for key in ("q", "skill", "country", "city"):
        vals = parsed.get(key)
        if vals and vals[0]:
            out[key] = vals[0][:120]
    if "remote" in parsed and parsed["remote"]:
        out["remote"] = parsed["remote"][0]
    return out


@dataclass
class RequestEvent:
    ts: float
    path: str
    method: str
    query: str
    user_agent: str
    referer: str
    client_class: str
    status_code: int
    duration_ms: float
    search_params: dict[str, str] = field(default_factory=dict)


class AnalyticsStore:
    def __init__(self, max_events: int = MAX_EVENTS) -> None:
        self._events: deque[RequestEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def record(self, event: RequestEvent) -> None:
        with self._lock:
            self._events.append(event)

    def summary(self) -> dict[str, Any]:
        with self._lock:
            events = list(self._events)

        if not events:
            return {
                "total_requests": 0,
                "client_classes": {},
                "endpoints": {},
                "search_queries": [],
                "recent": [],
            }

        client_counts = Counter(e.client_class for e in events)
        endpoint_counts = Counter(f"{e.method} {e.path}" for e in events)

        search_hits: Counter[str] = Counter()
        for e in events:
            if e.path != "/jobs" or not e.search_params:
                continue
            parts = [f"{k}={v}" for k, v in sorted(e.search_params.items())]
            search_hits["&".join(parts)] += 1

        recent = []
        for e in events[-50:][::-1]:
            recent.append(
                {
                    "time": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(e.ts)),
                    "client_class": e.client_class,
                    "method": e.method,
                    "path": e.path,
                    "query": e.query[:200] if e.query else "",
                    "user_agent": (e.user_agent or "")[:100],
                    "status": e.status_code,
                    "duration_ms": round(e.duration_ms, 1),
                }
            )

        return {
            "total_requests": len(events),
            "client_classes": dict(client_counts.most_common()),
            "endpoints": dict(endpoint_counts.most_common(20)),
            "search_queries": [
                {"query": q, "count": c} for q, c in search_hits.most_common(15)
            ],
            "recent": recent,
        }


STORE = AnalyticsStore()


def stats_token_ok(token: str | None) -> bool:
    expected = os.environ.get("STATS_TOKEN", "").strip()
    if not expected:
        return True
    return bool(token) and token == expected


def event_to_dict(event: RequestEvent) -> dict[str, Any]:
    return asdict(event)
