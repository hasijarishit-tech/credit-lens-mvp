from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import auth

# Creates tables on startup if they don't exist yet. Fine for a hackathon MVP;
# a real product would use migrations (e.g. Alembic) instead.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="CreditLens API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)


@app.get("/health")
def health():
    return {"status": "ok"}
