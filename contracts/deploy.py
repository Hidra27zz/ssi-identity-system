"""
Script deploy DID_Registry.vy voi Ape Framework.
Nguoi phu trach: Nhan

Chay local:
    ape run deploy --network ethereum:local:http://127.0.0.1:8545

Chay Sepolia:
    ape accounts import deployer   # nhap private key lan dau
    ape run deploy --network ethereum:sepolia:infura
"""
import json
import os
from pathlib import Path

from ape import accounts, networks, project
from dotenv import load_dotenv

load_dotenv()

SHARED_ABIS_DIR = Path(__file__).parent.parent / "shared" / "abis"


def main():
    network_name = networks.provider.network.name

    # Local: dung test account co san (khong can import)
    # Sepolia: dung account da import qua `ape accounts import deployer`
    if "local" in network_name:
        deployer = accounts.test_accounts[0]
    else:
        deployer = accounts.load("deployer")

    print(f"Network  : {network_name}")
    print(f"Deployer : {deployer.address}")

    did_registry = deployer.deploy(project.DID_Registry)
    print(f"DID_Registry : {did_registry.address}")

    # Export ABI
    SHARED_ABIS_DIR.mkdir(parents=True, exist_ok=True)
    abi_path = SHARED_ABIS_DIR / "DID_Registry.json"
    with open(abi_path, "w") as f:
        json.dump([m.dict() for m in did_registry.contract_type.abi], f, indent=2)
    print(f"ABI saved : {abi_path}")
    print(f"Them vao .env: DID_REGISTRY_ADDRESS={did_registry.address}")
