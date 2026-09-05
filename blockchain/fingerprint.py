"""
Canonical Verification Record & SHA-256 Fingerprint Generator.

HH Goa 2026 Shortlisting Task 3 - Milestone 4.

This module formats verification records into canonical JSON strings and calculates
their deterministic SHA-256 hashes for on-chain blockchain storage.
"""

import json
import hashlib
from typing import Dict, Any


def canonicalize_record(record: Dict[str, Any]) -> str:
    """
    Produces a deterministic, canonical JSON representation of a verification record.

    To ensure identical SHA-256 hashes across different systems:
      - Keys are sorted alphabetically (`sort_keys=True`).
      - Compact separators (',', ':') eliminate non-deterministic whitespace.
      - Dynamic/transient fields (timestamps, local temp paths, tx hashes) are excluded.

    Args:
        record (dict): Dictionary containing core verification attributes.

    Returns:
        str: Deterministic canonical JSON string.
    """
    # Select only deterministic verification fields
    allowed_keys = ["face_distance", "face_match", "image_url", "source", "source_url", "title"]
    
    clean_record = {}
    for k in sorted(allowed_keys):
        if k in record:
            val = record[k]
            # Round floats to 4 decimal places for floating-point consistency
            if isinstance(val, float):
                val = round(val, 4)
            clean_record[k] = val

    canonical_json = json.dumps(clean_record, sort_keys=True, separators=(",", ":"))
    return canonical_json


def create_fingerprint(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates the SHA-256 fingerprint for a verification record.

    1. Converts record to canonical JSON string.
    2. Encodes canonical JSON as UTF-8 bytes.
    3. Calculates SHA-256 hash using hashlib.
    4. Returns canonical JSON, 64-char hex string, and 0x-prefixed hex string for Web3.

    Args:
        record (dict): Verification record dictionary.

    Returns:
        dict:
          - 'canonical_json' (str): Canonical JSON string.
          - 'hex_hash' (str): 64-character SHA-256 hex string.
          - 'bytes32_hex' (str): '0x' prefixed hex string for Solidity bytes32.
          - 'bytes32_raw' (bytes): 32-byte raw representation.
    """
    canonical_str = canonicalize_record(record)
    encoded_bytes = canonical_str.encode("utf-8")
    
    sha256_hash = hashlib.sha256(encoded_bytes).hexdigest()
    bytes32_hex = f"0x{sha256_hash}"
    bytes32_raw = bytes.fromhex(sha256_hash)

    return {
        "canonical_json": canonical_str,
        "hex_hash": sha256_hash,
        "bytes32_hex": bytes32_hex,
        "bytes32_raw": bytes32_raw
    }


if __name__ == "__main__":
    sample_record = {
        "title": "Zoid Kirsch on X: The story of how I came to own a copy of ...",
        "source": "x.com",
        "source_url": "https://x.com/ZoidCTF/status/1414325266298540040",
        "image_url": "https://pbs.twimg.com/media/E6Cv6PCVIAM41zp.png",
        "face_match": True,
        "face_distance": 0.0167
    }

    res = create_fingerprint(sample_record)
    print("Canonical JSON:")
    print(res["canonical_json"])
    print("\nSHA-256 Hex Hash:")
    print(res["hex_hash"])
    print("\nBytes32 Format:")
    print(res["bytes32_hex"])
