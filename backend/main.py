"""
FastAPI backend cho he thong SSI.
Nguoi phu trach: Thuy

Serve ca frontend va API tu cung 1 server:
  - /api/*        -> REST API endpoints
  - /shared/*     -> shared/constants.js, shared/abis/
  - /             -> frontend/ (user.html, creator.html, verifier.html)
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from backend.models.database import init_db
from backend.routers import did, ipfs, nft, consent, crypto

load_dotenv()

app = FastAPI(title="SSI Backend API", version="1.0.0")

# CORS - cho phep tat ca origins de FE co the goi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers (phai dang ky TRUOC StaticFiles) ──────────────
app.include_router(did.router, prefix="/api/did", tags=["DID"])
app.include_router(ipfs.router, prefix="/api", tags=["IPFS"])
app.include_router(nft.router, prefix="/api/nft", tags=["NFT"])
app.include_router(consent.router, prefix="/api/consent", tags=["Consent"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["Crypto"])


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    """Redirect trang chu ve login.html."""
    return RedirectResponse(url="/login.html")


# ── Static Files (sau tat ca API routes) ─────────────────────
ROOT = Path(__file__).parent.parent

# Serve shared/ tai /shared/ (de FE import ../../shared/constants.js hoat dong)
app.mount("/shared", StaticFiles(directory=str(ROOT / "shared")), name="shared")

# Serve frontend/ tai / (trang chu la index.html hoac user.html)
app.mount("/", StaticFiles(directory=str(ROOT / "frontend"), html=True), name="frontend")
