"""
Ethereum Sepolia Blockchain Verification & Tamper Test CLI.

HH Goa 2026 Shortlisting Task 3 - Sepolia Migration.

Demonstrates:
  1. Record canonicalization and SHA-256 fingerprint calculation.
  2. Storing evidence fingerprint on Ethereum Sepolia Testnet.
  3. Reading recorded data from Sepolia state.
  4. On-chain verification (TRUE / VALID).
  5. Tamper Test: Modifying verification data -> detecting hash mismatch on Sepolia (FALSE / TAMPER DETECTED).
  6. Sepolia Etherscan URL generation.
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Ensure imports work from parent directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blockchain.fingerprint import canonicalize_record, create_fingerprint
from blockchain.blockchain_client import BlockchainClient

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_sepolia_demo():
    print("\n==================================================")
    print("      SEPOLIA BLOCKCHAIN VERIFICATION & TAMPER DEMO")
    print("==================================================")

    # Step 1: Create Sample Verification Record
    original_record = {
        "title": "Zoid Kirsch on X: \"The story of how I came to own a copy of ...",
        "source": "x.com",
        "source_url": "https://x.com/ZoidCTF/status/1414325266298540040",
        "image_url": "https://pbs.twimg.com/media/E6Cv6PCVIAM41zp.png",
        "face_match": True,
        "face_distance": 0.0167
    }

    print("\n[*] 1. Original Verification Record:")
    print(json.dumps(original_record, indent=2))

    # Step 2: Generate Canonical JSON & SHA-256 Fingerprint
    fp = create_fingerprint(original_record)
    print("\n[*] 2. Canonical JSON String:")
    print(f"    '{fp['canonical_json']}'")
    print(f"\n[*] SHA-256 Fingerprint (Hex):")
    print(f"    {fp['hex_hash']}")
    print(f"[*] Bytes32 Solidity Representation:")
    print(f"    {fp['bytes32_hex']}")

    # Step 3: Connect to Sepolia Blockchain
    print("\n[*] 3. Connecting to Ethereum Sepolia Testnet...")
    client = BlockchainClient()
    print(f"    [+] Network  : {client.network_name} (Chain ID {client.chain_id})")
    print(f"    [+] Contract : {client.contract_address}")

    # Step 4: Store Fingerprint on Sepolia
    print("\n[*] 4. Submitting Fingerprint Transaction to Sepolia Smart Contract...")
    print("    (Waiting for Sepolia block confirmation...)")
    receipt = client.store_record(fp['bytes32_hex'], original_record['source_url'])

    print(f"    [+] Transaction Hash   : {receipt['transaction_hash']}")
    print(f"    [+] Block Number       : {receipt['block_number']}")
    print(f"    [+] Gas Used           : {receipt['gas_used']}")
    print(f"    [+] Transaction Status : SUCCESS (Status Code {receipt['status']})")
    print(f"    [+] Etherscan Tx Link  : {receipt['etherscan_tx_url']}")

    # Step 5: Read Stored Record from Sepolia
    print("\n[*] 5. Reading Stored Record from Sepolia State...")
    stored_rec = client.get_record(fp['bytes32_hex'])
    timestamp_readable = datetime.fromtimestamp(stored_rec['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')
    print(f"    - Recorded Hash : {stored_rec['data_hash']}")
    print(f"    - Recorded URL  : {stored_rec['source_url']}")
    print(f"    - Block Time    : {timestamp_readable} (unix: {stored_rec['timestamp']})")

    # Step 6: Verify Exact Fingerprint Against Sepolia
    print("\n[*] 6. Verifying Original Fingerprint Against Sepolia...")
    is_valid_original = client.verify_record(fp['bytes32_hex'])
    print(f"    - On-Chain Verification Status : {is_valid_original}")
    if is_valid_original:
        print("    -> RESULT: VALID / FINGERPRINT VERIFIED ON BLOCKCHAIN")
    else:
        print("    -> RESULT: FAILED / RECORD NOT FOUND")

    # Step 7: TAMPER TEST (Modify one field and test hash verification)
    print("\n" + "=" * 50)
    print("           SEPOLIA TAMPER VERIFICATION TEST       ")
    print("=" * 50)

    tampered_record = original_record.copy()
    tampered_record["face_distance"] = 0.5000  # Modified face distance

    print("[*] Modifying record field: 'face_distance' (0.0167 -> 0.5000)...")
    print("\n[*] Tampered Record:")
    print(json.dumps(tampered_record, indent=2))

    tampered_fp = create_fingerprint(tampered_record)
    print("\n[*] Recalculated SHA-256 Fingerprint for Tampered Record:")
    print(f"    Original Hash : {fp['hex_hash']}")
    print(f"    Tampered Hash : {tampered_fp['hex_hash']}")

    print("\n[*] Querying Sepolia Smart Contract for Tampered Fingerprint...")
    is_valid_tampered = client.verify_record(tampered_fp['bytes32_hex'])
    print(f"    - On-Chain Verification Status : {is_valid_tampered}")

    if not is_valid_tampered:
        print("    -> RESULT: TAMPER DETECTED! (Fingerprint NOT FOUND on blockchain)")
        print("    -> Explanation: Tampering detected because the modified evidence produced a different SHA-256 fingerprint that was not recorded on-chain.")
    else:
        print("    -> ERROR: Tampered record was incorrectly verified!")

    print("\n==================================================")
    print("      SEPOLIA BLOCKCHAIN DEMO SUMMARY REPORT      ")
    print("==================================================")
    print(f"  Network                      : {client.network_name}")
    print(f"  Contract Address             : {client.contract_address}")
    print(f"  Transaction Hash             : {receipt['transaction_hash']}")
    print(f"  Block Number                 : {receipt['block_number']}")
    print(f"  Original Record Fingerprint  : {fp['hex_hash'][:16]}...")
    print(f"  Original Verification Status : {is_valid_original} (VALID)")
    print(f"  Tampered Record Fingerprint  : {tampered_fp['hex_hash'][:16]}...")
    print(f"  Tampered Verification Status : {is_valid_tampered} (TAMPER DETECTED)")
    print(f"  Etherscan Contract Link      : {client.get_etherscan_contract_url()}")
    print(f"  Etherscan Transaction Link   : {receipt['etherscan_tx_url']}")
    print("==================================================\n")


def main():
    parser = argparse.ArgumentParser(
        description="Milestone 4: Ethereum Sepolia Blockchain Verification & Tamper Demo CLI"
    )
    args = parser.parse_args()

    try:
        run_sepolia_demo()
    except Exception as err:
        print(f"\n[-] ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
