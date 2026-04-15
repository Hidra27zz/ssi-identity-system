"""
Script deploy Soulbound_Contract.vy voi Ape Framework.
Nguoi phu trach: Nhu

Chay local:
    ape run deploy --network ethereum:local:http://127.0.0.1:8545

Chay Sepolia:
    ape accounts import deployer   # nhap private key lan dau
    ape run deploy --network ethereum:sepolia:infura

NOTE: Ape doc contract tu contracts/ (root ape-config.yaml).
      Chay lenh nay tu thu muc goc du an, khong phai tu nft-integration/
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

    if "local" in network_name:
        deployer = accounts.test_accounts[0]
    else:
        deployer = accounts.load("deployer")

    print(f"Network  : {network_name}")
    print(f"Deployer : {deployer.address}")

    soulbound = deployer.deploy(project.Soulbound_Contract)
    print(f"Soulbound_Contract : {soulbound.address}")

    SHARED_ABIS_DIR.mkdir(parents=True, exist_ok=True)
    abi_path = SHARED_ABIS_DIR / "Soulbound_Contract.json"
    with open(abi_path, "w") as f:
        json.dump([m.dict() for m in soulbound.contract_type.abi], f, indent=2)
    print(f"ABI saved : {abi_path}")
    print(f"Them vao .env: SOULBOUND_ADDRESS={soulbound.address}")
