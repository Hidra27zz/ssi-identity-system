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


# ============================================================
# Schemas
# ============================================================

class CreateDIDRequest(BaseModel):
    wallet_address: str
    did: str

class CreateDIDResponse(BaseModel):
    tx_hash: str
    did: str
    status: str

class StoreHashRequest(BaseModel):
    wallet_address: str
    doc_hash: str        # SHA-256 hex string (64 chars)
    cid: str             # IPFS CID
    creator_address: str

class StoreHashResponse(BaseModel):
    tx_hash: str
    status: str

class UpdateHashRequest(BaseModel):
    wallet_address: str
    new_hash: str
    new_cid: str
    creator_address: str

class VerifyDIDResponse(BaseModel):
    address: str
    is_valid: bool
    did: Optional[str]
    cid: Optional[str]
    status: str
    verified_by: Optional[str]
    update_count: int

class RevokeDIDRequest(BaseModel):
    wallet_address: str


# ============================================================
# Endpoints
# ============================================================

@router.post("/create", response_model=CreateDIDResponse)
def create_did(body: CreateDIDRequest):
    """Tao DID moi cho dia chi vi."""
    try:
        tx_hash = blockchain_service.create_did_on_chain(body.wallet_address, body.did)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain error: {e}")

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO did_cache (wallet_address, did, status, last_synced_at, created_at)
               VALUES (?, ?, 'pending', ?, ?)
               ON CONFLICT(wallet_address) DO UPDATE
               SET did=excluded.did, last_synced_at=excluded.last_synced_at""",
            (body.wallet_address, body.did, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    return CreateDIDResponse(tx_hash=tx_hash, did=body.did, status="pending")


@router.post("/store-hash", response_model=StoreHashResponse)
def store_hash(body: StoreHashRequest):
    """Creator luu hash tai lieu len blockchain."""
    # Kiem tra wallet co trong cache va lay did truoc
    conn = get_connection()
    try:
        cache_row = conn.execute(
            "SELECT did FROM did_cache WHERE wallet_address=?",
            (body.wallet_address,),
        ).fetchone()
    finally:
        conn.close()

    if not cache_row or not cache_row["did"]:
        raise HTTPException(status_code=404, detail="Wallet address chua co DID trong cache. Hay tao DID truoc.")

    did_str = cache_row["did"]

    # Goi blockchain truoc, neu thanh cong moi ghi DB
    try:
        tx_hash = blockchain_service.store_hash_on_chain(
            body.wallet_address, body.doc_hash, body.cid
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain error: {e}")

    # Blockchain thanh cong -> ghi DB
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO pending_verifications
               (wallet_address, did, doc_hash, ipfs_cid, creator_address, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, 'submitted', ?, ?)""",
            (body.wallet_address, did_str,
             body.doc_hash, body.cid, body.creator_address, now, now),
        )
        conn.execute(
            "UPDATE did_cache SET status='verified', ipfs_cid=?, last_synced_at=? WHERE wallet_address=?",
            (body.cid, now, body.wallet_address),
        )
        conn.commit()
    finally:
        conn.close()

    return StoreHashResponse(tx_hash=tx_hash, status="pending")


@router.post("/update-hash", response_model=StoreHashResponse)
def update_hash(body: UpdateHashRequest):
    """Creator cap nhat hash tai lieu sau khi da xac minh."""
    try:
        tx_hash = blockchain_service.update_hash_on_chain(
            body.wallet_address, body.new_hash, body.new_cid
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain error: {e}")

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE did_cache SET ipfs_cid=?, last_synced_at=? WHERE wallet_address=?",
            (body.new_cid, now, body.wallet_address),
        )
        conn.commit()
    finally:
        conn.close()

    return StoreHashResponse(tx_hash=tx_hash, status="pending")


@router.get("/verify/{address}", response_model=VerifyDIDResponse)
def verify_did(address: str):
    """Kiem tra DID co hop le khong."""
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
        verified_by=result.get("verified_by"),
        update_count=result.get("update_count", 0),
    )


@router.get("/record/{address}")
def get_did_record(address: str):
    """Lay toan bo thong tin DID tu blockchain, bao gom created_at, verified_at, updated_at."""
    try:
        return blockchain_service.get_did_record_full(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/revoke")
def revoke_did(body: RevokeDIDRequest):
    """
    Thu hoi DID.
    Tu dong invalidate tat ca Soulbound Token con hieu luc cua dia chi nay.
    """
    try:
        tx_hash = blockchain_service.revoke_did_on_chain(body.wallet_address)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain error: {e}")

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

    # Tu dong invalidate tat ca Soulbound Token con hieu luc
    # Loi o buoc nay khong lam fail request revoke DID
    invalidated_txs = []
    try:
        invalidated_txs = blockchain_service.invalidate_all_tokens_of_owner(body.wallet_address)
    except Exception as e:
        print(f"[WARN] Could not invalidate NFTs for {body.wallet_address}: {e}")

    return {
        "tx_hash":        tx_hash,
        "status":         "confirmed",
        "invalidated_nft_txs": invalidated_txs,
    }


@router.get("/stats")
def get_stats():
    """Lay thong ke he thong: tong DID va tong da xac minh."""
    try:
        return blockchain_service.get_did_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/public-key/{address}")
def get_public_key(address: str):
    """
    Lay public key RSA cua mot dia chi vi tu did_cache.
    Creator dung endpoint nay de lay public key truoc khi ma hoa file.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT public_key_pem FROM did_cache WHERE wallet_address=?",
            (address,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Khong tim thay thong tin cho dia chi nay")
    if not row["public_key_pem"]:
        raise HTTPException(status_code=404, detail="Nguoi dung chua tao keypair RSA")

    return {"wallet_address": address, "public_key_pem": row["public_key_pem"]}


@router.get("/pending")
def get_pending_verifications():
    """Lay danh sach DID dang cho Creator xac minh."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM pending_verifications WHERE status='submitted' ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
