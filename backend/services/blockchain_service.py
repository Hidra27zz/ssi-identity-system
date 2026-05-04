"""
Dich vu tuong tac voi smart contract qua web3.py.
Nguoi phu trach: Thuy
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3
from web3.exceptions import ContractLogicError

load_dotenv()

RPC_URL     = os.getenv("RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
SHARED_ABIS = Path(__file__).parent.parent.parent / "shared" / "abis"

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from shared.constants import DID_REGISTRY_ADDRESS, SOULBOUND_ADDRESS

# Trang thai DID - khop voi Vyper contract
STATUS_PENDING   = 0
STATUS_VERIFIED  = 1
STATUS_REVOKED   = 2
STATUS_NOT_FOUND = 255

STATUS_LABELS = {
    STATUS_PENDING:   "pending",
    STATUS_VERIFIED:  "verified",
    STATUS_REVOKED:   "revoked",
    STATUS_NOT_FOUND: "not_found",
}


def get_web3() -> Web3:
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        raise ConnectionError(f"Khong the ket noi den Ethereum node: {RPC_URL}")
    return w3


def _load_abi(filename: str) -> list:
    path = SHARED_ABIS / filename
    if not path.exists():
        raise FileNotFoundError(
            f"ABI chua co: {path}. Hay deploy contract truoc: ape run contracts/deploy"
        )
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def _get_did_contract(w3: Web3):
    abi = _load_abi("DID_Registry.json")
    return w3.eth.contract(
        address=Web3.to_checksum_address(DID_REGISTRY_ADDRESS),
        abi=abi
    )


def _get_soulbound_contract(w3: Web3):
    abi = _load_abi("Soulbound_Contract.json")
    return w3.eth.contract(
        address=Web3.to_checksum_address(SOULBOUND_ADDRESS),
        abi=abi
    )


def _send_tx(w3: Web3, fn) -> str:
    """
    Ky, gui giao dich va cho receipt xac nhan.
    Raise ValueError neu transaction bi revert on-chain.
    Tra ve tx_hash hex.
    """
    account = w3.eth.account.from_key(PRIVATE_KEY)
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    tx = fn.build_transaction({
        "from":     account.address,
        "nonce":    nonce,
        "gas":      300000,
        "gasPrice": w3.eth.gas_price,
    })
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)

    # Cho receipt de biet tx co thanh cong khong (timeout 120s)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status == 0:
        raise ValueError(f"Transaction reverted on-chain. tx={tx_hash.hex()}")

    return tx_hash.hex()


def _parse_revert(e: Exception) -> str:
    msg = str(e)
    if "revert" in msg.lower():
        # Lay phan thong bao sau "revert"
        parts = msg.split("revert")
        return parts[-1].strip().strip("'\"")
    return msg


# ============================================================
# DID Registry functions
# ============================================================

def create_did_on_chain(wallet_address: str, did: str) -> str:
    """
    Goi DID_Registry.createDID().
    Tra ve tx_hash.
    """
    w3 = get_web3()
    contract = _get_did_contract(w3)
    try:
        fn = contract.functions.createDID(did)
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def store_hash_on_chain(wallet_address: str, doc_hash: str, cid: str) -> str:
    """
    Goi DID_Registry.storeDocumentHash().
    doc_hash: hex string 64 ky tu (SHA-256).
    Tra ve tx_hash.
    """
    w3 = get_web3()
    contract = _get_did_contract(w3)
    try:
        doc_hash_bytes = bytes.fromhex(doc_hash)
        fn = contract.functions.storeDocumentHash(
            Web3.to_checksum_address(wallet_address),
            doc_hash_bytes,
            cid,
        )
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def update_hash_on_chain(wallet_address: str, new_hash: str, new_cid: str) -> str:
    """
    Goi DID_Registry.updateDocumentHash().
    Dung khi tai lieu thay doi sau khi da xac minh.
    Tra ve tx_hash.
    """
    w3 = get_web3()
    contract = _get_did_contract(w3)
    try:
        new_hash_bytes = bytes.fromhex(new_hash)
        fn = contract.functions.updateDocumentHash(
            Web3.to_checksum_address(wallet_address),
            new_hash_bytes,
            new_cid,
        )
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def verify_did_on_chain(wallet_address: str) -> dict:
    """
    Goi verifyDID() va getDIDStatus() de kiem tra nhanh tinh hop le.
    Dung cho endpoint GET /verify/{address}.
    Tra ve dict: is_valid, did, ipfs_cid, status, verified_by, update_count.
    """
    w3 = get_web3()
    contract = _get_did_contract(w3)
    addr = Web3.to_checksum_address(wallet_address)

    is_valid = contract.functions.verifyDID(addr).call()
    status_code = contract.functions.getDIDStatus(addr).call()
    record = contract.functions.getDIDRecord(addr).call()

    # record la tuple theo thu tu cac truong trong struct Vyper:
    # (owner, did, doc_hash, ipfs_cid, status, created_at, verified_at, updated_at, verified_by, update_count)
    did_str      = record[1] if record else ""
    ipfs_cid     = record[3] if record else ""
    verified_by  = record[8] if record else ""
    update_count = record[9] if record else 0

    return {
        "is_valid":     is_valid,
        "did":          did_str or None,
        "ipfs_cid":     ipfs_cid or None,
        "status_code":  status_code,
        "status":       STATUS_LABELS.get(status_code, "unknown"),
        "verified_by":  verified_by or None,
        "update_count": update_count,
    }


def get_did_record_full(wallet_address: str) -> dict:
    """
    Lay day du thong tin DID Record tu blockchain.
    Dung cho endpoint GET /record/{address}.
    Tra ve tat ca cac truong trong struct DIDRecord bao gom created_at, verified_at, updated_at.
    """
    w3 = get_web3()
    contract = _get_did_contract(w3)
    addr = Web3.to_checksum_address(wallet_address)

    is_valid = contract.functions.verifyDID(addr).call()
    status_code = contract.functions.getDIDStatus(addr).call()
    record = contract.functions.getDIDRecord(addr).call()

    # record tuple: (owner, did, doc_hash, ipfs_cid, status, created_at, verified_at, updated_at, verified_by, update_count)
    doc_hash_bytes = record[2] if record else b"\x00" * 32
    doc_hash_hex   = doc_hash_bytes.hex() if doc_hash_bytes != b"\x00" * 32 else None

    return {
        "address":      wallet_address,
        "is_valid":     is_valid,
        "owner":        record[0] if record else None,
        "did":          record[1] or None,
        "doc_hash":     doc_hash_hex,
        "ipfs_cid":     record[3] or None,
        "status_code":  status_code,
        "status":       STATUS_LABELS.get(status_code, "unknown"),
        "created_at":   record[5] if record else 0,
        "verified_at":  record[6] if record else 0,
        "updated_at":   record[7] if record else 0,
        "verified_by":  record[8] or None,
        "update_count": record[9] if record else 0,
    }


def revoke_did_on_chain(wallet_address: str) -> str:
    """
    Goi DID_Registry.revokeDID().
    Tra ve tx_hash.
    """
    w3 = get_web3()
    contract = _get_did_contract(w3)
    try:
        fn = contract.functions.revokeDID(
            Web3.to_checksum_address(wallet_address)
        )
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def get_did_stats() -> dict:
    """Lay thong ke: tong DID da tao va tong DID da xac minh."""
    w3 = get_web3()
    contract = _get_did_contract(w3)
    total, verified = contract.functions.getStats().call()
    return {"total_dids": total, "total_verified": verified}


def grant_creator_role(creator_address: str) -> str:
    """Cap quyen Identity Creator. Tra ve tx_hash."""
    w3 = get_web3()
    contract = _get_did_contract(w3)
    try:
        fn = contract.functions.grantCreatorRole(
            Web3.to_checksum_address(creator_address)
        )
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def is_creator_on_chain(address: str) -> bool:
    """Kiem tra dia chi co quyen Identity Creator khong."""
    w3 = get_web3()
    contract = _get_did_contract(w3)
    return contract.functions.isCreator(Web3.to_checksum_address(address)).call()


# ============================================================
# Soulbound Token functions
# ============================================================

def mint_soulbound_token(recipient: str, credential_type: str, metadata_uri: str) -> str:
    """
    Goi Soulbound_Contract.mint(recipient, credential_type, metadata_uri).
    Contract moi yeu cau 3 tham so: recipient, credential_type, metadata_uri.
    Tra ve tx_hash.
    """
    w3 = get_web3()
    contract = _get_soulbound_contract(w3)
    try:
        fn = contract.functions.mint(
            Web3.to_checksum_address(recipient),
            credential_type,
            metadata_uri,
        )
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def check_soulbound_token(address: str) -> dict:
    """
    Kiem tra trang thai Soulbound Token cua mot dia chi.
    Lay danh sach token_id cua owner, kiem tra hasValidToken.
    Tra ve dict: has_valid_token, tokens (list token_id), token_count.
    """
    w3 = get_web3()
    contract = _get_soulbound_contract(w3)
    addr = Web3.to_checksum_address(address)

    has_token = contract.functions.hasValidToken(addr).call()
    token_ids = contract.functions.getTokensOfOwner(addr).call()

    return {
        "has_valid_token": has_token,
        "tokens":          token_ids,
        "token_count":     len(token_ids),
    }


def get_soulbound_token_data(token_id: int) -> dict:
    """
    Lay thong tin chi tiet cua 1 token theo token_id.
    Tra ve dict: owner, issuer, token_id, credential_type, metadata_uri, is_valid, minted_at.
    """
    w3 = get_web3()
    contract = _get_soulbound_contract(w3)
    try:
        data = contract.functions.getTokenData(token_id).call()
        # TokenData tuple: (owner, issuer, token_id, credential_type, metadata_uri, is_valid, minted_at)
        return {
            "owner":           data[0],
            "issuer":          data[1],
            "token_id":        data[2],
            "credential_type": data[3],
            "metadata_uri":    data[4],
            "is_valid":        data[5],
            "minted_at":       data[6],
        }
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def invalidate_soulbound_token(token_id: int) -> str:
    """
    Vo hieu hoa Soulbound Token theo token_id.
    Contract moi dung token_id (uint256), khong phai owner address.
    Tra ve tx_hash.
    """
    w3 = get_web3()
    contract = _get_soulbound_contract(w3)
    try:
        fn = contract.functions.invalidateToken(token_id)
        return _send_tx(w3, fn)
    except ContractLogicError as e:
        raise ValueError(_parse_revert(e))


def invalidate_all_tokens_of_owner(owner_address: str) -> list[str]:
    """
    Vo hieu hoa tat ca Soulbound Token con hieu luc cua mot dia chi.
    Dung khi revoke DID de dam bao NFT cung bi invalidate.
    Tra ve danh sach tx_hash da xu ly.
    Loi tung token duoc log nhung khong lam fail toan bo ham.
    """
    w3 = get_web3()
    contract = _get_soulbound_contract(w3)
    addr = Web3.to_checksum_address(owner_address)

    token_ids = contract.functions.getTokensOfOwner(addr).call()
    tx_hashes = []

    for token_id in token_ids:
        try:
            is_valid = contract.functions.isTokenValid(token_id).call()
            if not is_valid:
                continue
            fn = contract.functions.invalidateToken(token_id)
            tx_hash = _send_tx(w3, fn)
            tx_hashes.append(tx_hash)
        except Exception as e:
            # Log loi nhung tiep tuc xu ly cac token con lai
            print(f"[WARN] Could not invalidate token {token_id} for {owner_address}: {e}")

    return tx_hashes


def verify_nft_access(address: str) -> dict:
    """
    Kiem tra quyen truy cap dua tren Soulbound Token (token-gated access).
    Tra ve dict: has_access, reason, has_valid_token, token_count.
    """
    w3 = get_web3()
    contract = _get_soulbound_contract(w3)
    addr = Web3.to_checksum_address(address)

    has_token = contract.functions.hasValidToken(addr).call()
    token_ids = contract.functions.getTokensOfOwner(addr).call()

    if has_token:
        return {
            "has_access":      True,
            "reason":          "Valid Soulbound Token found",
            "has_valid_token": True,
            "token_count":     len(token_ids),
        }
    elif len(token_ids) > 0:
        return {
            "has_access":      False,
            "reason":          "All tokens have been invalidated",
            "has_valid_token": False,
            "token_count":     len(token_ids),
        }
    else:
        return {
            "has_access":      False,
            "reason":          "No Soulbound Token found for this address",
            "has_valid_token": False,
            "token_count":     0,
        }
