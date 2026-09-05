"""
HH Goa 2026 Shortlisting Task 3 - Main End-to-End Pipeline Entry Point.

Milestone 5: Complete Integrated Pipeline.

Orchestrates:
  1. Input Image Validation & Face Detection (face_processor.py)
  2. Google Lens Reverse Image Search via SerpApi (search/lens_search.py)
  3. Candidate Image Download & ArcFace Face Verification (search/candidate_verifier.py)
  4. Best Match Selection & Safeguard Verification
  5. Canonical Verification Record & SHA-256 Hashing (blockchain/fingerprint.py)
  6. On-Chain Fingerprint Storage & Re-Verification (blockchain/blockchain_client.py)
  7. Final Structured Result Output (`final_result.json`)
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Import modular project components
import face_processor
from search.lens_search import perform_reverse_image_search
from search.candidate_verifier import process_and_verify_candidates
from blockchain.fingerprint import create_fingerprint
from blockchain.blockchain_client import BlockchainClient

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def run_pipeline(image_path: str, top_n: int = 10) -> dict:
    """
    Executes the complete end-to-end face verification and blockchain storage pipeline.

    Args:
        image_path (str): Path to input image file.
        top_n (int): Maximum number of top Google Lens candidates to process.

    Returns:
        dict: Complete structured result dictionary.
    """
    # ---------------------------------------------------------
    # STEP 1: Input Image Validation & Face Processing
    # ---------------------------------------------------------
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Input image file not found: '{image_path}'")

    print("\n============================================================")
    print("  HH GOA 2026 - FACE VERIFICATION & BLOCKCHAIN PIPELINE   ")
    print("============================================================")
    print(f"\n[*] STEP 1: Validating input image and detecting faces...")
    print(f"    - Input Image: {image_path}")

    try:
        faces = face_processor.extract_face(image_path, enforce_detection=True)
        if not faces or len(faces) == 0:
            raise ValueError("No detectable face found in input image.")
        print(f"    [+] Face Detection: SUCCESS ({len(faces)} face(s) detected)")
    except Exception as err:
        raise ValueError(f"No detectable face found in input image. Details: {err}")

    # ---------------------------------------------------------
    # STEP 2: Google Lens Reverse Image Search
    # ---------------------------------------------------------
    print(f"\n[*] STEP 2: Executing Google Lens reverse image search (SerpApi)...")
    try:
        lens_candidates, raw_lens_response = perform_reverse_image_search(image_path, save_raw=True)
        lens_count = len(lens_candidates)
        print(f"    [+] Google Lens Search: CONNECTED")
        print(f"    [+] Visual Matches Returned: {lens_count}")
    except Exception as err:
        raise RuntimeError(f"Google Lens search failed: {err}")

    if lens_count == 0:
        print("    [-] No candidate visual matches returned by Google Lens for this image.")
        return {
            "input_image": image_path,
            "lens_candidates_found": 0,
            "candidates_processed": 0,
            "best_match": None,
            "blockchain": None,
            "status": "NO_LENS_CANDIDATES"
        }

    # ---------------------------------------------------------
    # STEP 3: Candidate Download & ArcFace Verification
    # ---------------------------------------------------------
    print(f"\n[*] STEP 3: Downloading top {top_n} candidates & running ArcFace verification...")
    summary = process_and_verify_candidates(
        original_image_path=image_path,
        candidates=lens_candidates,
        max_candidates=top_n
    )

    best_match = summary.get("best_candidate")

    # ---------------------------------------------------------
    # STEP 4: Best Match Selection & Safeguard Check
    # ---------------------------------------------------------
    if not best_match or not best_match.get("verified"):
        print("\n[-] RESULT: NO VERIFIED FACE MATCH FOUND.")
        print("    (Unverified candidates will NOT be recorded on blockchain.)")
        
        result_payload = {
            "input_image": image_path,
            "lens_candidates_found": lens_count,
            "candidates_processed": summary["processed_candidates_count"],
            "candidate_images_downloaded": summary["download_success_count"],
            "candidates_with_faces": summary["images_with_faces_count"],
            "verified_face_matches": summary["verified_matches_count"],
            "best_match": None,
            "blockchain": None,
            "status": "NO_VERIFIED_MATCH"
        }
        
        with open("final_result.json", "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)
        return result_payload

    print("\n[+] VERIFIED BEST MATCH FOUND:")
    print(f"    - Title         : {best_match['title']}")
    print(f"    - Source Domain : {best_match['source']}")
    print(f"    - Page URL      : {best_match['page_url']}")
    print(f"    - Image URL     : {best_match['image_url']}")
    print(f"    - ArcFace Dist  : {best_match['best_distance']:.4f} (Threshold: {best_match['threshold']:.4f})")
    print(f"    - Match Status  : ✓ FACE MATCH VERIFIED")

    # ---------------------------------------------------------
    # STEP 5: Canonical Record & SHA-256 Fingerprint
    # ---------------------------------------------------------
    print(f"\n[*] STEP 5: Generating canonical record & SHA-256 fingerprint...")
    canonical_record = {
        "title": best_match["title"],
        "source": best_match["source"],
        "source_url": best_match["page_url"],
        "image_url": best_match["image_url"],
        "face_match": True,
        "face_distance": round(best_match["best_distance"], 4)
    }

    fp = create_fingerprint(canonical_record)
    print(f"    - Canonical Record : {fp['canonical_json']}")
    print(f"    - SHA-256 Fingerprint : {fp['hex_hash']}")

    # ---------------------------------------------------------
    # STEP 6: Blockchain Storage & On-Chain Re-Verification
    # ---------------------------------------------------------
    print(f"\n[*] STEP 6: Connecting to local blockchain & recording fingerprint...")
    try:
        blockchain_client = BlockchainClient()
        print(f"    [+] Blockchain: CONNECTED ({blockchain_client.rpc_url})")
        print(f"    [+] Contract Address: {blockchain_client.contract_address}")

        # Store fingerprint on-chain
        tx_receipt = blockchain_client.store_record(fp["bytes32_hex"], canonical_record["source_url"])
        print(f"    [+] Transaction Hash : {tx_receipt['transaction_hash']}")
        print(f"    [+] Block Number     : {tx_receipt['block_number']}")
        print(f"    [+] Gas Used         : {tx_receipt['gas_used']}")

        # Re-verify on-chain state
        is_verified_on_chain = blockchain_client.verify_record(fp["bytes32_hex"])
        print(f"    [+] On-Chain Verification Status: {is_verified_on_chain}")

        if not is_verified_on_chain:
            raise RuntimeError("On-chain fingerprint re-verification failed!")

        print("    [+] FINGERPRINT VERIFIED ON BLOCKCHAIN")

        blockchain_info = {
            "sha256": fp["hex_hash"],
            "bytes32_hex": fp["bytes32_hex"],
            "contract_address": blockchain_client.contract_address,
            "transaction_hash": tx_receipt["transaction_hash"],
            "block_number": tx_receipt["block_number"],
            "verified": is_verified_on_chain
        }

    except Exception as err:
        raise ConnectionError(
            f"Could not connect to local blockchain at configured RPC endpoint.\n"
            f"Please start Ganache on http://127.0.0.1:8545, deploy contract via 'python blockchain/deploy_local.py', and try again.\n"
            f"Error details: {err}"
        )

    # ---------------------------------------------------------
    # STEP 7: Save Structured Result & Generate Final Report
    # ---------------------------------------------------------
    final_payload = {
        "input_image": image_path,
        "lens_candidates_found": lens_count,
        "candidates_processed": summary["processed_candidates_count"],
        "candidate_images_downloaded": summary["download_success_count"],
        "candidates_with_faces": summary["images_with_faces_count"],
        "verified_face_matches": summary["verified_matches_count"],
        "best_match": {
            "title": best_match["title"],
            "source": best_match["source"],
            "page_url": best_match["page_url"],
            "image_url": best_match["image_url"],
            "face_match": True,
            "face_distance": round(best_match["best_distance"], 4)
        },
        "blockchain": blockchain_info,
        "status": "SUCCESS"
    }

    with open("final_result.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    print_cli_report(final_payload)
    return final_payload


def print_cli_report(data: dict):
    """
    Renders clean, human-readable terminal report.
    """
    best = data.get("best_match", {})
    bc = data.get("blockchain", {})

    print("\n" + "=" * 60)
    print("HH GOA 2026 — FACE VERIFICATION & BLOCKCHAIN PIPELINE")
    print("=" * 60)

    print("\nINPUT")
    print("-" * 60)
    print(f"Image:\n{data['input_image']}")
    print("\nFace Detection:\n✓ Face detected")

    print("\nREVERSE IMAGE SEARCH")
    print("-" * 60)
    print("Provider:\nGoogle Lens via SerpApi")
    print(f"\nCandidates Found:\n{data['lens_candidates_found']}")

    print("\nCANDIDATE VERIFICATION")
    print("-" * 60)
    print(f"Candidates Processed:\n{data['candidates_processed']}")
    print(f"\nImages Downloaded:\n{data['candidate_images_downloaded']}")
    print(f"\nCandidates With Faces:\n{data['candidates_with_faces']}")
    print(f"\nFace Matches Verified (ArcFace):\n{data['verified_face_matches']}")

    if best:
        print("\nBEST MATCH")
        print("-" * 60)
        print(f"Title:\n{best.get('title')}")
        print(f"\nSource:\n{best.get('source')}")
        print(f"\nPage URL:\n{best.get('page_url')}")
        print(f"\nImage URL:\n{best.get('image_url')}")
        print(f"\nArcFace Distance:\n{best.get('face_distance')}")
        print("\nFace Match:\n✓ FACE MATCH VERIFIED")

    if bc:
        print("\nBLOCKCHAIN")
        print("-" * 60)
        print(f"SHA-256:\n{bc.get('sha256')}")
        print(f"\nContract:\n{bc.get('contract_address')}")
        print(f"\nTransaction:\n{bc.get('transaction_hash')}")
        print(f"\nBlock:\n{bc.get('block_number')}")
        print("\nBlockchain Verification:\n✓ FINGERPRINT VERIFIED ON BLOCKCHAIN")

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)
    print("FACE MATCH:\n✓ VERIFIED")
    print("\nBLOCKCHAIN RECORD:\n✓ VERIFIED ON-CHAIN")
    print("=" * 60 + "\n")
    print("[+] Full structured pipeline output saved to 'final_result.json'\n")


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa 2026 Task 3: Integrated End-to-End Pipeline CLI"
    )
    parser.add_argument(
        "--image", "-i", required=True, help="Path to local input image file"
    )
    parser.add_argument(
        "--top", "-t", type=int, default=10, help="Number of top candidates to process (default: 10)"
    )

    args = parser.parse_args()

    try:
        run_pipeline(image_path=args.image, top_n=args.top)
    except Exception as err:
        print(f"\n[-] ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
