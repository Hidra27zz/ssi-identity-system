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
    metadata_uri: str


@router.post("/mint")
def mint_nft(body: MintRequest):
    try:
        tx_hash = blockchain_service.mint_soulbound_token(body.recipient_address, body.metadata_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"tx_hash": tx_hash, "status": "pending"}


@router.get("/status/{address}")
def nft_status(address: str):
    try:
        result = blockchain_service.check_soulbound_token(address)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result
