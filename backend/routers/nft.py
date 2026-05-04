"""
Router quan ly Soulbound NFT.
Nguoi phu trach: Thuy
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services import blockchain_service

router = APIRouter()


class MintRequest(BaseModel):
    recipient_address: str
    credential_type: str
    metadata_uri: str


@router.post("/mint")
def mint_nft(body: MintRequest):
    """
    Mint Soulbound Token cho nguoi dung.
    credential_type: loai chung chi (vd: "Document", "Identity").
    """
    try:
        tx_hash = blockchain_service.mint_soulbound_token(
            body.recipient_address,
            body.credential_type,
            body.metadata_uri,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"tx_hash": tx_hash, "status": "pending"}


@router.get("/status/{address}")
def nft_status(address: str):
    """Lay danh sach token va trang thai cua mot dia chi."""
    try:
        result = blockchain_service.check_soulbound_token(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.get("/token/{token_id}")
def get_token(token_id: int):
    """Lay thong tin chi tiet cua 1 token theo token_id."""
    try:
        result = blockchain_service.get_soulbound_token_data(token_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@router.post("/invalidate/{token_id}")
def invalidate_token(token_id: int):
    """Vo hieu hoa Soulbound Token theo token_id."""
    try:
        tx_hash = blockchain_service.invalidate_soulbound_token(token_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"tx_hash": tx_hash, "status": "confirmed"}


@router.get("/verify-access/{address}")
def verify_nft_access(address: str):
    """
    Kiem tra quyen truy cap dua tren Soulbound Token (token-gated access).
    Tra ve has_access=True neu dia chi co it nhat 1 token con hieu luc.
    Dung de gate quyen truy cap dich vu theo yeu cau de bai.
    """
    try:
        result = blockchain_service.verify_nft_access(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
