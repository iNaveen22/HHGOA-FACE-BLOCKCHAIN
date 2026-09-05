"""
Ethereum Sepolia Smart Contract Deployment Script.

HH Goa 2026 Shortlisting Task 3 - Sepolia Migration.

Compiles VerificationRegistry.sol and deploys it to Ethereum Sepolia Testnet (Chain ID: 11155111).
Saves deployed contract address, ABI, and transaction metadata to contract_sepolia_data.json.
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
SEPOLIA_CHAIN_ID = 11155111
CONTRACT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "VerificationRegistry.sol"))
OUTPUT_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "contract_sepolia_data.json"))
ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))


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
        print(f"[!] Compiler setup notice: {e}")

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


def deploy_to_sepolia():
    """
    Connects to Sepolia RPC, validates chain ID & ETH balance, deploys VerificationRegistry contract,
    and records contract metadata.
    """
    load_dotenv()
    rpc_url = os.getenv("SEPOLIA_RPC_URL")
    private_key = os.getenv("SEPOLIA_PRIVATE_KEY")
    env_chain_id = int(os.getenv("SEPOLIA_CHAIN_ID", 11155111))

    if not rpc_url or not rpc_url.strip():
        raise ValueError("SEPOLIA_RPC_URL is missing in .env file.")
    if not private_key or not private_key.strip():
        raise ValueError("SEPOLIA_PRIVATE_KEY is missing in .env file.")

    rpc_url = rpc_url.strip()
    private_key = private_key.strip()

    # Sanitize private key prefix
    if not private_key.startswith("0x"):
        private_key = "0x" + private_key

    print(f"[*] Connecting to Sepolia RPC endpoint...")
    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        raise ConnectionError(
            "Could not connect to Sepolia RPC. Please verify your SEPOLIA_RPC_URL in .env."
        )

    chain_id = w3.eth.chain_id
    print(f"[+] Connected to network RPC! Detected Chain ID: {chain_id}")

    if chain_id != SEPOLIA_CHAIN_ID:
        raise ValueError(
            f"Connected RPC Chain ID ({chain_id}) does not match Sepolia Chain ID ({SEPOLIA_CHAIN_ID})."
        )

    # Derive deployer account from private key (NEVER PRINT PRIVATE KEY)
    deployer_account = w3.eth.account.from_key(private_key)
    deployer_address = deployer_account.address

    balance_wei = w3.eth.get_balance(deployer_address)
    balance_eth = w3.from_wei(balance_wei, "ether")

    print(f"[*] Deployer Wallet Address : {deployer_address}")
    print(f"[*] Wallet Sepolia ETH Balance: {balance_eth:.6f} ETH")

    if balance_wei == 0:
        raise ValueError(
            f"Deployer account {deployer_address} has 0 Sepolia ETH. "
            "Please request testnet ETH from a Sepolia faucet before deploying."
        )

    abi, bytecode = compile_contract()
    ContractFactory = w3.eth.contract(abi=abi, bytecode=bytecode)

    print("[*] Building Sepolia deployment transaction...")
    nonce = w3.eth.get_transaction_count(deployer_address)

    # Handle gas pricing
    tx_params = {
        "from": deployer_address,
        "nonce": nonce,
        "chainId": SEPOLIA_CHAIN_ID,
        "gas": 2000000,
        "gasPrice": w3.eth.gas_price
    }

    tx = ContractFactory.constructor().build_transaction(tx_params)
    print("[*] Signing transaction with deployer key...")
    signed_tx = w3.eth.account.sign_transaction(tx, private_key)

    print("[*] Broadcasting raw transaction to Ethereum Sepolia...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hex = tx_hash.hex()
    print(f"[*] Submitted deployment transaction! Tx Hash: {tx_hex}")
    print(f"[*] Waiting for Sepolia block confirmation (this may take 12-30 seconds)...")

    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    contract_address = tx_receipt.contractAddress
    etherscan_address_url = f"https://sepolia.etherscan.io/address/{contract_address}"
    etherscan_tx_url = f"https://sepolia.etherscan.io/tx/{tx_hex}"

    print(f"\n==================================================")
    print(f"    SEPOLIA CONTRACT DEPLOYMENT SUCCESSFUL        ")
    print(f"==================================================")
    print(f"Network             : Ethereum Sepolia (Chain ID {SEPOLIA_CHAIN_ID})")
    print(f"Contract Address    : {contract_address}")
    print(f"Transaction Hash    : {tx_hex}")
    print(f"Block Number        : {tx_receipt.blockNumber}")
    print(f"Gas Used            : {tx_receipt.gasUsed}")
    print(f"Etherscan Contract  : {etherscan_address_url}")
    print(f"Etherscan Tx Link   : {etherscan_tx_url}")
    print(f"==================================================")

    # Save to contract_sepolia_data.json
    contract_meta = {
        "network": "Ethereum Sepolia",
        "chain_id": SEPOLIA_CHAIN_ID,
        "contract_address": contract_address,
        "tx_hash": tx_hex,
        "block_number": tx_receipt.blockNumber,
        "rpc_url": rpc_url,
        "etherscan_contract_url": etherscan_address_url,
        "etherscan_tx_url": etherscan_tx_url,
        "abi": abi
    }

    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(contract_meta, f, indent=2)
    print(f"[+] Saved Sepolia contract ABI and metadata to: {OUTPUT_JSON_PATH}")

    # Append SEPOLIA_CONTRACT_ADDRESS to .env if not already present
    update_env_contract_address(contract_address)

    return contract_meta


def update_env_contract_address(contract_address: str):
    """
    Updates or appends SEPOLIA_CONTRACT_ADDRESS in .env.
    """
    if not os.path.exists(ENV_PATH):
        return

    with open(ENV_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.startswith("SEPOLIA_CONTRACT_ADDRESS="):
            new_lines.append(f"SEPOLIA_CONTRACT_ADDRESS={contract_address}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"SEPOLIA_CONTRACT_ADDRESS={contract_address}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"[+] Updated SEPOLIA_CONTRACT_ADDRESS in .env")


if __name__ == "__main__":
    try:
        deploy_to_sepolia()
    except Exception as err:
        print(f"\n[-] SEPOLIA DEPLOYMENT ERROR: {err}", file=sys.stderr)
        sys.exit(1)
