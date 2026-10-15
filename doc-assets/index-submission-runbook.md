# Index submission runbook (GSC / Bing / IndexNow / Google Indexing API)

**Gate:** do not submit to Google Search Console, Bing Webmaster Tools, IndexNow, or Google Indexing API until the owner explicitly confirms (`INDEX_SUBMIT_OK` or clear approval in chat).

This service is an **independent GEO prototype**. Canonical JobPosting URLs are on this host; careers.epam.com remains the apply destination only.

## Prerequisites

1. Stable public host (`PUBLIC_BASE_URL`), ideally a custom domain (Render URL works for smoke).
2. Live HTML surface: `/`, `/vacancies`, `/vacancies/{slug}`, `/sitemap.xml`, `/robots.txt`, `/llms.txt`.
3. Fresh index: `data/jobs.json.gz` + `data/removed_ids.json` after ingest.
4. Verified ownership of the host in each webmaster tool.

## 1. Google Search Console

1. Add property for the public host.
2. Verify via DNS or HTML meta/file.
3. Submit `https://{host}/sitemap.xml`.
4. Spot-check vacancy URLs with URL Inspection / Rich Results Test.
5. (Optional, JobPosting) enable **Google Indexing API** for publish/update/delete notifications — requires GCP service account + Search Console ownership. Store credentials only under owner gate (`OWNER_CREDENTIALS_OK`).

## 2. Bing Webmaster Tools + IndexNow

1. Add and verify the same host in Bing Webmaster Tools.
2. Submit the sitemap.
3. Generate an IndexNow key (8–128 hex/alphanumeric chars).
4. Host key file at `https://{host}/{KEY}.txt` containing only the key.
5. Set env on Render: `INDEXNOW_KEY={KEY}`, `PUBLIC_BASE_URL=https://{host}`.
6. After approval, refresh pipeline calls `_scripts/notify_indexnow.py` (no-op without key).

Manual dry-run:

```bash
INDEXNOW_KEY=yourkey PUBLIC_BASE_URL=https://epam-ai-vacancies.onrender.com \
  .venv/bin/python _scripts/notify_indexnow.py --lifecycle data/lifecycle-latest.json --dry-run
```

## 3. What not to do

- Do not mass-submit URL spam or fake directories.
- Do not claim ranking / AI-answer guarantees.
- Do not block OAI-SearchBot / PerplexityBot / Bingbot if the goal is AI-search visibility (training crawlers are separately toggled via `ALLOW_AI_TRAINING_CRAWLERS`).

## 4. KPI after submission

| Signal | Where |
|--------|--------|
| Sitemap discovered / indexed | GSC + Bing |
| JobPosting validity | Rich Results / GSC enhancements |
| Crawler hits | `/stats` + stdout `[crawler-hit]` lines (UA alone ≠ verified bot) |
| Time-to-index | New vacancy → first GSC/Bing crawl |
| AI citation smoke | Weekly fixed candidate queries → % citing this host |

## Approval phrase

When ready for live submission, reply with something like:

`INDEX_SUBMIT_OK` — proceed with GSC sitemap + Bing IndexNow for https://{host}
