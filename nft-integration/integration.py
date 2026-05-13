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
import traceback
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.constants import DID_REGISTRY_ADDRESS, IPFS_GATEWAY, SOULBOUND_ADDRESS

RPC_URL        = os.getenv("RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY    = os.getenv("ISSUER_PRIVATE_KEY") or os.getenv("PRIVATE_KEY", "")
SHARED_ABIS    = Path(__file__).parent.parent / "shared" / "abis"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./backend/ssi.db")
POLL_INTERVAL  = 5


# =========================
# VALIDATION
# =========================
assert PRIVATE_KEY, "Set ISSUER_PRIVATE_KEY or PRIVATE_KEY in .env (key của ví được authorize mint NFT)"
assert SOULBOUND_ADDRESS != "0x0000000000000000000000000000000000000000", "Soulbound not deployed"


# =========================
# CONNECT
# =========================
def get_w3() -> Web3:
    if not RPC_URL or "YOUR_" in RPC_URL:
        raise RuntimeError(
            "RPC_URL trong .env chua hop le (con placeholder YOUR_...). "
            "Dung URL that, vi du https://rpc.sepolia.org hoac Infura/Alchemy."
        )
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    assert w3.is_connected(), f"Cannot connect to RPC: {RPC_URL}"
    return w3


def load_contract(w3: Web3, abi_file: str, address: str):
    abi_path = SHARED_ABIS / abi_file

    if not abi_path.exists():
        raise FileNotFoundError(f"ABI not found: {abi_path}")

    with open(abi_path) as f:
        abi = json.load(f)

    return w3.eth.contract(
        address=Web3.to_checksum_address(address),
        abi=abi
    )


# =========================
# SEND TX
# =========================
def send_tx(w3: Web3, fn) -> str:
    account = w3.eth.account.from_key(PRIVATE_KEY)

    nonce = w3.eth.get_transaction_count(account.address, "pending")

    tx = fn.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 500000,
        "gasPrice": w3.eth.gas_price,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    return tx_hash.hex()


# =========================
# SQLITE
# =========================
def record_mint(owner: str, tx_hash: str):
    try:
        conn = sqlite3.connect(SQLITE_DB_PATH)
        now = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """UPDATE pending_verifications
               SET tx_hash=?, status='confirmed', updated_at=?
               WHERE wallet_address=? AND status='submitted'""",
            (tx_hash, now, owner),
        )

        conn.commit()
        conn.close()

    except Exception as e:
        print(f"[SQLITE ERROR] {e}")


# =========================
# EVENT HANDLERS
# =========================
def handle_document_hash_stored(event, w3: Web3, soulbound):
    owner = event["args"]["owner"]
    cid   = event["args"]["cid"]

    metadata_uri = f"{IPFS_GATEWAY}{cid}"

    print("\n[DocumentHashStored]")
    print(f"Owner: {owner}")
    print(f"CID  : {cid}")

    try:
        owner_checksum = Web3.to_checksum_address(owner)

        # Check số lượng token (tránh crash DynArray)
        tokens = soulbound.functions.getTokensOfOwner(owner_checksum).call()

        if len(tokens) >= 20:
            print("→ Max token reached (20)")
            return

        # Mint NFT
        tx_hash = send_tx(
            w3,
            soulbound.functions.mint(
                owner_checksum,
                "Document",  # TODO: có thể dynamic
                metadata_uri
            )
        )

        print(f"→ Minted NFT, tx = {tx_hash}")

        record_mint(owner, tx_hash)

    except Exception as e:
        print(f"[ERROR mint] {e}")
        traceback.print_exc()


def handle_did_revoked(event, w3: Web3, soulbound):
    owner = event["args"]["owner"]

    print("\n[DIDRevoked]")
    print(f"Owner: {owner}")

    try:
        owner_checksum = Web3.to_checksum_address(owner)

        tokens = soulbound.functions.getTokensOfOwner(owner_checksum).call()

        if len(tokens) == 0:
            print("→ No tokens found")
            return

        for token_id in tokens:

            # Check token còn valid không
            is_valid = soulbound.functions.isTokenValid(token_id).call()

            if not is_valid:
                continue

            tx_hash = send_tx(
                w3,
                soulbound.functions.invalidateToken(token_id)
            )

            print(f"→ Invalidated token {token_id}, tx = {tx_hash}")

    except Exception as e:
        print(f"[ERROR revoke] {e}")
        traceback.print_exc()


# =========================
# LISTENER
# =========================
def listen_and_sync():
    w3 = get_w3()

    did_registry = load_contract(
        w3,
        "DID_Registry.json",
        DID_REGISTRY_ADDRESS
    )

    soulbound = load_contract(
        w3,
        "Soulbound_Contract.json",
        SOULBOUND_ADDRESS
    )

    print("\n===== SSI ORCHESTRATOR =====")
    print(f"DID Registry : {DID_REGISTRY_ADDRESS}")
    print(f"Soulbound    : {SOULBOUND_ADDRESS}")
    print(f"Polling      : {POLL_INTERVAL}s")
    print("===========================\n")

    hash_filter = did_registry.events.DocumentHashStored.create_filter(
        from_block="latest"
    )

    revoke_filter = did_registry.events.DIDRevoked.create_filter(
        from_block="latest"
    )

    while True:
        try:
            # Event: lưu document → mint NFT
            for event in hash_filter.get_new_entries():
                handle_document_hash_stored(event, w3, soulbound)

            # Event: revoke → invalidate NFT
            for event in revoke_filter.get_new_entries():
                handle_did_revoked(event, w3, soulbound)

        except Exception as e:
            print(f"[LOOP ERROR] {e}")
            traceback.print_exc()

        time.sleep(POLL_INTERVAL)


# =========================
# MAIN
# =========================
if __name__ == "__main__":
    listen_and_sync()