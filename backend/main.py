# main.py — FastAPI application entry point
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[db] tables created / verified")
    yield


app = FastAPI(
    title="Uganda Public Asset Auction API",
    version="1.0.0",
    description="Backend for the Public Asset Auction and Bidding System.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", tags=["System"])
def health():
    return {"ok": True}


app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])