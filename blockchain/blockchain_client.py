"""
Blockchain Client Module using Web3.py.

HH Goa 2026 Shortlisting Task 3 - Sepolia Migration.

Interacts with the deployed VerificationRegistry smart contract on Ethereum Sepolia Testnet
(with automatic fallback to local Ganache RPC).
Provides clean Python functions for storing verification fingerprints, reading records,
performing on-chain verification checks, and generating Sepolia Etherscan URLs.
"""

import os
import sys
import json
from typing import Dict, Any
from dotenv import load_dotenv
from web3 import Web3

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SEPOLIA_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "contract_sepolia_data.json"))
LOCAL_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "contract_data.json"))


class BlockchainClient:
    """
    Python client for interacting with VerificationRegistry smart contract on Sepolia or local chain.
    """

    def __init__(self, rpc_url: str = None, contract_address: str = None, private_key: str = None):
        load_dotenv()

        # Priority 1: Sepolia environment variables
        sepolia_rpc = os.getenv("SEPOLIA_RPC_URL")
        sepolia_key = os.getenv("SEPOLIA_PRIVATE_KEY")
        sepolia_addr = os.getenv("SEPOLIA_CONTRACT_ADDRESS")

        # Priority 2: Local Ganache environment variables
        local_rpc = os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        local_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")

        # Select RPC URL and Private Key
        self.rpc_url = rpc_url or sepolia_rpc or local_rpc
        self.private_key = private_key or sepolia_key or local_key

        if self.private_key and not self.private_key.startswith("0x"):
            self.private_key = "0x" + self.private_key

        print(f"[*] Connecting to Blockchain RPC: {self.rpc_url[:45]}...")
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))

        if not self.w3.is_connected():
            raise ConnectionError(
                f"Could not connect to blockchain at '{self.rpc_url}'. "
                "Please verify your SEPOLIA_RPC_URL in .env or start local Ganache."
            )

        self.chain_id = self.w3.eth.chain_id
        if self.chain_id == 11155111:
            self.network_name = "Ethereum Sepolia"
        elif self.chain_id == 1337 or self.chain_id == 5777:
            self.network_name = "Local Ganache"
        else:
            self.network_name = f"Ethereum Network (Chain ID {self.chain_id})"

        # Load contract address and ABI
        self.contract_address = contract_address or sepolia_addr
        self.abi = None

        # Check metadata JSON files for ABI and contract address fallback
        if os.path.exists(SEPOLIA_DATA_PATH):
            with open(SEPOLIA_DATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                self.abi = meta.get("abi")
                if not self.contract_address:
                    self.contract_address = meta.get("contract_address")

        if (not self.contract_address or not self.abi) and os.path.exists(LOCAL_DATA_PATH):
            with open(LOCAL_DATA_PATH, "r", encoding="utf-8") as f:
                meta = json.load(f)
                if not self.abi:
                    self.abi = meta.get("abi")
                if not self.contract_address:
                    self.contract_address = meta.get("contract_address")

        if not self.contract_address or not self.abi:
            raise ValueError(
                "Could not resolve contract address or ABI. "
                "Please run 'python blockchain/deploy_sepolia.py' first."
            )

        self.contract_address = Web3.to_checksum_address(self.contract_address)
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )

        # Configure account
        accounts = self.w3.eth.accounts
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
            self.account_address = self.account.address
        elif accounts and len(accounts) > 0:
            self.account_address = accounts[0]
            self.account = None
        else:
            raise ValueError("No private key or unlocked accounts available for transaction signing.")

    def get_etherscan_tx_url(self, tx_hash: str) -> str:
        """Returns Sepolia Etherscan transaction URL if on Sepolia network."""
        if self.chain_id == 11155111:
            clean_hash = tx_hash if tx_hash.startswith("0x") else "0x" + tx_hash
            return f"https://sepolia.etherscan.io/tx/{clean_hash}"
        return "N/A (Local Blockchain)"

    def get_etherscan_contract_url(self) -> str:
        """Returns Sepolia Etherscan contract URL if on Sepolia network."""
        if self.chain_id == 11155111:
            return f"https://sepolia.etherscan.io/address/{self.contract_address}"
        return "N/A (Local Blockchain)"

    def store_record(self, bytes32_hex: str, source_url: str) -> Dict[str, Any]:
        """
        Stores a fingerprint on-chain by calling VerificationRegistry.storeRecord().

        Args:
            bytes32_hex (str): 0x-prefixed 64-char hex string (32 bytes).
            source_url (str): Verified candidate page/source URL.

        Returns:
            dict: Transaction receipt details including Etherscan URLs.
        """
        bytes32_val = Web3.to_bytes(hexstr=bytes32_hex)

        if self.account:
            # Get pending nonce to handle back-to-back transactions
            nonce = self.w3.eth.get_transaction_count(self.account_address, "pending")

            # Build EIP-1559 or legacy transaction for reliable miner inclusion
            try:
                latest_block = self.w3.eth.get_block("latest")
                base_fee = latest_block.get("baseFeePerGas", self.w3.eth.gas_price)
                try:
                    priority_fee = self.w3.eth.max_priority_fee
                except Exception:
                    priority_fee = self.w3.to_wei(2, "gwei")

                max_fee = int(base_fee * 2.5) + priority_fee

                tx_params = {
                    "from": self.account_address,
                    "nonce": nonce,
                    "gas": 300000,
                    "maxFeePerGas": max_fee,
                    "maxPriorityFeePerGas": priority_fee,
                    "chainId": self.chain_id
                }
            except Exception:
                tx_params = {
                    "from": self.account_address,
                    "nonce": nonce,
                    "gas": 300000,
                    "gasPrice": int(self.w3.eth.gas_price * 1.5),
                    "chainId": self.chain_id
                }

            tx = self.contract.functions.storeRecord(bytes32_val, source_url).build_transaction(tx_params)
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        else:
            # Send transaction via unlocked local node account
            tx_hash = self.contract.functions.storeRecord(bytes32_val, source_url).transact({
                "from": self.account_address
            })

        tx_hex = tx_hash.hex()
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

        return {
            "transaction_hash": tx_hex,
            "block_number": tx_receipt.blockNumber,
            "gas_used": tx_receipt.gasUsed,
            "status": tx_receipt.status,
            "contract_address": self.contract_address,
            "bytes32_hex": bytes32_hex,
            "network_name": self.network_name,
            "chain_id": self.chain_id,
            "etherscan_tx_url": self.get_etherscan_tx_url(tx_hex),
            "etherscan_contract_url": self.get_etherscan_contract_url()
        }

    def verify_record(self, bytes32_hex: str) -> bool:
        """
        Checks whether a given fingerprint exists on-chain.

        Args:
            bytes32_hex (str): 0x-prefixed hex string of the SHA-256 fingerprint.

        Returns:
            bool: True if fingerprint exists on-chain, False otherwise.
        """
        bytes32_val = Web3.to_bytes(hexstr=bytes32_hex)
        exists = self.contract.functions.verifyRecord(bytes32_val).call()
        return exists

    def get_record(self, bytes32_hex: str) -> Dict[str, Any]:
        """
        Retrieves the recorded fingerprint details from the blockchain state.

        Args:
            bytes32_hex (str): 0x-prefixed hex string of the SHA-256 fingerprint.

        Returns:
            dict: Record details (data_hash, source_url, block_timestamp).
        """
        bytes32_val = Web3.to_bytes(hexstr=bytes32_hex)
        res = self.contract.functions.getRecord(bytes32_val).call()

        return {
            "data_hash": Web3.to_hex(res[0]),
            "source_url": res[1],
            "timestamp": res[2]
        }


if __name__ == "__main__":
    try:
        client = BlockchainClient()
        print(f"[+] Connected to {client.network_name}! Contract Address: {client.contract_address}")
        print(f"    - Etherscan Contract: {client.get_etherscan_contract_url()}")
    except Exception as err:
        print(f"[-] Blockchain Client Error: {err}")
