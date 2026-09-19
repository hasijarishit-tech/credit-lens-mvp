# CreditLens (MSME Credit Risk Meter) — Hackathon MVP

A credit-risk scoring tool for Indian MSMEs. Reads balance sheet + P&L data
(via PDF, manual entry, a public source link, or company-name search),
computes financial ratios and a derived cash flow, flags anomalies, and
produces a letter-grade credit score — with a plain-English coaching view
for MSMEs and a portfolio screening view for lenders.

## Where things live

```
credit-lens-mvp/
  backend/                    <- Python API server (FastAPI)
    app/
      main.py                  entry point; wires all routers together
      config.py                reads settings from .env
      database.py               SQLite connection setup
      models.py                 database tables (users, companies,
                                 financial records, scores)
      schemas.py                shapes of data the API accepts/returns
      auth.py                   password hashing + login token logic
      known_companies.py        the small hand-verified index name-search
                                 matches against (see note below)
      routers/
        auth.py                  signup / login / "who am I"
        companies.py             create/list/get companies
        financial_records.py     all 4 intake paths + corrections + scoring
        name_search.py           search + confirm
        scenario.py              lender scenario Q&A (preset what-ifs)
      scoring/                  the deterministic engine — NO Claude
                                 calls anywhere in this folder
        benchmarks.py            sector benchmark medians (illustrative)
        sanity.py                pre-scoring balance/scale checks
        cashflow.py              indirect-method operating cash flow
        ratios.py                the 12 ratios across 4 buckets
        score.py                 composite score + letter grade
        anomalies.py             the 4 anomaly flag checks
        preset_scenarios.py      no-key scenario Q&A (fixed what-if menu)
        pipeline.py              orchestrates all of the above
      llm/                      Claude-powered versions (used automatically
                                 once you add an API key)
        extraction.py, narrative.py, scenario.py
      extraction/               the no-key fallback path
        rule_based.py            generic keyword-matching extractor
        screener_parser.py       Screener.in-specific parser (see note)
        router.py                picks Claude vs. fallback automatically
      narrative/                 templated no-key coaching/analyst text
      utils/
        pdf_text.py               PDF -> text (pypdf)
        web_fetch.py              URL -> text, with SSRF guards
        records.py                small shared helpers
    scripts/
      seed_demo_companies.py    loads the 3 real demo companies (below)
    uploads/                   (reserved; not currently used — PDFs are
                                 read in-memory and not persisted to disk)
    requirements.txt
    .env.example                template for secrets/config (copy to .env)

  frontend/                    <- React + Vite + Tailwind
    src/
      api/client.js             axios instance, attaches the login token
      context/AuthContext.jsx   login/signup/logout state
      components/                shared UI: forms, ratio table, bucket
                                  bars, anomaly flags, grade badge, layout
      pages/
        Login.jsx, Signup.jsx
        IntakePage.jsx           shared 4-path intake screen (both roles)
        ReviewPage.jsx           shared extraction review screen
        msme/                    MyScorePage, ScoreResultPage
        lender/                  PortfolioPage, DrilldownPage (+ scenario Q&A)
```

## What's built (Stages 1–3 complete)

- **Auth** for both MSME and lender accounts (signup, login, JWT sessions).
- **All 4 intake paths**: manual entry, PDF upload, a public source-link
  fetch, and name-search-with-confirmation — each tagged with its source
  type and self-reported/verified trust label.
- **The scoring engine**: sanity checks, indirect-method cash flow,
  12 ratios across 4 buckets, sector-benchmarked composite score + letter
  grade, and 4 kinds of anomaly flags — all pure Python, hand-verified,
  and fully independent of any LLM.
- **AI narrative + extraction**, with automatic fallback: if you add an
  `ANTHROPIC_API_KEY`, extraction and coaching/analyst text are written by
  Claude; without one, extraction falls back to keyword matching (plus a
  Screener.in-specific parser), and narratives fall back to sentence
  templates filled with the real computed numbers. Nothing needs to be
  rebuilt when a key is added later — it's picked up automatically.
- **Scenario Q&A**: with a key, free-text questions; without one, a fixed
  menu of what-if buttons (receivables +50%, revenue -20%, etc.) — both
  recompute the actual scoring engine, never a made-up answer.
- **Full frontend** for both roles, wired to the real API.

**A note on name-search:** a live web-search integration needs its own
paid API (Google/Bing/SerpAPI). Since this build avoids new paid
dependencies, name-search matches against a small index of companies
we've already confirmed are fetchable (`known_companies.py`) rather than
crawling the live web. This is an honest, working version of the feature
— for almost any real MSME name you search, it will correctly find no
match and point you to PDF upload or manual entry instead, which is
exactly the behavior the product spec calls for anyway.

## The 3 demo companies

`backend/scripts/seed_demo_companies.py` loads three **real** BSE
SME/NSE Emerge companies (sourced from their public Screener.in pages),
scored by the actual engine:

| Company | Sector | Grade | Notable flag |
|---|---|---|---|
| Fascinate Textiles Ltd | Manufacturing | BBB (61.2) | Profit without cash — inventory ballooned |
| Propshop Events and Exhibitions Ltd | Services | A (83.5) | Receivables outpacing revenue |
| Galaxy Supermarket Ltd | Trading | BB (41.6) | Negative equity |

They're owned by a demo lender account: `demo-lender@creditlens.dev` /
`demo-password-123`.

## Running it locally

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add ANTHROPIC_API_KEY here if/when you have one
uvicorn app.main:app --reload --port 8000
python3 scripts/seed_demo_companies.py   # optional: load the 3 demo companies
```
Visit `http://127.0.0.1:8000/docs` for an interactive API test page.

**Frontend:**
```bash
cd frontend
npm install
cp .env.example .env        # points at the backend above by default
npm run dev
```
Visit `http://localhost:5173`.

## Key decisions made along the way

- **SQLite**, not Postgres — one file, nothing to install, swappable later.
- **FastAPI (Python)** backend — cleanest Claude API integration story.
- One `users` table with a `role` field, not two separate tables.
- No migrations tool — tables auto-create on startup.
- **Fallback-first architecture**: every AI-dependent feature (extraction,
  narrative, scenario Q&A) has a working non-AI version, with a router
  that picks Claude automatically the moment a key is configured.
- Ratio math never imports anything from `app/llm` or `app/narrative` —
  the scoring engine is provably independent of the AI layer.

## Known limitations worth knowing about

- The Screener.in parser reconstructs receivables/inventory/payables from
  aggregated figures (Screener doesn't expose them as line items) —
  medium confidence, clearly flagged in the Extraction Review screen.
- The rule-based (non-Screener) extractor only recognizes a fixed list of
  English/Indian label variants; anything it doesn't recognize defaults
  to 0 with a warning rather than guessing.
- Preset scenarios keep net income internally consistent with the
  scenario (e.g. a revenue drop also reduces profit), but only for the
  specific fields each preset touches — they're illustrative "what ifs,"
  not a full financial model.

## Roadmap (explicitly out of scope for this MVP)

- OCR for scanned (non-native-text) PDFs
- A live web-search API for name-search (currently a hand-verified index)
- Bypassing logins/paywalls on gated data aggregators (Tofler, Zauba, etc.)
- Live data pulls from MCA / GST / bank statement APIs
- Regulatory/compliance infrastructure for real lending decisions
- Mobile app or mobile-optimized UI
- Payment/subscription billing for lenders
