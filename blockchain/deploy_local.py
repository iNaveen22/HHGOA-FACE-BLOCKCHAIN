"""
Local Blockchain Contract Deployment Script.

HH Goa 2026 Shortlisting Task 3 - Milestone 4.

Compiles VerificationRegistry.sol and deploys it to a local Ethereum blockchain (Ganache/Anvil RPC).
Saves contract address and ABI to contract_data.json for client use.
"""

import os
import sys
import json
from dotenv import load_dotenv
from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOLC_VERSION = "0.8.20"
CONTRACT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "VerificationRegistry.sol"))
OUTPUT_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "contract_data.json"))


def compile_contract():
    """
    Installs solc compiler if missing and compiles VerificationRegistry.sol.

    Returns:
        tuple: (abi, bytecode)
    """
    print(f"[*] Ensuring Solidity compiler version {SOLC_VERSION} is installed...")
    try:
        install_solc(SOLC_VERSION)
        set_solc_version(SOLC_VERSION)
    except Exception as e:
        print(f"[!] Compiler setup warning: {e}")

    with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
        source_code = f.read()

    print(f"[*] Compiling {CONTRACT_PATH}...")
    compiled_sol = compile_standard(
        {
            "language": "Solidity",
            "sources": {"VerificationRegistry.sol": {"content": source_code}},
            "settings": {
                "outputSelection": {
                    "*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}
                }
            },
        },
        solc_version=SOLC_VERSION,
    )

    contract_data = compiled_sol["contracts"]["VerificationRegistry.sol"]["VerificationRegistry"]
    abi = contract_data["abi"]
    bytecode = contract_data["evm"]["bytecode"]["object"]

    print(f"[+] Compilation successful.")
    return abi, bytecode


def deploy_contract():
    """
    Connects to local RPC, deploys VerificationRegistry contract, and saves contract data.
    """
    load_dotenv()
    rpc_url = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY", None)

    print(f"[*] Connecting to local blockchain at: {rpc_url}")
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        raise ConnectionError(
            f"Could not connect to local blockchain at {rpc_url}. "
            "Please ensure Ganache / Anvil is running on http://127.0.0.1:8545 and try again."
        )

    print(f"[+] Connected to local blockchain! Chain ID: {w3.eth.chain_id}")

    # Select deployment account
    accounts = w3.eth.accounts
    if private_key:
        deployer_account = w3.eth.account.from_key(private_key)
        deployer_address = deployer_account.address
    elif accounts and len(accounts) > 0:
        deployer_address = accounts[0]
        deployer_account = None
    else:
        raise ValueError("No accounts available on local blockchain node.")

    print(f"[*] Deployer address: {deployer_address}")

    abi, bytecode = compile_contract()
    ContractFactory = w3.eth.contract(abi=abi, bytecode=bytecode)

    print("[*] Submitting contract deployment transaction...")

    if deployer_account:
        # Build, sign, and send deployment transaction
        tx = ContractFactory.constructor().build_transaction({
            "from": deployer_address,
            "nonce": w3.eth.get_transaction_count(deployer_address),
            "gas": 3000000,
            "gasPrice": w3.eth.gas_price
        })
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    else:
        # Send deployment transaction via unlocked node account
        tx_hash = ContractFactory.constructor().transact({"from": deployer_address})

    print(f"[*] Waiting for transaction receipt (tx: {tx_hash.hex()})...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    contract_address = tx_receipt.contractAddress
    print(f"\n==================================================")
    print(f"       CONTRACT DEPLOYMENT SUCCESSFUL             ")
    print(f"==================================================")
    print(f"Contract Address : {contract_address}")
    print(f"Transaction Hash : {tx_receipt.transactionHash.hex()}")
    print(f"Block Number     : {tx_receipt.blockNumber}")
    print(f"Gas Used         : {tx_receipt.gasUsed}")
    print(f"==================================================")

    # Save metadata to contract_data.json
    contract_meta = {
        "contract_address": contract_address,
        "tx_hash": tx_receipt.transactionHash.hex(),
        "block_number": tx_receipt.blockNumber,
        "rpc_url": rpc_url,
        "abi": abi
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(contract_meta, f, indent=2)

    print(f"[+] Saved contract ABI and metadata to: {OUTPUT_JSON_PATH}")

    return contract_meta


if __name__ == "__main__":
    try:
        deploy_contract()
    except Exception as err:
        print(f"\n[-] DEPLOYMENT ERROR: {err}", file=sys.stderr)
        sys.exit(1)
