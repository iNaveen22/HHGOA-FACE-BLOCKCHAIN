"""
Blockchain Client Module using Web3.py.

HH Goa 2026 Shortlisting Task 3 - Milestone 4.

Interacts with the deployed VerificationRegistry smart contract on local Ethereum blockchain.
Provides clean Python functions for storing verification fingerprints, reading records,
and performing on-chain verification checks.
"""

import os
import sys
import json
from typing import Dict, Any, Tuple
from dotenv import load_dotenv
from web3 import Web3

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CONTRACT_DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "contract_data.json"))


class BlockchainClient:
    """
    Python client for interacting with VerificationRegistry smart contract.
    """

    def __init__(self, rpc_url: str = None, contract_address: str = None):
        load_dotenv()
        self.rpc_url = rpc_url or os.getenv("BLOCKCHAIN_RPC_URL", "http://127.0.0.1:8545")
        self.private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY", None)

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(
                f"Could not connect to local blockchain at {self.rpc_url}. "
                "Please start Anvil/Ganache on http://127.0.0.1:8545 and try again."
            )

        # Load contract address and ABI
        if not os.path.exists(CONTRACT_DATA_PATH):
            raise FileNotFoundError(
                f"Contract data file not found at '{CONTRACT_DATA_PATH}'. "
                "Please run 'python blockchain/deploy_local.py' first."
            )

        with open(CONTRACT_DATA_PATH, "r", encoding="utf-8") as f:
            meta = json.load(f)

        self.contract_address = contract_address or meta.get("contract_address")
        self.abi = meta.get("abi")

        if not self.contract_address or not self.abi:
            raise ValueError("Invalid contract data file: missing contract address or ABI.")

        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.contract_address),
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
            raise ValueError("No accounts available on local blockchain node.")

    def store_record(self, bytes32_hex: str, source_url: str) -> Dict[str, Any]:
        """
        Stores a fingerprint on-chain by calling VerificationRegistry.storeRecord().

        Args:
            bytes32_hex (str): 0x-prefixed 64-char hex string (32 bytes).
            source_url (str): Verified candidate page/source URL.

        Returns:
            dict: Transaction receipt details (tx_hash, block_number, gas_used, status).
        """
        bytes32_val = Web3.to_bytes(hexstr=bytes32_hex)

        if self.account:
            # Build, sign, and broadcast raw transaction
            tx = self.contract.functions.storeRecord(bytes32_val, source_url).build_transaction({
                "from": self.account_address,
                "nonce": self.w3.eth.get_transaction_count(self.account_address),
                "gas": 200000,
                "gasPrice": self.w3.eth.gas_price
            })
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        else:
            # Send transaction via unlocked local node account
            tx_hash = self.contract.functions.storeRecord(bytes32_val, source_url).transact({
                "from": self.account_address
            })

        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        return {
            "transaction_hash": tx_receipt.transactionHash.hex(),
            "block_number": tx_receipt.blockNumber,
            "gas_used": tx_receipt.gasUsed,
            "status": tx_receipt.status,
            "contract_address": self.contract_address,
            "bytes32_hex": bytes32_hex
        }

    def verify_record(self, bytes32_hex: str) -> bool:
        """
        Checks whether a given fingerprint exists on the local blockchain.

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
        Retrieves the recorded fingerprint details from the local blockchain.

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
        print(f"[+] Connected to Blockchain Client! Contract Address: {client.contract_address}")
    except Exception as err:
        print(f"[-] Blockchain Client Error: {err}")
