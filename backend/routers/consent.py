"""
Router quan ly explicit consent.
Nguoi phu trach: Thuy
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.models.database import get_connection

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.constants import CONSENT_ACCESS_DURATION_HOURS

router = APIRouter()


class ConsentRequestBody(BaseModel):
    owner_did: str
    requester_address: str
    data_type: str  # "portrait" | "document" | "metadata"


class ConsentRequestResponse(BaseModel):
    consent_id: int
    status: str


class ConsentRespondBody(BaseModel):
    consent_id: int
    owner_did: str
    decision: str  # "approved" | "rejected"


@router.post("/request", response_model=ConsentRequestResponse)
def request_consent(body: ConsentRequestBody):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO consent_records (owner_did, requester_address, data_type, status, requested_at) VALUES (?, ?, ?, 'pending', ?)",
            (body.owner_did, body.requester_address, body.data_type, now),
        )
        consent_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()
    return ConsentRequestResponse(consent_id=consent_id, status="pending")


@router.post("/respond")
def respond_consent(body: ConsentRespondBody):
    if body.decision not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="decision phai la 'approved' hoac 'rejected'")

    now = datetime.now(timezone.utc)
    expires_at = None
    if body.decision == "approved":
        expires_at = (now + timedelta(hours=CONSENT_ACCESS_DURATION_HOURS)).isoformat()

    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, owner_did FROM consent_records WHERE id=?",
            (body.consent_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Consent record khong ton tai")
        if row["owner_did"] != body.owner_did:
            raise HTTPException(status_code=403, detail="Khong co quyen cap nhat consent nay")

        conn.execute(
            "UPDATE consent_records SET status=?, responded_at=?, expires_at=? WHERE id=?",
            (body.decision, now.isoformat(), expires_at, body.consent_id),
        )
        conn.commit()
    finally:
        conn.close()

    return {"consent_id": body.consent_id, "status": body.decision}


@router.get("/pending/{did}")
def get_pending_consents(did: str):
    """Lay danh sach consent dang cho phan hoi cua owner."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM consent_records WHERE owner_did=? AND status='pending' ORDER BY requested_at DESC",
            (did,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


@router.get("/history/{did}")
def get_consent_history(did: str):
    """
    Lay lich su tat ca consent cua owner (pending + approved + rejected).
    Phuc hop cho User Dashboard va Verifier xem lai lich su.
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM consent_records WHERE owner_did=? ORDER BY requested_at DESC",
            (did,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
