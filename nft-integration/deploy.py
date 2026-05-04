"""
Script deploy Soulbound_Contract.vy với Ape Framework.
Người phụ trách: Như

Chạy local (cần anvil đang chạy):
    ape run nft-integration/deploy --network ethereum:local:http://127.0.0.1:8545

Chạy Sepolia:
    ape accounts import deployer
    ape run nft-integration/deploy --network ethereum:sepolia:infura
"""
import json
from pathlib import Path

from ape import accounts, networks, project
from dotenv import load_dotenv

load_dotenv()

SHARED_ABIS_DIR = Path(__file__).parent.parent / "shared" / "abis"
CONSTANTS_PY    = Path(__file__).parent.parent / "shared" / "constants.py"
CONSTANTS_JS    = Path(__file__).parent.parent / "shared" / "constants.js"


def _update_constants(address: str):
    """Cập nhật địa chỉ Soulbound Contract vào shared/constants.py và constants.js."""
    for path, old, new in [
        (
            CONSTANTS_PY,
            'SOULBOUND_ADDRESS = "0x0000000000000000000000000000000000000000"',
            f'SOULBOUND_ADDRESS = "{address}"',
        ),
        (
            CONSTANTS_JS,
            'export const SOULBOUND_ADDRESS = "0x0000000000000000000000000000000000000000"',
            f'export const SOULBOUND_ADDRESS = "{address}"',
        ),
    ]:
        if path.exists():
            text = path.read_text()
            if old in text:
                path.write_text(text.replace(old, new))
                print(f"Updated {path.name} -> SOULBOUND_ADDRESS={address}")
            else:
                print(f"Note: {path.name} already has a non-zero SOULBOUND_ADDRESS, skipping auto-update.")


def main():
    network_name = networks.provider.network.name
    is_local = "local" in network_name

    deployer = accounts.test_accounts[0] if is_local else accounts.load("deployer")

    print(f"Network  : {network_name}")
    print(f"Deployer : {deployer.address}")
    print("Deploying Soulbound_Contract...")

    soulbound = deployer.deploy(project.Soulbound_Contract)
    address = soulbound.address
    print(f"Soulbound_Contract deployed : {address}")

    # Export ABI vào shared/abis/
    SHARED_ABIS_DIR.mkdir(parents=True, exist_ok=True)
    abi_path = SHARED_ABIS_DIR / "Soulbound_Contract.json"
    with open(abi_path, "w") as f:
        json.dump([m.dict() for m in soulbound.contract_type.abi], f, indent=2)
    print(f"ABI saved : {abi_path}")

    # Tự động cập nhật constants
    _update_constants(address)

    # Verify trên Etherscan (chỉ khi deploy testnet/mainnet)
    if not is_local:
        try:
            soulbound.contract_type
            print(f"Contract verified on Etherscan: https://sepolia.etherscan.io/address/{address}")
        except Exception as e:
            print(f"Etherscan verify failed (có thể verify thủ công): {e}")

    print("\nDone. Thêm vào .env:")
    print(f"  SOULBOUND_ADDRESS={address}")
