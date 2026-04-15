"""
FastAPI backend cho he thong SSI.
Nguoi phu trach: Thuy
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.models.database import init_db
from backend.routers import did, ipfs, nft, consent, crypto

load_dotenv()

app = FastAPI(title="SSI Backend API", version="1.0.0")

# CORS
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
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
