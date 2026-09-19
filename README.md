# CreditLens (MSME Credit Risk Meter) — Hackathon MVP

A credit-risk scoring tool for Indian MSMEs. Reads balance sheet + P&L data
(via PDF, manual entry, a public source link, or company-name search),
computes financial ratios and a derived cash flow, flags anomalies, and
produces a letter-grade credit score — with a plain-English coaching view
for MSMEs and a portfolio screening view for lenders.

## Where things live

```
credit-lens-mvp/
  backend/              <- Python API server (FastAPI)
    app/
      main.py            entry point; wires everything together
      config.py          reads settings from .env
      database.py        SQLite connection setup
      models.py          the database tables (users, companies, financial
                          records, scores)
      schemas.py         the shapes of data the API accepts/returns
      auth.py            password hashing + login token logic
      routers/
        auth.py           signup / login / "who am I" endpoints
    uploads/             uploaded PDFs will be saved here (Stage 2)
    requirements.txt     Python packages this project needs
    .env.example         template for secrets/config (copy to .env)
  frontend/              <- (not built yet — Stage 3)
```

## Stage 1 — what's built so far

- The database schema: `users`, `companies`, `financial_records`, `scores`.
- Signup and login for both MSME and Lender accounts, with passwords
  stored as secure hashes (never in plain text) and a login token (JWT)
  used to keep a user signed in.
- Tested end to end: signup, login, a protected "who am I" endpoint,
  duplicate-email rejection, and wrong-password rejection all work.

**Decisions made on your behalf (implementation details, no business impact):**
- **SQLite** for the database (a single file, no server to install) rather
  than PostgreSQL. It's a straight drop-in swap later if you ever need to
  scale past a hackathon demo.
- **FastAPI (Python)** for the backend — it has the cleanest Claude API
  integration story for Stage 2 (extraction + narrative), and Python reads
  fairly plainly even without a dev background.
- One `users` table with a `role` field (`msme` or `lender`) rather than
  two separate tables — same login flow, the app just shows a different
  screen based on the role.
- Login tokens last 7 days, so you won't have to keep re-logging-in during
  demo prep.
- No formal database migrations tool (e.g. Alembic) — tables are created
  automatically on server startup. Fine for a hackathon; would need
  revisiting if this became a real product with a live database to preserve.

**Not built yet (later stages):** PDF/link/name-search extraction,
ratio & score calculations, anomaly flags, AI narrative, and all frontend
screens.

## Running the backend locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit .env if needed
uvicorn app.main:app --reload --port 8000
```

Then visit `http://127.0.0.1:8000/docs` for an interactive API test page
(FastAPI generates this automatically — try signup/login there without
writing any code).

## Roadmap (explicitly out of scope for this MVP)

- OCR for scanned (non-native-text) PDFs
- Bypassing logins/paywalls on gated data aggregators (Tofler, Zauba, etc.)
- Live data pulls from MCA / GST / bank statement APIs
- Regulatory/compliance infrastructure for real lending decisions
- Mobile app or mobile-optimized UI
- Payment/subscription billing for lenders
