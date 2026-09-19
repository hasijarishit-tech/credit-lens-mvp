from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth, companies, financial_records, name_search, scenario

# Creates tables on startup if they don't exist yet. Fine for a hackathon MVP;
# a real product would use migrations (e.g. Alembic) instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CreditLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    # No cookies are used (auth is a Bearer token), so allowing any origin
    # doesn't expose session data cross-site — fine for a hackathon deploy
    # where the frontend's exact deployed URL isn't known ahead of time.
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(financial_records.router)
app.include_router(name_search.router)
app.include_router(scenario.router)


@app.get("/health")
def health():
    return {"status": "ok"}
