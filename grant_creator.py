import sys
from web3 import Web3
import json
import os
from dotenv import load_dotenv

load_dotenv(".env")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
RPC_URL = "https://ethereum-sepolia-rpc.publicnode.com"
DID_REGISTRY_ADDRESS = "0x4442864E86805E1c5C8759ED1047Ef4802Ce15Ee"

w3 = Web3(Web3.HTTPProvider(RPC_URL))
with open("shared/abis/DID_Registry.json") as f:
    abi = json.load(f)

contract = w3.eth.contract(address=Web3.to_checksum_address(DID_REGISTRY_ADDRESS), abi=abi)
admin_account = w3.eth.account.from_key(PRIVATE_KEY)

print(f"Admin address: {admin_account.address}")

def grant_creator(address):
    address = Web3.to_checksum_address(address)
    is_creator = contract.functions.isCreator(address).call()
    if is_creator:
        print(f"{address} is already a creator.")
        return
        
    print(f"Granting Creator role to {address}...")
    tx = contract.functions.grantCreatorRole(address).build_transaction({
        'from': admin_account.address,
        'nonce': w3.eth.get_transaction_count(admin_account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"TX Hash: {tx_hash.hex()}")
    w3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Success! {address} is now a creator.")

grant_creator("0x97c62e9f554770a7e9F02421d2DB448e51Bb1852")
grant_creator("0x022B3dd640D5c7E1A24e1a37bdc9672bB4FA1A2b")

