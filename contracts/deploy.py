"""
Script deploy DID_Registry.vy voi Ape Framework.
Nguoi phu trach: Nhan

Chay local (can anvil dang chay):
    ape run deploy --network ethereum:local:http://127.0.0.1:8545

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


def update_constants(address: str):
    """Cap nhat dia chi contract vao shared/constants.py va constants.js."""
    # constants.py
    if CONSTANTS_PY.exists():
        text = CONSTANTS_PY.read_text()
        text = text.replace(
            'DID_REGISTRY_ADDRESS = "0x0000000000000000000000000000000000000000"',
            f'DID_REGISTRY_ADDRESS = "{address}"'
        )
        CONSTANTS_PY.write_text(text)
        print(f"Updated shared/constants.py -> DID_REGISTRY_ADDRESS={address}")

    # constants.js
    if CONSTANTS_JS.exists():
        text = CONSTANTS_JS.read_text()
        text = text.replace(
            'export const DID_REGISTRY_ADDRESS = "0x0000000000000000000000000000000000000000"',
            f'export const DID_REGISTRY_ADDRESS = "{address}"'
        )
        CONSTANTS_JS.write_text(text)
        print(f"Updated shared/constants.js -> DID_REGISTRY_ADDRESS={address}")


def main():
    network_name = networks.provider.network.name
    is_local = "local" in network_name

    deployer = accounts.test_accounts[0] if is_local else accounts.load("deployer")

    print(f"Network  : {network_name}")
    print(f"Deployer : {deployer.address}")
    print("Deploying DID_Registry...")

    did_registry = deployer.deploy(project.DID_Registry)
    address = did_registry.address
    print(f"DID_Registry deployed : {address}")

    # Export ABI vao shared/abis/
    SHARED_ABIS_DIR.mkdir(parents=True, exist_ok=True)
    abi_path = SHARED_ABIS_DIR / "DID_Registry.json"
    with open(abi_path, "w") as f:
        json.dump([m.dict() for m in did_registry.contract_type.abi], f, indent=2)
    print(f"ABI saved : {abi_path}")

    # Tu dong cap nhat constants
    update_constants(address)

    # Verify tren Etherscan (chi khi deploy testnet/mainnet)
    if not is_local:
        try:
            did_registry.contract_type  # ape-etherscan tu dong verify neu plugin duoc cai
            print(f"Contract verified on Etherscan: https://sepolia.etherscan.io/address/{address}")
        except Exception as e:
            print(f"Etherscan verify failed (co the verify thu cong): {e}")

    print("\nDone. Them vao .env:")
    print(f"  DID_REGISTRY_ADDRESS={address}")
