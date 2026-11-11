# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routes import auth, assets

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("[db] initialized")
    yield

app = FastAPI(
    title="Uganda Public Asset Auction API",
    version="1.0.0",
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
app.include_router(assets.router, prefix="/api/assets", tags=["Assets"])
