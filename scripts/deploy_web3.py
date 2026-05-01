"""
Deploy DID_Registry bang Web3.py.
Chay: python scripts/deploy_web3.py
"""
import json
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

SHARED_ABIS_DIR = Path(__file__).parent.parent / "shared" / "abis"
CONSTANTS_PY    = Path(__file__).parent.parent / "shared" / "constants.py"
CONSTANTS_JS    = Path(__file__).parent.parent / "shared" / "constants.js"

RPC_URL     = "http://127.0.0.1:8545"
ACCOUNT     = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

def main():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    print(f"Network  : local")
    print(f"Deployer : {ACCOUNT}")
    print(f"Ket noi  : {w3.is_connected()}")

    with open(SHARED_ABIS_DIR / "DID_Registry.json", encoding="utf-8-sig") as f:
        abi = json.load(f)
    with open(SHARED_ABIS_DIR / "DID_Registry.bin", encoding="utf-8-sig") as f:
        bytecode = f.read().strip().splitlines()[0].strip()

    print("Deploying DID_Registry...")
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = Contract.constructor().build_transaction({
        "from": ACCOUNT,
        "nonce": w3.eth.get_transaction_count(ACCOUNT),
        "gas": 3000000,
        "gasPrice": w3.to_wei("1", "gwei"),
    })
    signed  = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    address = receipt.contractAddress

    print(f"DID_Registry deployed : {address}")

    with open(SHARED_ABIS_DIR / "deployed_address.txt", "w") as f:
        f.write(address)

    _update_constants(address)
    print(f"\nDone! Them vao .env: DID_REGISTRY_ADDRESS={address}")

def _update_constants(address):
    for path, old, new in [
        (CONSTANTS_PY,
         'DID_REGISTRY_ADDRESS = "0x0000000000000000000000000000000000000000"',
         f'DID_REGISTRY_ADDRESS = "{address}"'),
        (CONSTANTS_JS,
         'export const DID_REGISTRY_ADDRESS = "0x0000000000000000000000000000000000000000"',
         f'export const DID_REGISTRY_ADDRESS = "{address}"'),
    ]:
        if path.exists():
            text = path.read_text()
            if old in text:
                path.write_text(text.replace(old, new))
                print(f"Updated {path.name}")

if __name__ == "__main__":
    main()