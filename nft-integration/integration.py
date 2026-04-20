"""
Orchestrator: lang nghe event tu DID_Registry va mint/invalidate Soulbound Token.
Nguoi phu trach: Nhu

Chay: python nft-integration/integration.py
"""
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.constants import DID_REGISTRY_ADDRESS, IPFS_GATEWAY, SOULBOUND_ADDRESS

RPC_URL        = os.getenv("RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY    = os.getenv("PRIVATE_KEY", "")
SHARED_ABIS    = Path(__file__).parent.parent / "shared" / "abis"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./backend/ssi.db")
POLL_INTERVAL  = 5  # giay


def get_w3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    assert w3.is_connected(), f"Khong the ket noi RPC: {RPC_URL}"
    return w3


def load_contract(w3: Web3, abi_file: str, address: str):
    abi_path = SHARED_ABIS / abi_file
    if not abi_path.exists():
        raise FileNotFoundError(f"ABI chua co: {abi_path}. Hay deploy contract truoc.")
    with open(abi_path) as f:
        abi = json.load(f)
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def send_tx(w3: Web3, fn) -> str:
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    tx = fn.build_transaction({
        "from":     account.address,
        "nonce":    nonce,
        "gas":      300000,
        "gasPrice": w3.eth.gas_price,
    })
    signed   = account.sign_transaction(tx)
    tx_hash  = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def record_mint(owner: str, tx_hash: str):
    """Ghi nhan tx_hash mint NFT vao SQLite."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    now  = datetime.now(timezone.utc).isoformat()
    conn.execute(
        """UPDATE pending_verifications
           SET tx_hash=?, status='confirmed', updated_at=?
           WHERE wallet_address=? AND status='submitted'""",
        (tx_hash, now, owner),
    )
    conn.commit()
    conn.close()


def handle_document_hash_stored(event, w3: Web3, soulbound):
    """Xu ly event DocumentHashStored: mint Soulbound Token neu chua co."""
    owner = event["args"]["owner"]
    cid   = event["args"]["cid"]
    metadata_uri = f"{IPFS_GATEWAY}{cid}"

    print(f"[DocumentHashStored] owner={owner}, cid={cid}")

    has_token = soulbound.functions.hasValidToken(
        Web3.to_checksum_address(owner)
    ).call()

    if not has_token:
        tx_hash = send_tx(w3, soulbound.functions.mint(
            Web3.to_checksum_address(owner), metadata_uri
        ))
        print(f"  Minted Soulbound Token -> tx={tx_hash}")
        record_mint(owner, tx_hash)
    else:
        print(f"  Da co token, bo qua.")


def handle_did_revoked(event, w3: Web3, soulbound):
    """Xu ly event DIDRevoked: vo hieu hoa Soulbound Token tuong ung."""
    owner = event["args"]["owner"]
    print(f"[DIDRevoked] owner={owner}")

    has_token = soulbound.functions.hasValidToken(
        Web3.to_checksum_address(owner)
    ).call()

    if has_token:
        tx_hash = send_tx(w3, soulbound.functions.invalidateToken(
            Web3.to_checksum_address(owner)
        ))
        print(f"  Invalidated Soulbound Token -> tx={tx_hash}")
    else:
        print(f"  Khong co token de invalidate.")


def listen_and_sync():
    """Lang nghe events tu DID_Registry va dong bo Soulbound Token."""
    w3           = get_w3()
    did_registry = load_contract(w3, "DID_Registry.json", DID_REGISTRY_ADDRESS)
    soulbound    = load_contract(w3, "Soulbound_Contract.json", SOULBOUND_ADDRESS)

    print(f"Lang nghe events tu DID_Registry: {DID_REGISTRY_ADDRESS}")
    print(f"Soulbound Contract              : {SOULBOUND_ADDRESS}")
    print(f"Poll interval                   : {POLL_INTERVAL}s")
    print("Nhan Ctrl+C de dung.\n")

    hash_filter   = did_registry.events.DocumentHashStored.create_filter(from_block="latest")
    revoke_filter = did_registry.events.DIDRevoked.create_filter(from_block="latest")

    while True:
        try:
            for event in hash_filter.get_new_entries():
                handle_document_hash_stored(event, w3, soulbound)

            for event in revoke_filter.get_new_entries():
                handle_did_revoked(event, w3, soulbound)

        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    listen_and_sync()
