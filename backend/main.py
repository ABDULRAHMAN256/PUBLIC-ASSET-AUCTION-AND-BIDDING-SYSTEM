# main.py — FastAPI application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import init_db
from routes import auth

app = FastAPI(
    title="Uganda Public Asset Auction API",
    version="1.0.0",
    description="Backend for the Public Asset Auction and Bidding System.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    created = init_db()
    print("[db] schema applied" if created else "[db] schema already exists")

@app.get("/api/health", tags=["System"])
def health():
    return {"ok": True}

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
