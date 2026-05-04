import json
from web3 import Web3
from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
account = w3.eth.account.from_key(os.getenv("USER_PRIVATE_KEY"))

# Load ABI
base_path = Path(__file__).resolve().parent.parent
with open(base_path / "shared" / "abis" / "DID_Registry.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=os.getenv("DID_REGISTRY_ADDRESS"), abi=abi)

def register():
    print(f"--- Đang đăng ký DID cho ví: {account.address} ---")
    nonce = w3.eth.get_transaction_count(account.address)
    
    # Thêm một chuỗi bất kỳ vào trong ngoặc, ví dụ "User_Profile_Metadata"
    # Bạn có thể để tên của mình hoặc thông tin mô tả ngắn
    tx = contract.functions.createDID("Nhu_Student_Profile").build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 200000,
        'gasPrice': w3.eth.gas_price
    })

    signed_tx = w3.eth.account.sign_transaction(tx, os.getenv("USER_PRIVATE_KEY"))
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"✅ Đã đăng ký DID! Hash: {tx_hash.hex()}")

if __name__ == "__main__":
    register()