# EPAM AI-native vacancy visibility — stakeholder one-pager

**Audience:** Careers platform / VMT / TA job-postings owners  
**Date:** 2026-08-31  
**Prototype:** `projects/ai-native-vacancy-service/` (local REST + MCP over LinkedIn XML inventory)

---

## Problem

Candidates increasingly ask **ChatGPT, Perplexity, Google AI** (and agent tools) for open roles — not only LinkedIn or Google classic SERP.

EPAM already ships a **LinkedIn partner XML feed** (`vacancies.careers.epam.com/api/feed/linkedin`). That feed is for **LinkedIn ingest**, not for LLM crawlers. AI tools do not reliably treat partner XML as “jobs to recommend.”

If we want models to **see, rank, and cite** EPAM vacancies, we need:

1. **Crawlable, structured career pages** (standards / GEO), and  
2. Optionally a **first-class machine API** that agents can call (AI-native service).

---

## Audit snapshot (careers.epam.com, 2026-08-31)

| Check | Result |
|-------|--------|
| `robots.txt` | `User-agent: * Allow: /` (application/api paths blocked — OK) |
| Sitemap | Declared: `https://careers.epam.com/sitemap.xml.gz` |
| Vacancy HTML | Server-rendered content visible to GPTBot-like UA |
| JSON-LD `JobPosting` | **Present** (title, description, datePosted, validThrough, hiringOrganization, identifier, TELECOMMUTE + country for remote) |
| Gaps | No `baseSalary`; no `directApply` in sampled markup; Indexing API / public `llms.txt` unknown or missing |
| Feed host | `vacancies.careers.epam.com` not public outside EPAM network |

**Implication:** Level 1 foundation is partially there. Closing schema gaps + Indexing API + agent index files is the fastest path to better Google AI / crawler citation. Level 2 (this prototype) unlocks ChatGPT Actions / Claude MCP / custom agent tools.

---

## Level 1 — Standards (careers site) — recommend for platform backlog

1. **Complete JobPosting** on every live vacancy URL  
   - Keep required fields; add **`directApply: true`** when apply is on EPAM domain.  
   - Add **`baseSalary`** where policy allows (largest AI-ranking gap vs peers).  
   - Ensure onsite roles emit **`jobLocation`** (Place), remote keep TELECOMMUTE + `applicantLocationRequirements`.  
   - Content–schema parity: every JSON-LD fact visible in HTML.

2. **Hygiene**  
   - Closed roles → 404/410 or strip JobPosting immediately.  
   - Google **Indexing API** for publish/unpublish (JobPosting-scoped).

3. **Agent discovery files**  
   - `/llms.txt` (+ optional `/llms-full.txt`) pointing to careers search, sitemap, and (if shipped) the public jobs API.  
   - Confirm AI bots (GPTBot, ClaudeBot, PerplexityBot, etc.) remain allowed unless Security mandates otherwise.

4. **Do not** position LinkedIn XML as the AI SEO surface.

---

## Level 2 — AI-native vacancy service (prototype in this repo)

```text
LinkedIn XML feed / snapshot
        → ingest_feed.py
        → data/jobs.json (normalized slots)
        → FastAPI /jobs + /llms.txt + OpenAPI
        → MCP tools: search_vacancies, get_vacancy, list_locations
```

**What the demo proves**

- Agent can search “Java remote Poland”, “BA Mexico”, “Salesforce Romania” and get **careers URLs** + **JobPosting JSON-LD**.  
- Same inventory powering LinkedIn slots can power **LLM tools** without scraping LinkedIn.  
- OpenAPI is ready for a **Custom GPT / ChatGPT Action** once hosted publicly.

**Prototype limits**

- Local only (127.0.0.1:8977); not production SSO/rate-limits/CDN.  
- Salary placeholder only (feed has no compensation).  
- Search is keyword-based (not semantic embeddings) — enough for demo; production should add embeddings / ranking.

**Production sketch**

| Piece | Owner (suggested) |
|-------|-------------------|
| Canonical job API (read) sourced from VMT/ContentStack, not only LI XML | Careers / VMT platform |
| Public host + auth (API key / OAuth for partners) | Platform + Security |
| MCP server in EPAM agent catalog | TA automation / Platform |
| GPT Action registration | Growth / Employer brand + Platform |
| Metrics: AI referral UTM, citation smoke tests weekly | Job postings / Analytics |

---

## Why “top of AI answers” is not one toggle

Models cite sources that are (a) crawlable, (b) structured, (c) fresh, (d) matched to query intent (skills, location, salary, remote).  
EPAM can **maximize eligibility and citation quality**; no vendor guarantees “always #1” across ChatGPT, Perplexity, and Google AI simultaneously.

Practical KPI set:

1. Rich Results / JobPosting validity rate on careers URLs.  
2. Time-to-index for new/closed roles (Indexing API).  
3. Weekly smoke: N candidate queries → share of answers citing `careers.epam.com`.  
4. (If Level 2 ships) Action/MCP call volume and apply CTR from AI referral UTMs.

---

## Ask / next decisions

1. Approve Level 1 schema + Indexing API + `llms.txt` as careers-platform backlog.  
2. Decide whether Level 2 becomes a **public** jobs API (recommended) or stays internal agent-only.  
3. Policy on publishing salary ranges in schema (biggest content gap for AI match).  
4. Demo walkthrough of local prototype (`README.md` in this project).

---

## References

- Prototype README: `projects/ai-native-vacancy-service/README.md`  
- Feed slot definition: `projects/job-postings-okr/AGENTS.md`  
- schema.org JobPosting / Google for Jobs docs (external)  
- Sample live vacancy (audit): `https://careers.epam.com/en/vacancy/bltznvhmn0uymjakiwu_en?country=Argentina`
