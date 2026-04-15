"""
Orchestrator: lang nghe event tu DID_Registry va mint Soulbound Token.
Nguoi phu trach: Nhu

Chay: python integration.py
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.constants import DID_REGISTRY_ADDRESS, IPFS_GATEWAY, SOULBOUND_ADDRESS

RPC_URL = os.getenv("RPC_URL", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
SHARED_ABIS = Path(__file__).parent.parent / "shared" / "abis"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./backend/ssi.db")


def get_w3():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    assert w3.is_connected(), "Khong the ket noi RPC"
    return w3


def load_contract(w3, abi_file, address):
    with open(SHARED_ABIS / abi_file) as f:
        abi = json.load(f)
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def mint_token(w3, soulbound, recipient: str, metadata_uri: str) -> str:
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    tx = soulbound.functions.mint(
        Web3.to_checksum_address(recipient), metadata_uri
    ).build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def record_mint(tx_hash: str, recipient: str):
    """Ghi nhan tx_hash vao SQLite."""
    import sqlite3
    conn = sqlite3.connect(SQLITE_DB_PATH)
    now = datetime.now(timezone.utc).isoformat()
    conn.execute(
        "UPDATE pending_verifications SET tx_hash=?, status='confirmed', updated_at=? WHERE wallet_address=? AND status='submitted'",
        (tx_hash, now, recipient),
    )
    conn.commit()
    conn.close()


def listen_and_mint():
    """Lang nghe event DocumentHashStored va mint Soulbound Token."""
    w3 = get_w3()
    did_registry = load_contract(w3, "DID_Registry.json", DID_REGISTRY_ADDRESS)
    soulbound = load_contract(w3, "Soulbound_Contract.json", SOULBOUND_ADDRESS)

    print(f"Lang nghe event DocumentHashStored tu {DID_REGISTRY_ADDRESS}...")
    event_filter = did_registry.events.DocumentHashStored.create_filter(from_block="latest")

    while True:
        try:
            for event in event_filter.get_new_entries():
                owner = event["args"]["owner"]
                cid = event["args"]["cid"]
                metadata_uri = f"{IPFS_GATEWAY}{cid}"

                print(f"Nhan event: owner={owner}, cid={cid}")

                # Kiem tra da co token chua
                has_token = soulbound.functions.hasValidToken(
                    Web3.to_checksum_address(owner)
                ).call()

                if not has_token:
                    tx_hash = mint_token(w3, soulbound, owner, metadata_uri)
                    print(f"Minted Soulbound Token cho {owner}: tx={tx_hash}")
                    record_mint(tx_hash, owner)
                else:
                    print(f"Dia chi {owner} da co Soulbound Token, bo qua.")

        except Exception as e:
            print(f"Loi: {e}")

        time.sleep(5)


if __name__ == "__main__":
    listen_and_mint()
