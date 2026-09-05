"""
Milestone 3 to Milestone 4 Integration Module.

HH Goa 2026 Shortlisting Task 3 - Milestone 4.

Takes a verified candidate from Milestone 3, formats the canonical verification record,
generates the SHA-256 fingerprint, and stores it on the local blockchain.
"""

import os
import sys
import json
from typing import Dict, Any

# Ensure parent directory imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from blockchain.fingerprint import create_fingerprint
from blockchain.blockchain_client import BlockchainClient

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def store_verified_candidate_on_chain(candidate_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Takes a verified candidate result dictionary, creates the canonical record,
    calculates the SHA-256 fingerprint, and records it on the local blockchain.

    Args:
        candidate_data (dict): Verified candidate record from Milestone 3.

    Returns:
        dict: Summary containing fingerprint, transaction details, and on-chain verification status.
    """
    # 1. Format canonical record
    canonical_record = {
        "title": candidate_data.get("title", "N/A"),
        "source": candidate_data.get("source", "N/A"),
        "source_url": candidate_data.get("page_url", "N/A"),
        "image_url": candidate_data.get("image_url", "N/A"),
        "face_match": candidate_data.get("verified", False),
        "face_distance": round(candidate_data.get("best_distance", 0.0), 4) if candidate_data.get("best_distance") is not None else None
    }

    # 2. Compute SHA-256 Fingerprint
    fp = create_fingerprint(canonical_record)

    # 3. Connect to Blockchain Client & Store
    client = BlockchainClient()
    tx_receipt = client.store_record(fp["bytes32_hex"], canonical_record["source_url"])

    # 4. Verify on-chain presence
    is_verified_on_chain = client.verify_record(fp["bytes32_hex"])
    on_chain_record = client.get_record(fp["bytes32_hex"])

    return {
        "canonical_record": canonical_record,
        "fingerprint_hex": fp["hex_hash"],
        "bytes32_hex": fp["bytes32_hex"],
        "transaction_hash": tx_receipt["transaction_hash"],
        "block_number": tx_receipt["block_number"],
        "contract_address": tx_receipt["contract_address"],
        "on_chain_verified": is_verified_on_chain,
        "block_timestamp": on_chain_record["timestamp"]
    }


def main():
    summary_file = "verification_summary.json"

    if not os.path.exists(summary_file):
        print(f"[-] ERROR: Milestone 3 summary file '{summary_file}' not found. Run Milestone 3 first.", file=sys.stderr)
        sys.exit(1)

    with open(summary_file, "r", encoding="utf-8") as f:
        m3_data = json.load(f)

    best_cand = m3_data.get("best_candidate")
    if not best_cand or not best_cand.get("verified"):
        print("[-] No verified candidate found in Milestone 3 summary.")
        sys.exit(1)

    print(f"\n[*] Integrating Milestone 3 Best Verified Candidate into Blockchain Storage...")
    result = store_verified_candidate_on_chain(best_cand)

    print("\n==================================================")
    print("      MILESTONE 3 -> 4 BLOCKCHAIN INTEGRATION     ")
    print("==================================================")
    print(f"  Title            : {result['canonical_record']['title']}")
    print(f"  Source URL       : {result['canonical_record']['source_url']}")
    print(f"  Face Distance    : {result['canonical_record']['face_distance']}")
    print(f"  SHA-256 Hash     : {result['fingerprint_hex']}")
    print(f"  Contract Address : {result['contract_address']}")
    print(f"  Tx Hash          : {result['transaction_hash']}")
    print(f"  Block Number     : {result['block_number']}")
    print(f"  On-Chain Verified: {result['on_chain_verified']} (VALID)")
    print("==================================================\n")


if __name__ == "__main__":
    main()
