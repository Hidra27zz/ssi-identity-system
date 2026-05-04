"""
Router quan ly ma hoa RSA.
Nguoi phu trach: Thuy
"""
from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.database import get_connection
from backend.services.crypto_service import generate_rsa_keypair

router = APIRouter()


class GenerateKeypairRequest(BaseModel):
    wallet_address: str


class GenerateKeypairResponse(BaseModel):
    public_key: str
    private_key: str
    message: str


@router.post("/generate-keypair", response_model=GenerateKeypairResponse)
def generate_keypair(body: GenerateKeypairRequest):
    """
    Tao cap khoa RSA moi cho nguoi dung.
    Public key duoc luu vao did_cache.
    Private key tra ve cho nguoi dung tu bao quan - KHONG luu DB.
    """
    public_key, private_key = generate_rsa_keypair()

    now = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO did_cache (wallet_address, did, status, public_key_pem, last_synced_at, created_at)
            VALUES (?, ?, 'pending', ?, ?, ?)
            ON CONFLICT(wallet_address) DO UPDATE
            SET public_key_pem=excluded.public_key_pem, last_synced_at=excluded.last_synced_at
            """,
            (body.wallet_address, "", public_key, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    return GenerateKeypairResponse(
        public_key=public_key,
        private_key=private_key,
        message="Luu private key o noi an toan. He thong khong luu private key.",
    )
