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
from pathlib import Path

from ape import accounts, networks, project, chain
from dotenv import load_dotenv

load_dotenv()

SHARED_ABIS_DIR = Path(__file__).parent.parent / "shared" / "abis"


def main():
    network_name = networks.provider.network.name

    print(f"Network  : {network_name}")
    print(f"Provider : {networks.provider.uri}")
    print(f"Block    : {chain.blocks.head.number}")

    # Check contract tồn tại
    assert hasattr(project, "Soulbound_Contract"), "Contract not found. Run 'ape compile' first."

    # Chọn account
    if "local" in network_name:
        deployer = accounts.test_accounts[0]
    else:
        deployer = accounts.load("deployer")

    print(f"Deployer : {deployer.address}")

    # Deploy
    soulbound = deployer.deploy(project.Soulbound_Contract)
    print(f"Soulbound deployed at: {soulbound.address}")

    # Save ABI
    SHARED_ABIS_DIR.mkdir(parents=True, exist_ok=True)
    abi_path = SHARED_ABIS_DIR / "Soulbound_Contract.json"

    abi = [m.dict() for m in soulbound.contract_type.abi]

    with open(abi_path, "w") as f:
        json.dump(abi, f, indent=2)

    print(f"ABI saved at: {abi_path}")

    # Auto update .env (optional)
    env_path = Path(".env")
    if env_path.exists():
        content = env_path.read_text()

        if "SOULBOUND_ADDRESS=" in content:
            content = content.replace(
                "SOULBOUND_ADDRESS=0x0000000000000000000000000000000000000000",
                f"SOULBOUND_ADDRESS={soulbound.address}"
            )
            env_path.write_text(content)
            print("Updated .env with SOULBOUND_ADDRESS")

    print("\n=== DONE ===")
if __name__ == "__main__":
    main()