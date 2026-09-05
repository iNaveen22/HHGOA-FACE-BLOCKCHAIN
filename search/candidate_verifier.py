"""
Candidate Image Face Verification Module for HH Goa 2026 Task 3 - Milestone 3.

This module downloads candidate images returned by Google Lens (Milestone 2)
and performs ArcFace face verification against the original input image using DeepFace (Milestone 1).
"""

import os
import sys
import json
import argparse
import requests
from PIL import Image, UnidentifiedImageError
from dotenv import load_dotenv

# Ensure imports from parent directory and search package work seamlessly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import face_processor
from search.lens_search import perform_reverse_image_search

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


DOWNLOAD_DIR = "candidate_downloads"


def download_image(url: str, save_path: str, timeout: int = 10) -> bool:
    """
    Downloads an image from a URL and verifies that it is a valid image file.

    Args:
        url (str): Image URL to download.
        save_path (str): Local filepath to save the downloaded image.
        timeout (int): HTTP request timeout in seconds.

    Returns:
        bool: True if downloaded and validated successfully, False otherwise.
    """
    if not url or url == "N/A" or not url.startswith("http"):
        return False

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        if response.status_code != 200:
            return False

        with open(save_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        # Verify image integrity with PIL
        with Image.open(save_path) as img:
            img.verify()

        return True

    except Exception:
        # If download or verification fails, cleanup partial file if created
        if os.path.exists(save_path):
            try:
                os.remove(save_path)
            except OSError:
                pass
        return False


def verify_candidate(original_image_path: str, candidate_image_path: str) -> dict:
    """
    Performs face detection and ArcFace verification between original image and candidate image.

    Args:
        original_image_path (str): Path to original input image.
        candidate_image_path (str): Path to downloaded candidate image.

    Returns:
        dict:
          - 'faces_detected_count' (int)
          - 'verified' (bool)
          - 'best_distance' (float or None)
          - 'threshold' (float or None)
          - 'error' (str or None)
    """
    try:
        # Step 1: Detect faces in candidate image
        # DeepFace.extract_faces with enforce_detection=False handles images with or without faces
        extracted_faces = face_processor.extract_face(
            candidate_image_path, enforce_detection=False
        )

        # Filter faces with valid confidence
        valid_faces = [
            f for f in extracted_faces if f.get("confidence", 0) > 0.40
        ]
        faces_count = len(valid_faces)

        if faces_count == 0:
            return {
                "faces_detected_count": 0,
                "verified": False,
                "best_distance": None,
                "threshold": None,
                "error": "No face detected in candidate image"
            }

        # Step 2: Perform ArcFace verification using DeepFace's built-in thresholding mechanism
        # DeepFace.verify evaluates the candidate image against original image
        verification_result = face_processor.verify_faces(
            original_image_path, candidate_image_path, enforce_detection=False
        )

        return {
            "faces_detected_count": faces_count,
            "verified": verification_result.get("verified", False),
            "best_distance": verification_result.get("distance", None),
            "threshold": verification_result.get("threshold", None),
            "error": None
        }

    except Exception as err:
        return {
            "faces_detected_count": 0,
            "verified": False,
            "best_distance": None,
            "threshold": None,
            "error": f"Verification error: {str(err)}"
        }


def process_and_verify_candidates(
    original_image_path: str, candidates: list, max_candidates: int = 10
) -> dict:
    """
    Downloads top candidate images, performs ArcFace verification, and ranks results.

    Args:
        original_image_path (str): Path to original input image.
        candidates (list): List of candidate dictionaries from Google Lens search.
        max_candidates (int): Maximum number of candidates to process.

    Returns:
        dict: Aggregated pipeline summary and structured verified candidate list.
    """
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    selected_candidates = candidates[:max_candidates]

    results = []
    download_success_count = 0
    faces_detected_count = 0
    verified_matches_count = 0

    print(f"\n[*] Processing Top {len(selected_candidates)} Lens Candidates for ArcFace Verification...")
    print("=" * 70)

    for idx, candidate in enumerate(selected_candidates, 1):
        pos = candidate.get("position", idx)
        title = candidate.get("title", "N/A")
        page_url = candidate.get("page_url", "N/A")
        image_url = candidate.get("image_url", "N/A")
        thumb_url = candidate.get("thumbnail_url", "N/A")

        print(f"\n[{idx}/{len(selected_candidates)}] Candidate #{pos}: {title[:60]}...")
        print(f"    - Domain   : {candidate.get('source', 'N/A')}")
        print(f"    - Page URL : {page_url}")

        # Path for downloaded candidate image
        save_filename = f"candidate_{pos}.jpg"
        save_path = os.path.join(DOWNLOAD_DIR, save_filename)

        # Attempt download: Try image_url first, fallback to thumbnail_url
        downloaded = download_image(image_url, save_path)
        used_url = image_url

        if not downloaded and thumb_url and thumb_url != "N/A":
            print("    - Primary image download failed; attempting thumbnail fallback...")
            downloaded = download_image(thumb_url, save_path)
            used_url = thumb_url

        if not downloaded:
            print("    [-] Image Download Status: FAILED")
            results.append({
                "position": pos,
                "title": title,
                "source": candidate.get("source", "N/A"),
                "page_url": page_url,
                "image_url": image_url,
                "thumbnail_url": thumb_url,
                "downloaded_path": None,
                "download_status": "failed",
                "faces_detected_count": 0,
                "verified": False,
                "best_distance": None,
                "threshold": None,
                "error": "Failed to download image from primary and thumbnail URLs"
            })
            continue

        download_success_count += 1
        print(f"    [+] Image Download Status: SUCCESS ({save_path})")

        # Perform ArcFace Verification
        ver_res = verify_candidate(original_image_path, save_path)
        faces_in_img = ver_res["faces_detected_count"]
        is_verified = ver_res["verified"]

        if faces_in_img > 0:
            faces_detected_count += 1

        if is_verified:
            verified_matches_count += 1
            print(f"    [+] ArcFace Verification : VERIFIED MATCH (Verified=True, Distance={ver_res['best_distance']:.4f}, Threshold={ver_res['threshold']:.4f})")
        elif faces_in_img > 0:
            print(f"    [-] ArcFace Verification : NO MATCH (Verified=False, Distance={ver_res['best_distance']:.4f}, Threshold={ver_res['threshold']:.4f})")
        else:
            print(f"    [-] ArcFace Verification : SKIPPED ({ver_res['error']})")

        results.append({
            "position": pos,
            "title": title,
            "source": candidate.get("source", "N/A"),
            "page_url": page_url,
            "image_url": used_url,
            "thumbnail_url": thumb_url,
            "downloaded_path": save_path,
            "download_status": "success",
            "faces_detected_count": faces_in_img,
            "verified": is_verified,
            "best_distance": ver_res["best_distance"],
            "threshold": ver_res["threshold"],
            "error": ver_res["error"]
        })

    # Rank Candidates: Verified matches first (sorted by distance asc), then unverified (distance asc), then failures
    def ranking_key(item):
        is_verified = item["verified"]
        has_distance = item["best_distance"] is not None
        dist = item["best_distance"] if has_distance else 999.0

        if is_verified:
            return (0, dist)
        elif has_distance:
            return (1, dist)
        else:
            return (2, 999.0)

    ranked_results = sorted(results, key=ranking_key)

    # Find best matching candidate
    best_candidate = None
    for r in ranked_results:
        if r["verified"] and r["best_distance"] is not None:
            best_candidate = r
            break

    if not best_candidate and len(ranked_results) > 0:
        # If no verified match, select candidate with smallest distance
        valid_dist_candidates = [r for r in ranked_results if r["best_distance"] is not None]
        if valid_dist_candidates:
            best_candidate = valid_dist_candidates[0]

    return {
        "total_lens_candidates": len(candidates),
        "processed_candidates_count": len(selected_candidates),
        "download_success_count": download_success_count,
        "images_with_faces_count": faces_detected_count,
        "verified_matches_count": verified_matches_count,
        "best_candidate": best_candidate,
        "ranked_candidates": ranked_results
    }


def main():
    parser = argparse.ArgumentParser(
        description="Milestone 3: Candidate Image Face Verification CLI (DeepFace + ArcFace + Google Lens)"
    )
    parser.add_argument(
        "--image", "-i", required=True, help="Path to original input image"
    )
    parser.add_argument(
        "--top", "-t", type=int, default=10, help="Number of top candidates to process (default: 10)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.image):
        print(f"[-] ERROR: Original image file not found: '{args.image}'", file=sys.stderr)
        sys.exit(1)

    try:
        # Step 1: Execute Google Lens Search
        print(f"[*] Step 1: Performing Google Lens reverse image search for: {args.image}")
        lens_candidates, raw_response = perform_reverse_image_search(args.image, save_raw=True)

        if not lens_candidates:
            print("[-] No candidates returned by Google Lens search.")
            sys.exit(0)

        # Step 2: Download & Verify Top Candidates using ArcFace
        summary = process_and_verify_candidates(
            original_image_path=args.image,
            candidates=lens_candidates,
            max_candidates=args.top
        )

        # Step 3: Print Pipeline Execution Summary
        print("\n" + "=" * 70)
        print("       MILESTONE 3: CANDIDATE FACE VERIFICATION SUMMARY REPORT      ")
        print("=" * 70)
        print(f"  Total Google Lens Candidates Returned : {summary['total_lens_candidates']}")
        print(f"  Processed Candidates Count            : {summary['processed_candidates_count']}")
        print(f"  Successfully Downloaded Images        : {summary['download_success_count']}")
        print(f"  Candidate Images Containing Faces     : {summary['images_with_faces_count']}")
        print(f"  Verified Identity Matches (ArcFace)   : {summary['verified_matches_count']}")
        print("=" * 70)

        best = summary["best_candidate"]
        if best:
            print("\n[+] BEST MATCHING CANDIDATE:")
            print(f"    - Title            : {best['title']}")
            print(f"    - Source Domain    : {best['source']}")
            print(f"    - Page URL         : {best['page_url']}")
            print(f"    - Image URL        : {best['image_url']}")
            print(f"    - Verified Match   : {best['verified']}")
            if best['best_distance'] is not None:
                print(f"    - ArcFace Distance : {best['best_distance']:.4f}")
                print(f"    - Model Threshold  : {best['threshold']:.4f}")
            else:
                print("    - ArcFace Distance : N/A (No face detected or processing error)")
        else:
            print("\n[-] No suitable candidate found for face verification.")

        # Save verification summary JSON
        with open("verification_summary.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"\n[+] Full verification report saved to 'verification_summary.json'")

    except Exception as err:
        print(f"\n[-] ERROR during pipeline execution: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
