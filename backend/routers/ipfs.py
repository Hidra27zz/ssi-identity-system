"""
Router quan ly IPFS upload/retrieve.
Nguoi phu trach: Thuy

RBAC (Role-Based Access Control):
- Upload file/metadata: chi Identity Creator (co quyen tren blockchain) moi duoc upload
- Retrieve file: bat ky ai co consent duoc phe duyet boi chu so huu
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel

from backend.models.database import get_connection
from backend.services import blockchain_service
from backend.services.crypto_service import decrypt_file, encrypt_file, hash_document
from backend.services.ipfs_service import (
    IPFSUnavailableError,
    build_metadata_json,
    retrieve_from_ipfs,
    upload_json_to_ipfs,
    upload_to_ipfs,
)

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.constants import MAX_DOCUMENT_SIZE, MAX_PORTRAIT_SIZE

router = APIRouter()

ALLOWED_TYPES = {"image/jpeg", "image/png", "application/pdf"}


def _require_creator_role(creator_address: str):
    """
    RBAC check: chi Identity Creator (duoc cap quyen tren blockchain) moi duoc upload.
    Raise 403 neu khong co quyen.
    """
    try:
        is_creator = blockchain_service.is_creator_on_chain(creator_address)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Khong the kiem tra quyen Creator tren blockchain"
        )
    if not is_creator:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied: {creator_address} khong co quyen Identity Creator."
        )


class UploadResponse(BaseModel):
    cid: str
    upload_id: int
    file_type: str
    encrypted: bool
    doc_hash: str


class RetrieveRequest(BaseModel):
    private_key: str
    owner_did: str
    requester_address: str


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile,
    public_key: str = Form(...),
    did: str = Form(...),
    creator_address: str = Form(default=""),
):
    """
    Upload file len IPFS sau khi ma hoa bang public key cua user.
    creator_address: tuy chon, neu co se kiem tra quyen Creator tren blockchain.
    Chap nhan: JPG, PNG, PDF (toi da 10MB).
    """
    if creator_address:
        _require_creator_role(creator_address)

    content_type = file.content_type or ""
    file_bytes = await file.read()
    file_size = len(file_bytes)

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: JPG, PNG, PDF")

    if file_size > MAX_DOCUMENT_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: max 10MB, got {file_size / 1024 / 1024:.2f}MB",
        )

    # Xac dinh loai file de luu vao DB
    if content_type in {"image/jpeg", "image/png"}:
        file_type = "portrait"
    else:
        file_type = "document"

    # Ma hoa va upload
    encrypted = encrypt_file(file_bytes, public_key)
    doc_hash = hash_document(file_bytes)

    try:
        cid = await upload_to_ipfs(encrypted, file.filename or "upload")
    except IPFSUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO upload_history (owner_did, ipfs_cid, file_type, file_size_bytes, encrypted, uploaded_at) VALUES (?, ?, ?, ?, 1, ?)",
            (did, cid, file_type, file_size, now),
        )
        upload_id = cursor.lastrowid
        conn.commit()
    finally:
        conn.close()

    return UploadResponse(cid=cid, upload_id=upload_id, file_type=file_type, encrypted=True, doc_hash=doc_hash)


@router.post("/upload/metadata")
async def upload_metadata(
    did: str = Form(...),
    doc_type: str = Form(...),
    issued_by: str = Form(...),
    portrait_cid: str = Form(...),
    document_cid: str = Form(...),
    creator_address: str = Form(default=""),
):
    """
    Upload metadata JSON len IPFS.
    creator_address: tuy chon, neu co se kiem tra quyen Creator.
    """
    if creator_address:
        _require_creator_role(creator_address)
    metadata = build_metadata_json(did, doc_type, issued_by, portrait_cid, document_cid)
    try:
        cid = await upload_json_to_ipfs(metadata)
    except IPFSUnavailableError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return {"cid": cid, "metadata": metadata}


@router.post("/retrieve/{cid}")
async def retrieve_file(cid: str, body: RetrieveRequest):
    """
    Tai va giai ma file tu IPFS.
    Yeu cau consent da duoc approved va chua het han.
    private_key truyen qua request body, khong qua URL.
    """
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT status, expires_at FROM consent_records
               WHERE owner_did=? AND requester_address=? AND data_type IS NOT NULL
               ORDER BY id DESC LIMIT 1""",
            (body.owner_did, body.requester_address),
        ).fetchone()
    finally:
        conn.close()

    if not row or row["status"] != "approved":
        raise HTTPException(status_code=403, detail="Access denied: no consent from owner")

    if row["expires_at"]:
        expires = datetime.fromisoformat(row["expires_at"])
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=403, detail="Access denied: consent da het han")

    try:
        encrypted_bytes = await retrieve_from_ipfs(cid)
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"IPFS retrieve failed: {e}")

    try:
        file_bytes = decrypt_file(encrypted_bytes, body.private_key)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    return Response(content=file_bytes, media_type="application/octet-stream")


@router.get("/upload/history")
def upload_history(owner_did: str):
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM upload_history WHERE owner_did=? ORDER BY uploaded_at DESC",
            (owner_did,),
        ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]
