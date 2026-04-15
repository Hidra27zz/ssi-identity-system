"""
Dich vu tuong tac voi smart contract qua web3.py.
Nguoi phu trach: Thuy
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

RPC_URL = os.getenv("RPC_URL", "")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
SHARED_ABIS = Path(__file__).parent.parent.parent / "shared" / "abis"

# Import constants tu shared
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.constants import DID_REGISTRY_ADDRESS, SOULBOUND_ADDRESS


def get_web3_connection() -> Web3:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError("Khong the ket noi den Ethereum node")
    return w3


def _load_contract(w3: Web3, abi_filename: str, address: str):
    abi_path = SHARED_ABIS / abi_filename
    if not abi_path.exists():
        raise FileNotFoundError(f"ABI chua co: {abi_path}. Hay compile contract truoc.")
    with open(abi_path) as f:
        abi = json.load(f)
    return w3.eth.contract(address=Web3.to_checksum_address(address), abi=abi)


def _send_transaction(w3: Web3, tx) -> str:
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    tx_built = tx.build_transaction({
        "from": account.address,
        "nonce": nonce,
        "gas": 300000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx_built)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    return tx_hash.hex()


def create_did_on_chain(wallet_address: str, did: str) -> str:
    w3 = get_web3_connection()
    contract = _load_contract(w3, "DID_Registry.json", DID_REGISTRY_ADDRESS)
    tx = contract.functions.createDID(did)
    return _send_transaction(w3, tx)


def store_hash_on_chain(wallet_address: str, doc_hash: str, cid: str) -> str:
    w3 = get_web3_connection()
    contract = _load_contract(w3, "DID_Registry.json", DID_REGISTRY_ADDRESS)
    doc_hash_bytes = bytes.fromhex(doc_hash)
    tx = contract.functions.storeDocumentHash(
        Web3.to_checksum_address(wallet_address),
        doc_hash_bytes,
        cid,
    )
    return _send_transaction(w3, tx)


def verify_did_on_chain(wallet_address: str) -> dict:
    w3 = get_web3_connection()
    contract = _load_contract(w3, "DID_Registry.json", DID_REGISTRY_ADDRESS)
    checksum_addr = Web3.to_checksum_address(wallet_address)
    is_valid = contract.functions.verifyDID(checksum_addr).call()
    record = contract.functions.getDIDRecord(checksum_addr).call()
    return {
        "is_valid": is_valid,
        "did": record[1] if record else None,
        "ipfs_cid": record[3] if record else None,
        "status": "active" if is_valid else ("revoked" if record and record[1] else "not_found"),
    }


def revoke_did_on_chain(wallet_address: str) -> str:
    w3 = get_web3_connection()
    contract = _load_contract(w3, "DID_Registry.json", DID_REGISTRY_ADDRESS)
    tx = contract.functions.revokeDID(Web3.to_checksum_address(wallet_address))
    return _send_transaction(w3, tx)


def mint_soulbound_token(recipient: str, metadata_uri: str) -> str:
    w3 = get_web3_connection()
    contract = _load_contract(w3, "Soulbound_Contract.json", SOULBOUND_ADDRESS)
    tx = contract.functions.mint(Web3.to_checksum_address(recipient), metadata_uri)
    return _send_transaction(w3, tx)


def check_soulbound_token(address: str) -> dict:
    w3 = get_web3_connection()
    contract = _load_contract(w3, "Soulbound_Contract.json", SOULBOUND_ADDRESS)
    checksum_addr = Web3.to_checksum_address(address)
    has_token = contract.functions.hasValidToken(checksum_addr).call()
    token_data = contract.functions.getTokenData(checksum_addr).call()
    return {
        "has_valid_token": has_token,
        "token_id": token_data[1] if token_data else None,
        "metadata_uri": token_data[2] if token_data else None,
    }
