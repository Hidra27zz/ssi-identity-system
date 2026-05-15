"""
FastAPI backend cho he thong SSI.
Nguoi phu trach: Thuy
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv

from backend.models.database import init_db
from backend.routers import did, ipfs, nft, consent, crypto, auth

load_dotenv()

app = FastAPI(title="SSI Backend API", version="1.0.0")

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers — phai dang ky TRUOC khi mount StaticFiles
app.include_router(did.router, prefix="/api/did", tags=["DID"])
app.include_router(ipfs.router, prefix="/api", tags=["IPFS"])
app.include_router(nft.router, prefix="/api/nft", tags=["NFT"])
app.include_router(consent.router, prefix="/api/consent", tags=["Consent"])
app.include_router(crypto.router, prefix="/api/crypto", tags=["Crypto"])
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


# Serve shared/ (constants.js, abis/) tai /shared/
SHARED_DIR = Path(__file__).parent.parent / "shared"
app.mount("/shared", StaticFiles(directory=str(SHARED_DIR)), name="shared")

# Serve frontend/ tai / — phai mount SAU tat ca API routes
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
