#!/usr/bin/env bash
# Single entry point for a one-process deploy (Replit, or anywhere else
# that wants "one run command"): builds the frontend, then serves it +
# the API from the same FastAPI process (see backend/app/main.py).
set -e

cd frontend
npm install
npm run build
cd ../backend

pip install -r requirements.txt

if [ ! -f creditlens.db ]; then
  python3 scripts/seed_demo_companies.py || true
fi

uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
