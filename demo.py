"""
Demo CLI Script for HH Goa 2026 Shortlisting Task 3 - Milestone 1.

Usage:
  1. Extract Face:
     python demo.py extract --image path/to/image.jpg

  2. Generate ArcFace Embedding:
     python demo.py embed --image path/to/image.jpg

  3. Verify Two Faces:
     python demo.py verify --image path/to/image1.jpg --compare path/to/image2.jpg
"""

import argparse
import sys
import os
import face_processor


def main():
    parser = argparse.ArgumentParser(
        description="HH Goa Milestone 1: Face Processing CLI (DeepFace + ArcFace)"
    )
    
    # Define CLI subcommands: extract, embed, verify
    subparsers = parser.add_subparsers(dest="command", help="Sub-command to execute")

    # 1. Extract subcommand
    extract_parser = subparsers.add_parser("extract", help="Detect and extract face from image")
    extract_parser.add_argument("--image", "-i", required=True, help="Path to input image")

    # 2. Embed subcommand
    embed_parser = subparsers.add_parser("embed", help="Generate 512-D ArcFace face embedding")
    embed_parser.add_argument("--image", "-i", required=True, help="Path to input image")

    # 3. Verify subcommand
    verify_parser = subparsers.add_parser("verify", help="Verify if two face images match")
    verify_parser.add_argument("--image", "-i", required=True, help="Path to first image")
    verify_parser.add_argument("--compare", "-c", required=True, help="Path to second image")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "extract":
            print(f"[*] Extracting face from: {args.image}")
            faces = face_processor.extract_face(args.image, enforce_detection=True)
            print(f"[+] Detection Successful!")
            print(f"    - Detected Faces Count: {len(faces)}")
            for idx, face_info in enumerate(faces, 1):
                area = face_info.get("facial_area", {})
                conf = face_info.get("confidence", "N/A")
                print(f"    - Face #{idx}: Bounding Box = x:{area.get('x')}, y:{area.get('y')}, w:{area.get('w')}, h:{area.get('h')} | Confidence: {conf}")

        elif args.command == "embed":
            print(f"[*] Generating ArcFace embedding for: {args.image}")
            embedding = face_processor.generate_embedding(args.image, enforce_detection=True)
            print(f"[+] Embedding Generated Successfully!")
            print(f"    - Vector Dimensions: {len(embedding)}")
            print(f"    - Preview (first 10 components): {embedding[:10]}")

        elif args.command == "verify":
            print(f"[*] Verifying face match between:")
            print(f"    - Image 1: {args.image}")
            print(f"    - Image 2: {args.compare}")
            result = face_processor.verify_faces(args.image, args.compare, enforce_detection=True)
            
            print("\n[+] Verification Result:")
            print(f"    - Verified Match  : {result['verified']}")
            print(f"    - Distance        : {result['distance']:.4f}")
            print(f"    - Model Threshold : {result['threshold']:.4f}")
            print(f"    - Metric          : {result['similarity_metric']}")
            print(f"    - Model Used      : {result['model']}")
            
            if result['verified']:
                print("\n-> CONCLUSION: SAME PERSON (Face Match)")
            else:
                print("\n-> CONCLUSION: DIFFERENT PERSON (No Match)")

    except Exception as e:
        print(f"\n[-] ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
