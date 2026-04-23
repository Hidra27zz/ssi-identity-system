"""
Script deploy DID_Registry.vy voi Ape Framework.
Nguoi phu trach: Nhan

Chay local (anvil dang chay):
    # Lan dau: import private key Anvil vao Ape
    ape accounts import anvil_deployer
    # Nhap private key: 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
    # Nhap passphrase: test (hoac bat ky)

    # Deploy:
    ape run deploy --network ethereum:local

Chay Sepolia:
    ape accounts import deployer
    ape run deploy --network ethereum:sepolia:infura
"""
import json
import os
from pathlib import Path

from ape import accounts, networks, project
from dotenv import load_dotenv

load_dotenv()

SHARED_ABIS_DIR = Path(__file__).parent.parent / "shared" / "abis"
CONSTANTS_PY    = Path(__file__).parent.parent / "shared" / "constants.py"
CONSTANTS_JS    = Path(__file__).parent.parent / "shared" / "constants.js"

# Ten account da import qua `ape accounts import`
LOCAL_ACCOUNT_NAME  = "anvil_deployer"
TESTNET_ACCOUNT_NAME = "deployer"


def main():
    network_name = networks.provider.network.name
    is_local = "local" in network_name

    print(f"Network  : {network_name}")

    account_name = LOCAL_ACCOUNT_NAME if is_local else TESTNET_ACCOUNT_NAME
    deployer = accounts.load(account_name)

    print(f"Deployer : {deployer.address}")
    print("Deploying DID_Registry...")

    did_registry = deployer.deploy(project.DID_Registry)
    address = did_registry.address
    print(f"DID_Registry deployed : {address}")

    # Export ABI
    SHARED_ABIS_DIR.mkdir(parents=True, exist_ok=True)
    abi_path = SHARED_ABIS_DIR / "DID_Registry.json"
    with open(abi_path, "w") as f:
        json.dump([m.dict() for m in did_registry.contract_type.abi], f, indent=2)
    print(f"ABI saved : {abi_path}")

    _update_constants(address)
    print(f"\nDone! Them vao .env: DID_REGISTRY_ADDRESS={address}")


def _update_constants(address: str):
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
