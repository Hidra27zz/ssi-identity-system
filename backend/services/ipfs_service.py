"""
Dich vu upload/retrieve IPFS qua Pinata API.
Nguoi phu trach: Thuy
"""
import asyncio
import os
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

PINATA_API_KEY = os.getenv("IPFS_API_KEY", "")
PINATA_SECRET_KEY = os.getenv("IPFS_SECRET_KEY", "")
IPFS_GATEWAY = os.getenv("IPFS_GATEWAY", "https://gateway.pinata.cloud/ipfs/")
PINATA_UPLOAD_URL = "https://api.pinata.cloud/pinning/pinFileToIPFS"
PINATA_JSON_URL = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
MAX_RETRIES = 3


class IPFSUnavailableError(Exception):
    pass


async def upload_to_ipfs(encrypted_bytes: bytes, filename: str) -> str:
    """
    Upload bytes len IPFS qua Pinata. Retry toi da 3 lan.
    Tra ve CID khi thanh cong.
    """
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY,
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                files = {"file": (filename, encrypted_bytes, "application/octet-stream")}
                response = await client.post(PINATA_UPLOAD_URL, headers=headers, files=files)
                response.raise_for_status()
                return response.json()["IpfsHash"]
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise IPFSUnavailableError(f"IPFS upload failed after {MAX_RETRIES} attempts: {e}")
            await asyncio.sleep(2 ** attempt)

    raise IPFSUnavailableError("IPFS upload failed")


async def retrieve_from_ipfs(cid: str) -> bytes:
    """Tai file tu IPFS theo CID."""
    url = f"{IPFS_GATEWAY}{cid}"
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.content


async def upload_json_to_ipfs(data: dict) -> str:
    """Upload JSON metadata len IPFS."""
    headers = {
        "pinata_api_key": PINATA_API_KEY,
        "pinata_secret_api_key": PINATA_SECRET_KEY,
        "Content-Type": "application/json",
    }
    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(PINATA_JSON_URL, headers=headers, json={"pinataContent": data})
                response.raise_for_status()
                return response.json()["IpfsHash"]
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise IPFSUnavailableError(f"IPFS JSON upload failed after {MAX_RETRIES} attempts: {e}")
            await asyncio.sleep(2 ** attempt)

    raise IPFSUnavailableError("IPFS JSON upload failed")


def build_metadata_json(
    did: str,
    doc_type: str,
    issued_by: str,
    portrait_cid: str,
    document_cid: str,
) -> dict:
    """
    Tao metadata JSON chuan. Khong chua PII plaintext.
    """
    return {
        "did": did,
        "documentType": doc_type,
        "issuedBy": issued_by,
        "portraitCID": portrait_cid,
        "documentCID": document_cid,
        "createdAt": datetime.now(timezone.utc).isoformat(),
    }
