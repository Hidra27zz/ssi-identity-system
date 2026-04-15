"""
Router quan ly DID.
Nguoi phu trach: Thuy
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.database import get_connection
from backend.services import blockchain_service

router = APIRouter()


class CreateDIDRequest(BaseModel):
    wallet_address: str
    did: str


class CreateDIDResponse(BaseModel):
    tx_hash: str
    did: str
    status: str


class StoreHashRequest(BaseModel):
    wallet_address: str
    doc_hash: str
    cid: str
    creator_address: str


class StoreHashResponse(BaseModel):
    tx_hash: str
    status: str


class VerifyDIDResponse(BaseModel):
    address: str
    is_valid: bool
    did: Optional[str]
    cid: Optional[str]
    status: str


class RevokeDIDRequest(BaseModel):
    wallet_address: str


@router.post("/create", response_model=CreateDIDResponse)
def create_did(body: CreateDIDRequest):
    try:
        tx_hash = blockchain_service.create_did_on_chain(body.wallet_address, body.did)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO did_cache (wallet_address, did, status, last_synced_at, created_at)
            VALUES (?, ?, 'active', ?, ?)
            ON CONFLICT(wallet_address) DO UPDATE SET did=excluded.did, last_synced_at=excluded.last_synced_at
            """,
            (body.wallet_address, body.did, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    return CreateDIDResponse(tx_hash=tx_hash, did=body.did, status="pending")


@router.post("/store-hash", response_model=StoreHashResponse)
def store_hash(body: StoreHashRequest):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO pending_verifications
            (wallet_address, did, doc_hash, ipfs_cid, creator_address, status, created_at, updated_at)
            VALUES (?, (SELECT did FROM did_cache WHERE wallet_address=?), ?, ?, ?, 'submitted', ?, ?)
            """,
            (body.wallet_address, body.wallet_address, body.doc_hash, body.cid, body.creator_address, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        tx_hash = blockchain_service.store_hash_on_chain(body.wallet_address, body.doc_hash, body.cid)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return StoreHashResponse(tx_hash=tx_hash, status="pending")


@router.get("/verify/{address}", response_model=VerifyDIDResponse)
def verify_did(address: str):
    try:
        result = blockchain_service.verify_did_on_chain(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return VerifyDIDResponse(
        address=address,
        is_valid=result["is_valid"],
        did=result.get("did"),
        cid=result.get("ipfs_cid"),
        status=result.get("status", "not_found"),
    )


@router.get("/record/{address}")
def get_did_record(address: str):
    try:
        result = blockchain_service.verify_did_on_chain(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/revoke")
def revoke_did(body: RevokeDIDRequest):
    try:
        tx_hash = blockchain_service.revoke_did_on_chain(body.wallet_address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE did_cache SET status='revoked', last_synced_at=? WHERE wallet_address=?",
            (now, body.wallet_address),
        )
        conn.commit()
    finally:
        conn.close()

    return {"tx_hash": tx_hash, "status": "pending"}
