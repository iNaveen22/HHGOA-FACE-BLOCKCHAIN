"""
Google Lens Reverse Image Search Module using SerpApi.

HH Goa 2026 Shortlisting Task 3 - Milestone 2.

This module uploads a local image to SerpApi's /image API endpoint to get an image_id,
then queries SerpApi's Google Lens search engine to retrieve structured web results.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

# Ensure stdout uses UTF-8 encoding on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


SERPAPI_UPLOAD_URL = "https://serpapi.com/image"
SERPAPI_SEARCH_URL = "https://serpapi.com/search"


def load_api_key() -> str:
    """
    Loads SERPAPI_KEY from .env file or environment variables.

    Returns:
        str: Valid API key string.

    Raises:
        ValueError: If SERPAPI_KEY is missing or empty.
    """
    load_dotenv()
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key or not api_key.strip():
        raise ValueError(
            "SERPAPI_KEY not found in .env or environment variables. "
            "Please add SERPAPI_KEY=your_key to your .env file."
        )
    return api_key.strip()


def upload_image_to_serpapi(image_path: str, api_key: str) -> str:
    """
    Uploads a local image file to SerpApi to obtain a temporary image_id.

    Args:
        image_path (str): Path to local image file.
        api_key (str): SerpApi API key.

    Returns:
        str: image_id returned by SerpApi.

    Raises:
        FileNotFoundError: If image file does not exist.
        RuntimeError: If API upload request fails or returns an error status.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Local image file not found: '{image_path}'")

    print(f"[*] Uploading local image to SerpApi: {image_path}")
    params = {"api_key": api_key}

    try:
        with open(image_path, "rb") as image_file:
            files = {"image": image_file}
            response = requests.post(
                SERPAPI_UPLOAD_URL,
                params=params,
                files=files,
                timeout=30
            )

        if response.status_code != 200:
            raise RuntimeError(
                f"SerpApi image upload failed with status code {response.status_code}: {response.text}"
            )

        data = response.json()
        image_id = data.get("image_id")

        if not image_id:
            raise RuntimeError(
                f"SerpApi upload response did not contain 'image_id': {data}"
            )

        print(f"[+] Image uploaded successfully. Obtained image_id: {image_id}")
        return image_id

    except requests.RequestException as err:
        raise RuntimeError(f"HTTP request error during image upload: {err}")


def search_google_lens(image_id: str, api_key: str) -> dict:
    """
    Queries SerpApi Google Lens engine using an image_id.

    Args:
        image_id (str): Image ID obtained from SerpApi upload.
        api_key (str): SerpApi API key.

    Returns:
        dict: Raw JSON response dictionary from SerpApi.

    Raises:
        RuntimeError: If search request fails or returns non-200 status.
    """
    print(f"[*] Executing Google Lens search for image_id: {image_id}")
    params = {
        "engine": "google_lens",
        "image_id": image_id,
        "api_key": api_key
    }

    try:
        response = requests.get(SERPAPI_SEARCH_URL, params=params, timeout=30)
        
        if response.status_code != 200:
            raise RuntimeError(
                f"SerpApi Google Lens search failed with status code {response.status_code}: {response.text}"
            )

        data = response.json()

        if "error" in data:
            raise RuntimeError(f"SerpApi error: {data['error']}")

        print(f"[+] Google Lens search completed successfully.")
        return data

    except requests.RequestException as err:
        raise RuntimeError(f"HTTP request error during Google Lens search: {err}")


def parse_lens_results(raw_response: dict) -> list:
    """
    Parses candidate web results from Google Lens raw response.

    Extracts:
      - position
      - title
      - source
      - page_url (link)
      - image_url (original image URL)
      - thumbnail_url
      - image_width
      - image_height

    Args:
        raw_response (dict): SerpApi JSON response.

    Returns:
        list of dict: Parsed structured candidates list.
    """
    candidates = []

    # Visual matches are the primary candidate web matches in Google Lens
    visual_matches = raw_response.get("visual_matches", [])

    for idx, match in enumerate(visual_matches, 1):
        candidates.append({
            "position": match.get("position", idx),
            "title": match.get("title", "N/A"),
            "source": match.get("source", "N/A"),
            "page_url": match.get("link", "N/A"),
            "image_url": match.get("image", "N/A"),
            "thumbnail_url": match.get("thumbnail", "N/A"),
            "image_width": match.get("image_width", None),
            "image_height": match.get("image_height", None)
        })

    return candidates


def perform_reverse_image_search(image_path: str, save_raw: bool = True) -> tuple:
    """
    Executes the full reverse image search pipeline:
    1. Loads API Key
    2. Uploads local image to SerpApi
    3. Performs Google Lens Search
    4. Saves raw response JSON temporarily for inspection
    5. Returns (parsed_candidates, raw_response)

    Args:
        image_path (str): Local image path.
        save_raw (bool): Whether to save raw JSON response to search_raw_response.json.

    Returns:
        tuple: (list of dict parsed candidates, dict raw response)
    """
    api_key = load_api_key()
    image_id = upload_image_to_serpapi(image_path, api_key)
    raw_response = search_google_lens(image_id, api_key)

    if save_raw:
        raw_output_path = "search_raw_response.json"
        with open(raw_output_path, "w", encoding="utf-8") as f:
            json.dump(raw_response, f, indent=2)
        print(f"[+] Saved raw SerpApi response to '{raw_output_path}'")

    candidates = parse_lens_results(raw_response)
    return candidates, raw_response


def main():
    parser = argparse.ArgumentParser(
        description="Milestone 2: Google Lens Reverse Image Search CLI via SerpApi"
    )
    parser.add_argument(
        "--image", "-i", required=True, help="Path to local image file to search"
    )

    args = parser.parse_args()

    try:
        candidates, raw_resp = perform_reverse_image_search(args.image)

        print(f"\n==================================================")
        print(f"       GOOGLE LENS REVERSE IMAGE SEARCH RESULTS   ")
        print(f"==================================================")
        print(f"Total Visual Matches Found: {len(candidates)}\n")

        if not candidates:
            print("[-] No visual matches returned by Google Lens for this image.")
        else:
            for candidate in candidates[:10]:
                print(f"[{candidate['position']}] {candidate['title']}")
                print(f"    - Source Domain : {candidate['source']}")
                print(f"    - Page URL      : {candidate['page_url']}")
                print(f"    - Image URL     : {candidate['image_url']}")
                print(f"    - Thumbnail URL : {candidate['thumbnail_url']}")
                print(f"    - Dimensions    : {candidate['image_width']} x {candidate['image_height']}")
                print("-" * 50)

            if len(candidates) > 10:
                print(f"... and {len(candidates) - 10} more candidate results.")

    except Exception as err:
        print(f"\n[-] ERROR: {err}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
