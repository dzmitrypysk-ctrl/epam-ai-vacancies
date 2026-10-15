"""Request analytics: in-memory ring buffer + bot/client classification."""

from __future__ import annotations

import os
import re
import sys
import time
from collections import Counter, deque
from dataclasses import asdict, dataclass, field
from threading import Lock
from typing import Any
from urllib.parse import parse_qs

MAX_EVENTS = 2000
SKIP_PATHS = frozenset({"/health", "/favicon.ico"})

# Search/discovery crawlers vs training crawlers are classified separately
# so training opt-out does not hide search visibility metrics.
_BOT_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("oai-searchbot", re.compile(r"oai-searchbot", re.I)),
    ("gptbot", re.compile(r"gptbot", re.I)),
    ("chatgpt-user", re.compile(r"chatgpt-user", re.I)),
    ("claude-searchbot", re.compile(r"claude-searchbot", re.I)),
    ("claude-user", re.compile(r"claude-user", re.I)),
    ("claudebot", re.compile(r"claudebot|anthropic-ai|claude-web", re.I)),
    ("perplexitybot", re.compile(r"perplexitybot", re.I)),
    ("perplexity-user", re.compile(r"perplexity-user", re.I)),
    ("googlebot", re.compile(r"googlebot|google-inspectiontool", re.I)),
    ("google-extended", re.compile(r"google-extended", re.I)),
    ("bingbot", re.compile(r"bingbot|msnbot|adidxbot", re.I)),
    ("curl", re.compile(r"^curl/", re.I)),
    ("python", re.compile(r"python-requests|python-urllib|aiohttp|httpx", re.I)),
    ("smoke", re.compile(r"epam-vacancy-smoke|epam-ai-native|cursor-health-check", re.I)),
]

_SEARCH_OR_AI_CLASSES = frozenset(
    {
        "oai-searchbot",
        "gptbot",
        "chatgpt-user",
        "claude-searchbot",
        "claude-user",
        "claudebot",
        "perplexitybot",
        "perplexity-user",
        "googlebot",
        "google-extended",
        "bingbot",
    }
)


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
    client_ip: str = ""


class AnalyticsStore:
    def __init__(self, max_events: int = MAX_EVENTS) -> None:
        self._events: deque[RequestEvent] = deque(maxlen=max_events)
        self._lock = Lock()

    def record(self, event: RequestEvent) -> None:
        with self._lock:
            self._events.append(event)
        if event.client_class in _SEARCH_OR_AI_CLASSES:
            # Durable-ish signal: stdout survives process restarts in host logs
            # (Render logs / launchd). UA alone is not proof of a verified bot.
            print(
                f"[crawler-hit] ts={time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(event.ts))} "
                f"class={event.client_class} {event.method} {event.path}"
                f"{('?' + event.query) if event.query else ''} "
                f"status={event.status_code} ip={event.client_ip or '-'} "
                f"ua={(event.user_agent or '')[:120]}",
                file=sys.stdout,
                flush=True,
            )

    def summary(self) -> dict[str, Any]:
        with self._lock:
            events = list(self._events)

        if not events:
            return {
                "total_requests": 0,
                "client_classes": {},
                "endpoints": {},
                "search_queries": [],
                "crawler_hits": 0,
                "recent": [],
            }

        client_counts = Counter(e.client_class for e in events)
        endpoint_counts = Counter(f"{e.method} {e.path}" for e in events)
        crawler_hits = sum(1 for e in events if e.client_class in _SEARCH_OR_AI_CLASSES)

        search_hits: Counter[str] = Counter()
        for e in events:
            if e.path not in ("/jobs", "/vacancies") or not e.search_params:
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
                    "client_ip": e.client_ip,
                }
            )

        return {
            "total_requests": len(events),
            "client_classes": dict(client_counts.most_common()),
            "endpoints": dict(endpoint_counts.most_common(20)),
            "search_queries": [
                {"query": q, "count": c} for q, c in search_hits.most_common(15)
            ],
            "crawler_hits": crawler_hits,
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
