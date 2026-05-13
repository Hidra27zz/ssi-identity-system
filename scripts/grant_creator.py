"""
Script cap quyen Identity Creator cho mot dia chi vi.
Chi contract_owner moi chay duoc script nay.

Su dung:
    python scripts/grant_creator.py <dia_chi_muon_cap_quyen>

Vi du:
    python scripts/grant_creator.py 0xab63fe861ed1ff0bab5c3044a4957a08d8345b60
"""
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))
from shared.constants import DID_REGISTRY_ADDRESS

SHARED_ABIS = Path(__file__).parent.parent / "shared" / "abis"
RPC_URL     = os.getenv("RPC_URL", "http://127.0.0.1:8545")
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")


def main():
    if len(sys.argv) < 2:
        print("Cach dung: python scripts/grant_creator.py <address>")
        sys.exit(1)

    target = sys.argv[1].strip()

    # Ket noi RPC
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print(f"[ERROR] Khong ket noi duoc RPC: {RPC_URL}")
        sys.exit(1)

    # Load ABI
    abi_path = SHARED_ABIS / "DID_Registry.json"
    if not abi_path.exists():
        print(f"[ERROR] ABI chua co: {abi_path}")
        print("Chay 'ape compile' truoc.")
        sys.exit(1)

    import json
    with open(abi_path) as f:
        abi = json.load(f)

    contract = w3.eth.contract(
        address=Web3.to_checksum_address(DID_REGISTRY_ADDRESS),
        abi=abi
    )

    # Kiem tra PRIVATE_KEY
    key = PRIVATE_KEY.strip()
    if not key:
        print("[ERROR] Thieu PRIVATE_KEY trong .env")
        sys.exit(1)
    if not key.startswith("0x"):
        key = "0x" + key

    account = w3.eth.account.from_key(key)
    print(f"Dang dung vi: {account.address}")

    # Kiem tra owner
    owner = contract.functions.getOwner().call()
    print(f"Contract owner: {owner}")

    if account.address.lower() != owner.lower():
        print(f"\n[ERROR] Vi {account.address} KHONG phai contract owner.")
        print(f"Chi {owner} moi cap quyen Creator duoc.")
        print("Lien he nguoi deploy de duoc cap quyen.")
        sys.exit(1)

    # Kiem tra target da co quyen chua
    target_cs = Web3.to_checksum_address(target)
    already = contract.functions.isCreator(target_cs).call()
    if already:
        print(f"\n[OK] {target} da co quyen Identity Creator roi.")
        sys.exit(0)

    # Grant Creator
    print(f"\nDang cap quyen Creator cho: {target_cs}")
    nonce = w3.eth.get_transaction_count(account.address, "pending")
    tx = contract.functions.grantCreatorRole(target_cs).build_transaction({
        "from":     account.address,
        "nonce":    nonce,
        "gas":      100000,
        "gasPrice": w3.eth.gas_price,
    })
    signed   = account.sign_transaction(tx)
    tx_hash  = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt  = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

    if receipt.status == 1:
        print(f"[THANH CONG] Da cap quyen Creator cho {target_cs}")
        print(f"Tx hash: {tx_hash.hex()}")
        print(f"Xem tren Etherscan: https://sepolia.etherscan.io/tx/{tx_hash.hex()}")
    else:
        print(f"[THAT BAI] Transaction reverted. Tx: {tx_hash.hex()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
