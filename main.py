"""
HH Goa 2026 Shortlisting Task 3 - Main End-to-End Pipeline Entry Point.

Milestone 5 & 6 Integrated Terminal Experience.
Supports both non-interactive CLI arguments (--image, --top) and an interactive CLI mode.

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
    # Clean input path (strip surrounding quotes and whitespace)
    clean_path = image_path.strip().strip('"').strip("'")
    if not os.path.exists(clean_path):
        raise FileNotFoundError(f"Input image file not found: '{clean_path}'")

    print("\n============================================================")
    print("HH Goa 2026 — Face Identification & Blockchain Verification")
    print("============================================================")

    # ---------------------------------------------------------
    # SECTION 1: INPUT FACE
    # ---------------------------------------------------------
    print("\n[1/4] INPUT FACE")
    print("-" * 60)
    print(f"Image:\n{clean_path}")

    try:
        faces = face_processor.extract_face(clean_path, enforce_detection=True)
        if not faces or len(faces) == 0:
            raise ValueError("No detectable face found in input image.")
        print(f"\nFaces detected:\n{len(faces)}")
    except Exception as err:
        raise ValueError(f"No detectable face found in input image. Details: {err}")

    # ---------------------------------------------------------
    # SECTION 2: GOOGLE LENS REVERSE SEARCH
    # ---------------------------------------------------------
    print("\n[2/4] GOOGLE LENS REVERSE SEARCH")
    print("-" * 60)
    try:
        lens_candidates, raw_lens_response = perform_reverse_image_search(clean_path, save_raw=True)
        lens_count = len(lens_candidates)
        print("✓ Search completed")
        print(f"✓ Visual matches found: {lens_count}")
    except Exception as err:
        raise RuntimeError(f"Google Lens search failed: {err}")

    if lens_count == 0:
        print("\n[-] No candidate visual matches returned by Google Lens for this image.")
        return {
            "input_image": clean_path,
            "lens_candidates_found": 0,
            "candidates_processed": 0,
            "best_match": None,
            "blockchain": None,
            "status": "NO_LENS_CANDIDATES"
        }

    # ---------------------------------------------------------
    # SECTION 3: ARCFACE FACE MATCH VERIFICATION
    # ---------------------------------------------------------
    print("\n[3/4] ARCFACE FACE MATCH VERIFICATION")
    print("-" * 60)
    summary = process_and_verify_candidates(
        original_image_path=clean_path,
        candidates=lens_candidates,
        max_candidates=top_n
    )

    ranked = summary.get("ranked_candidates", [])
    verified_candidates = [c for c in ranked if c.get("verified")]

    print("\nMATCHED WEB RESULTS")
    print("-" * 60)

    # Display up to 5 top verified matches
    top_display_matches = verified_candidates[:5]
    if top_display_matches:
        for idx, match in enumerate(top_display_matches, 1):
            dist_val = f"{match['best_distance']:.4f}" if match.get("best_distance") is not None else "N/A"
            print(f"[{idx}] ✓ FACE MATCH")
            print(f"Source: {match.get('source', 'N/A')}")
            print(f"Title: {match.get('title', 'N/A')}")
            print(f"URL: {match.get('page_url', 'N/A')}")
            print(f"ArcFace Distance: {dist_val}\n")
    else:
        print("[-] No verified face matches found among processed candidates.\n")

    print("-" * 60)
    print(f"Candidates analyzed: {summary['processed_candidates_count']}")
    print(f"Face Matches Verified (ArcFace): {summary['verified_matches_count']}")

    best_match = summary.get("best_candidate")

    if not best_match or not best_match.get("verified"):
        print("\n[-] RESULT: NO VERIFIED FACE MATCH FOUND.")
        print("    (Unverified candidates will NOT be recorded on blockchain.)")

        result_payload = {
            "input_image": clean_path,
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

    print("\nBEST FACE MATCH")
    print("-" * 60)
    print(f"Title: {best_match['title']}")
    print(f"Source: {best_match['source']}")
    print(f"Page URL: {best_match['page_url']}")
    print(f"Image URL: {best_match['image_url']}")
    print(f"ArcFace Distance: {best_match['best_distance']:.4f}")
    print(f"Threshold: {best_match['threshold']:.4f}")
    print("-" * 60)

    # ---------------------------------------------------------
    # SECTION 4: ETHEREUM SEPOLIA BLOCKCHAIN
    # ---------------------------------------------------------
    print("\n[4/4] ETHEREUM SEPOLIA BLOCKCHAIN")
    print("-" * 60)

    canonical_record = {
        "title": best_match["title"],
        "source": best_match["source"],
        "source_url": best_match["page_url"],
        "image_url": best_match["image_url"],
        "face_match": True,
        "face_distance": round(best_match["best_distance"], 4)
    }

    fp = create_fingerprint(canonical_record)

    try:
        blockchain_client = BlockchainClient()

        # Store fingerprint on-chain
        tx_receipt = blockchain_client.store_record(fp["bytes32_hex"], canonical_record["source_url"])

        # Re-verify on-chain state
        is_verified_on_chain = blockchain_client.verify_record(fp["bytes32_hex"])

        if not is_verified_on_chain:
            raise RuntimeError("On-chain fingerprint re-verification failed!")

        print("Canonical Evidence Fingerprint")
        print(f"SHA-256:\n{fp['hex_hash']}")
        print(f"\nNetwork:\n{blockchain_client.network_name}")
        print(f"\nContract:\n{blockchain_client.contract_address}")
        print(f"\nTransaction:\n{tx_receipt['transaction_hash']}")
        print(f"\nBlock:\n{tx_receipt['block_number']}")
        print("\n✓ FINGERPRINT STORED ON BLOCKCHAIN")
        print("✓ ON-CHAIN VERIFICATION: TRUE")

        etherscan_url = tx_receipt.get("etherscan_tx_url", "N/A")
        print(f"\nETHERSCAN\n{etherscan_url}")

        blockchain_info = {
            "sha256": fp["hex_hash"],
            "bytes32_hex": fp["bytes32_hex"],
            "network_name": blockchain_client.network_name,
            "chain_id": blockchain_client.chain_id,
            "contract_address": blockchain_client.contract_address,
            "transaction_hash": tx_receipt["transaction_hash"],
            "block_number": tx_receipt["block_number"],
            "etherscan_tx_url": etherscan_url,
            "etherscan_contract_url": tx_receipt.get("etherscan_contract_url"),
            "verified": is_verified_on_chain
        }

    except Exception as err:
        raise ConnectionError(
            f"Could not connect to blockchain at configured RPC endpoint.\n"
            f"Please verify your SEPOLIA_RPC_URL in .env or deploy local contract.\n"
            f"Error details: {err}"
        )

    # ---------------------------------------------------------
    # FINAL SUMMARY
    # ---------------------------------------------------------
    final_payload = {
        "input_image": clean_path,
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

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print("Input Face              : ✓ Detected")
    print("Google Lens Search      : ✓ Completed")
    print(f"Candidates Analyzed     : {summary['processed_candidates_count']}")
    print(f"Face Matches Verified   : {summary['verified_matches_count']}")
    print("Best Face Match         : ✓")
    print("SHA-256 Fingerprint     : ✓ Generated")
    print("Sepolia Registration    : ✓ Confirmed")
    print("Blockchain Verification : ✓ TRUE")
    print(f"\nEtherscan:\n{etherscan_url}")
    print("=" * 60 + "\n")

    return final_payload


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa 2026 Task 3: Integrated End-to-End Pipeline CLI"
    )
    parser.add_argument(
        "--image", "-i", default=None, help="Path to local input image file"
    )
    parser.add_argument(
        "--top", "-t", type=int, default=10, help="Number of top candidates to process (default: 10)"
    )

    args = parser.parse_args()

    image_path = args.image

    # If --image is omitted, enter Interactive Mode
    if not image_path:
        print("\n============================================================")
        print("HH Goa 2026 — Face Identification & Blockchain Verification")
        print("============================================================")
        print("\nEnter path to face image:")
        try:
            user_input = input("> ")
            image_path = user_input.strip().strip('"').strip("'")
        except (KeyboardInterrupt, EOFError):
            print("\n[-] Operation cancelled by user.")
            sys.exit(0)

        if not image_path:
            print("[-] ERROR: No image path entered.", file=sys.stderr)
            sys.exit(1)

    if not os.path.exists(image_path):
        print(f"[-] ERROR: Image file not found: '{image_path}'", file=sys.stderr)
        sys.exit(1)

    try:
        run_pipeline(image_path=image_path, top_n=args.top)
    except Exception as err:
        print(f"\n[-] ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
