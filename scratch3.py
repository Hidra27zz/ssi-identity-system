from backend.services.blockchain_service import get_web3, _signing_account, _get_did_contract
from web3 import Web3
from web3.exceptions import ContractLogicError

w3 = get_web3()
contract = _get_did_contract(w3)
account = _signing_account(w3)

wallet = Web3.to_checksum_address('0x01b3d559557693d1bb874056cde8573ee1d57638')
doc_hash_bytes = bytes.fromhex("1234567890123456789012345678901234567890123456789012345678901234")
cid = "QmXxx"

fn = contract.functions.storeDocumentHash(wallet, doc_hash_bytes, cid)
try:
    tx = fn.build_transaction({
        "from": account.address,
        "nonce": w3.eth.get_transaction_count(account.address, "pending"),
        "gasPrice": w3.eth.gas_price,
    })
    print("build_transaction SUCCESS")
except ContractLogicError as e:
    print(f"ContractLogicError CAUGHT: {e}")
except Exception as e:
    print(f"Other Error CAUGHT: {type(e)} - {e}")
