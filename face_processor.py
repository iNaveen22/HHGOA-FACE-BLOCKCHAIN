"""
Face Processor Module for HH Goa 2026 Shortlisting Task 3 - Milestone 1.

This module provides face processing functionalities using the DeepFace library
specifically configured with the ArcFace recognition model.

Key Features:
- Face Detection & Extraction
- Face Embedding Generation (using ArcFace)
- Face Verification between two images (using ArcFace's built-in thresholding)
"""

import os
import numpy as np
from deepface import DeepFace


MODEL_NAME = "ArcFace"


def extract_face(image_path: str, enforce_detection: bool = True):
    """
    Detects and extracts facial regions from an input image.

    Args:
        image_path (str): Path to the input image file.
        enforce_detection (bool): If True, raises an error when no face is detected.
                                  If False, returns the cropped center if face detection fails.

    Returns:
        list of dict: List containing extracted faces details:
                      - 'face': numpy array representing the detected facial RGB image.
                      - 'facial_area': dict with bounding box ('x', 'y', 'w', 'h').
                      - 'confidence': detection confidence score.
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Use DeepFace's extract_faces to detect facial area
    # opencv detector backend is fast and lightweight
    extracted = DeepFace.extract_faces(
        img_path=image_path,
        detector_backend="opencv",
        enforce_detection=enforce_detection
    )
    
    return extracted


def generate_embedding(image_path: str, enforce_detection: bool = True):
    """
    Generates a 512-dimensional face embedding vector using the ArcFace model.

    Args:
        image_path (str): Path to the input image file.
        enforce_detection (bool): Whether to enforce face detection before embedding calculation.

    Returns:
        list of float: Face embedding vector (512 numbers representing facial features).
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # DeepFace.represent generates feature vectors (embeddings)
    results = DeepFace.represent(
        img_path=image_path,
        model_name=MODEL_NAME,
        detector_backend="opencv",
        enforce_detection=enforce_detection
    )

    # results is a list of dictionaries (one per detected face)
    if results and len(results) > 0:
        embedding = results[0]["embedding"]
        return embedding
    else:
        raise ValueError(f"Could not generate embedding for image: {image_path}")


def verify_faces(img1_path: str, img2_path: str, enforce_detection: bool = True):
    """
    Verifies whether two face images match visually using ArcFace.

    Uses DeepFace.verify with the ArcFace model. DeepFace automatically
    calculates distance (cosine distance by default for ArcFace) and applies the
    official model threshold without hardcoding custom thresholds.

    Args:
        img1_path (str): Path to the first image file.
        img2_path (str): Path to the second image file.
        enforce_detection (bool): Whether face detection must pass for both images.

    Returns:
        dict: Verification result containing:
              - 'verified' (bool): True if faces match, False otherwise.
              - 'distance' (float): Calculated distance between embeddings.
              - 'threshold' (float): Model's decision threshold.
              - 'model' (str): Model name used ("ArcFace").
              - 'similarity_metric' (str): Distance metric used.
    """
    if not os.path.exists(img1_path):
        raise FileNotFoundError(f"Image file not found: {img1_path}")
    if not os.path.exists(img2_path):
        raise FileNotFoundError(f"Image file not found: {img2_path}")

    # DeepFace.verify returns a dictionary with 'verified', 'distance', 'threshold', etc.
    result = DeepFace.verify(
        img1_path=img1_path,
        img2_path=img2_path,
        model_name=MODEL_NAME,
        detector_backend="opencv",
        enforce_detection=enforce_detection
    )

    return {
        "verified": result.get("verified", False),
        "distance": result.get("distance", None),
        "threshold": result.get("threshold", None),
        "model": result.get("model", MODEL_NAME),
        "similarity_metric": result.get("similarity_metric", "cosine")
    }
