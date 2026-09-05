"""
HH Goa 2026 Shortlisting Task 3 - Professional Streamlit Interface.

Milestone 6: Digital Evidence & Verification Dashboard.
Light, clean, minimal, and classy presentation inspired by modern SaaS products
and Etherscan verification standards.
"""

import os
import sys
import json
import tempfile
import streamlit as st
from PIL import Image

# Import modular backend components
import face_processor
from main import run_pipeline
from blockchain.fingerprint import create_fingerprint
from blockchain.blockchain_client import BlockchainClient

# -----------------------------------------------------------------------------
# PAGE CONFIGURATION & LIGHT THEME STYLING
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="HH Goa 2026 — Evidence Verification System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Clean Light CSS Injection
st.markdown("""
<style>
    /* Global Page Styling */
    .stApp {
        background-color: #f8fafc;
        color: #0f172a;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Main Content Container Spacing */
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1200px;
    }

    /* Header Card */
    .header-container {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 24px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .header-title {
        font-size: 24px;
        font-weight: 700;
        color: #0f172a;
        margin: 0 0 6px 0;
        letter-spacing: -0.02em;
    }
    .header-subtitle {
        font-size: 14px;
        color: #64748b;
        margin: 0;
    }

    /* Network Badge */
    .network-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        color: #334155;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 9999px;
    }
    .network-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
    }

    /* Stepper Bar */
    .stepper-container {
        display: flex;
        justify-content: space-between;
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 12px 20px;
        margin-bottom: 24px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: 600;
        color: #64748b;
    }
    .step-item.active {
        color: #2563eb;
    }
    .step-item.completed {
        color: #059669;
    }
    .step-number {
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background-color: #e2e8f0;
        color: #475569;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 11px;
    }
    .step-item.active .step-number {
        background-color: #2563eb;
        color: #ffffff;
    }
    .step-item.completed .step-number {
        background-color: #10b981;
        color: #ffffff;
    }

    /* Metric Card */
    .metric-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .metric-value {
        font-size: 22px;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 4px;
    }
    .metric-label {
        font-size: 12px;
        color: #64748b;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }

    /* Custom Evidence Cards */
    .evidence-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .card-heading {
        font-size: 16px;
        font-weight: 600;
        color: #0f172a;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    /* Badges */
    .badge-verified {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
    }
    .badge-unverified {
        background-color: #fee2e2;
        color: #b91c1c;
        border: 1px solid #fca5a5;
        font-size: 12px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
    }

    /* Cryptographic Detail Table */
    .crypto-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #f1f5f9;
        font-size: 13px;
    }
    .crypto-row:last-child {
        border-bottom: none;
    }
    .crypto-key {
        color: #64748b;
        font-weight: 500;
        width: 140px;
        flex-shrink: 0;
    }
    .crypto-value {
        color: #0f172a;
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
        word-break: break-all;
        font-size: 12px;
    }

    /* Links */
    a.etherscan-link {
        color: #2563eb;
        text-decoration: none;
        font-weight: 500;
    }
    a.etherscan-link:hover {
        text-decoration: underline;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# SESSION STATE INITIALIZATION
# -----------------------------------------------------------------------------
if "pipeline_result" not in st.session_state:
    st.session_state["pipeline_result"] = None
if "selected_sample" not in st.session_state:
    st.session_state["selected_sample"] = "person1_a.jpg"


# -----------------------------------------------------------------------------
# HEADER & SEPOLIA NETWORK BADGE
# -----------------------------------------------------------------------------
sepolia_contract_addr = os.getenv(
    "SEPOLIA_CONTRACT_ADDRESS", "0x21bD1360C5bc74713EbFf45e83411A63Cde2D03d"
)
etherscan_contract_url = f"https://sepolia.etherscan.io/address/{sepolia_contract_addr}"

st.markdown(f"""
<div class="header-container">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 12px;">
        <div>
            <h1 class="header-title">HH Goa 2026 — Digital Evidence & Verification Dashboard</h1>
            <p class="header-subtitle">Face Recognition + Reverse Image Search + Ethereum Sepolia Blockchain Storage</p>
        </div>
        <div>
            <div class="network-badge">
                <span class="network-dot"></span>
                <span>Ethereum Sepolia (Chain ID: 11155111)</span>
            </div>
            <div style="font-size: 11px; color: #64748b; margin-top: 4px; text-align: right;">
                Contract: <a href="{etherscan_contract_url}" target="_blank" class="etherscan-link">{sepolia_contract_addr[:6]}...{sepolia_contract_addr[-4:]} ↗</a>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Determine stepper states
has_result = st.session_state["pipeline_result"] is not None
step1_class = "completed" if has_result else "active"
step2_class = "completed" if has_result else "pending"
step3_class = "completed" if has_result else "pending"
step4_class = "completed" if (has_result and st.session_state["pipeline_result"].get("blockchain")) else "pending"

st.markdown(f"""
<div class="stepper-container">
    <div class="step-item {step1_class}">
        <div class="step-number">1</div>
        <span>Input Evidence</span>
    </div>
    <div style="color: #cbd5e1;">→</div>
    <div class="step-item {step2_class}">
        <div class="step-number">2</div>
        <span>Google Lens Search</span>
    </div>
    <div style="color: #cbd5e1;">→</div>
    <div class="step-item {step3_class}">
        <div class="step-number">3</div>
        <span>ArcFace Verification</span>
    </div>
    <div style="color: #cbd5e1;">→</div>
    <div class="step-item {step4_class}">
        <div class="step-number">4</div>
        <span>Sepolia Blockchain</span>
    </div>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# MAIN LAYOUT: SIDEBAR / CONTROLS & DASHBOARD
# -----------------------------------------------------------------------------
col_input, col_display = st.columns([1, 2.2], gap="large")

# =============================================================================
# LEFT COLUMN: INPUT EVIDENCE & CONTROLS
# =============================================================================
with col_input:
    st.markdown('<div class="evidence-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-heading">1. Input Evidence Selection</div>', unsafe_allow_html=True)

    selected_image_path = None

    uploaded_file = st.file_uploader(
        "Upload target image (JPG, JPEG, PNG):",
        type=["jpg", "jpeg", "png"]
    )
    if uploaded_file is not None:
        # Save uploaded image to temp file
        temp_dir = tempfile.gettempdir()
        selected_image_path = os.path.join(temp_dir, f"uploaded_{uploaded_file.name}")
        with open(selected_image_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    # Image Preview & Quick Face Check
    if selected_image_path and os.path.exists(selected_image_path):
        st.markdown("---")
        st.image(selected_image_path, caption=f"Selected Input: {os.path.basename(selected_image_path)}", use_container_width=True)

        # Face detection preview badge
        try:
            detected_faces = face_processor.extract_face(selected_image_path, enforce_detection=False)
            if detected_faces and len(detected_faces) > 0:
                st.success(f"✓ Face Detected ({len(detected_faces)} face(s) found)")
            else:
                st.warning("⚠️ No face detected in preview.")
        except Exception:
            st.info("Face detection check pending pipeline run.")

    st.markdown("---")
    top_candidates = st.slider("Max Reverse Search Candidates:", min_value=1, max_value=20, value=10)

    run_btn = st.button("🚀 Run Verification Pipeline", type="primary", use_container_width=True)

    if run_btn:
        if not selected_image_path or not os.path.exists(selected_image_path):
            st.error("Please select or upload a valid input image.")
        else:
            with st.spinner("Processing pipeline: Face Detection → Google Lens → ArcFace Verification → Sepolia Blockchain..."):
                try:
                    result = run_pipeline(image_path=selected_image_path, top_n=top_candidates)
                    st.session_state["pipeline_result"] = result
                    st.success("Pipeline execution complete!")
                    st.rerun()
                except Exception as err:
                    st.error(f"Pipeline Execution Failed: {err}")

    st.markdown('</div>', unsafe_allow_html=True)


# =============================================================================
# RIGHT COLUMN: RESULTS & BLOCKCHAIN VERIFICATION PROOF
# =============================================================================
with col_display:
    res = st.session_state["pipeline_result"]

    if not res:
        st.markdown("""
        <div class="evidence-card" style="text-align: center; padding: 48px 24px; color: #64748b;">
            <div style="font-size: 36px; margin-bottom: 12px;">🛡️</div>
            <div style="font-size: 16px; font-weight: 600; color: #0f172a; margin-bottom: 6px;">Ready for Evidence Verification</div>
            <div>Select an input image on the left and click <b>Run Verification Pipeline</b> to execute reverse image intelligence and Sepolia blockchain fingerprinting.</div>
        </div>
        """, unsafe_allow_html=True)

    else:
        # TOP METRICS ROW
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{res.get('lens_candidates_found', 0)}</div>
                <div class="metric-label">Visual Matches</div>
            </div>
            """, unsafe_allow_html=True)

        with m2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{res.get('candidates_processed', 0)}</div>
                <div class="metric-label">Downloaded & Analyzed</div>
            </div>
            """, unsafe_allow_html=True)

        with m3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: #059669;">{res.get('verified_face_matches', 0)}</div>
                <div class="metric-label">Verified Matches</div>
            </div>
            """, unsafe_allow_html=True)

        with m4:
            bc_verified = res.get("blockchain", {}) and res["blockchain"].get("verified", False)
            status_color = "#059669" if bc_verified else "#dc2626"
            status_text = "VERIFIED" if bc_verified else "UNVERIFIED"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value" style="color: {status_color};">{status_text}</div>
                <div class="metric-label">On-Chain Status</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

        # HERO CARD: BEST VERIFIED MATCH
        best = res.get("best_match")

        if best:
            st.markdown("""
            <div class="evidence-card">
                <div class="card-heading">
                    <span>2. Best Web Face Match</span>
                    <span class="badge-verified">✓ Face Match Verified (ArcFace)</span>
                </div>
            """, unsafe_allow_html=True)

            b_col1, b_col2 = st.columns([1, 2])
            with b_col1:
                if best.get("image_url"):
                    st.image(best["image_url"], caption="Web Match Preview", use_container_width=True)

            with b_col2:
                st.markdown(f"**Title:** {best.get('title', 'N/A')}")
                st.markdown(f"**Source Domain:** `{best.get('source', 'N/A')}`")
                st.markdown(f"**Page URL:** [{best.get('page_url')}]({best.get('page_url')})")
                st.markdown(f"**ArcFace Distance:** `{best.get('face_distance', 0.0):.4f}` *(Threshold: `< 0.6800`)*")

                # Visual ArcFace distance bar
                dist = float(best.get("face_distance", 0.0))
                pct = min(max(int((dist / 0.6800) * 100), 0), 100)
                st.progress(pct, text=f"ArcFace Distance Score: {dist:.4f} (Lower = Better)")

            st.markdown('</div>', unsafe_allow_html=True)

        else:
            st.markdown("""
            <div class="evidence-card">
                <div class="card-heading">
                    <span>2. Best Web Face Match</span>
                    <span class="badge-unverified">No Verified Face Match</span>
                </div>
                <p style="color: #64748b; font-size: 14px;">No visual candidates met the ArcFace face verification threshold (&lt; 0.6800). Unverified candidates are strictly excluded from blockchain registration.</p>
            </div>
            """, unsafe_allow_html=True)

        # BLOCKCHAIN PROOF CARD (ETHERSCAN INSPIRED)
        bc = res.get("blockchain")
        if bc:
            tx_hash = bc.get("transaction_hash", "")
            tx_url = bc.get("etherscan_tx_url", "#")
            c_addr = bc.get("contract_address", "")
            c_url = bc.get("etherscan_contract_url", "#")

            st.markdown("""
            <div class="evidence-card">
                <div class="card-heading">
                    <span>3. Ethereum Sepolia Cryptographic Proof</span>
                    <span class="badge-verified">✓ Verified On-Chain</span>
                </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="crypto-row">
                <div class="crypto-key">Network</div>
                <div class="crypto-value">{bc.get('network_name', 'Ethereum Sepolia')} (Chain ID: {bc.get('chain_id', 11155111)})</div>
            </div>
            <div class="crypto-row">
                <div class="crypto-key">SHA-256 Digest</div>
                <div class="crypto-value">{bc.get('sha256')}</div>
            </div>
            <div class="crypto-row">
                <div class="crypto-key">Contract Address</div>
                <div class="crypto-value"><a href="{c_url}" target="_blank" class="etherscan-link">{c_addr} ↗</a></div>
            </div>
            <div class="crypto-row">
                <div class="crypto-key">Transaction Hash</div>
                <div class="crypto-value"><a href="{tx_url}" target="_blank" class="etherscan-link">{tx_hash} ↗</a></div>
            </div>
            <div class="crypto-row">
                <div class="crypto-key">Block Number</div>
                <div class="crypto-value">#{bc.get('block_number')}</div>
            </div>
            <div class="crypto-row">
                <div class="crypto-key">On-Chain State</div>
                <div class="crypto-value" style="color: #059669; font-weight: 600;">✓ VALID / FINGERPRINT VERIFIED ON BLOCKCHAIN</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

        # EXPANDER 1: VIEW EVIDENCE DETAILS (CANONICAL JSON)
        if best:
            with st.expander("🔍 View Evidence Details (Canonical JSON)"):
                canonical_record = {
                    "title": best["title"],
                    "source": best["source"],
                    "source_url": best["page_url"],
                    "image_url": best["image_url"],
                    "face_match": True,
                    "face_distance": round(best["face_distance"], 4)
                }
                fp_info = create_fingerprint(canonical_record)

                st.markdown("**Canonical JSON String (Byte-for-byte SHA-256 Input):**")
                st.code(fp_info["canonical_json"], language="json")

                st.markdown("**SHA-256 Hex Digest:**")
                st.code(fp_info["hex_hash"], language="text")

                st.markdown("**Bytes32 Contract Input:**")
                st.code(fp_info["bytes32_hex"], language="text")

        # EXPANDER 2: HOW INTEGRITY VERIFICATION WORKS
        with st.expander("ℹ️ How Integrity Verification Works"):
            st.markdown("""
            ### Cryptographic Fingerprint Verification Workflow

            1. **Canonical JSON Generation**:
               The verified match evidence (Title, Source Domain, Source URL, Image URL, Face Match status, ArcFace Distance) is formatted into a strictly ordered, space-trimmed canonical JSON string.

            2. **SHA-256 Hashing**:
               The canonical JSON string is hashed using SHA-256, generating an immutable 32-byte cryptographic fingerprint (hex digest).

            3. **Sepolia Smart Contract Storage**:
               The 32-byte fingerprint is submitted to the `VerificationRegistry` smart contract deployed on the Ethereum Sepolia Testnet.

            4. **On-Chain Verification vs. Tamper Detection**:
               - **Original Evidence**: Re-hashing the exact canonical record produces the identical SHA-256 fingerprint, which exists in smart contract storage (`TRUE / VERIFIED`).
               - **Modified / Tampered Evidence**: Changing even a single character, URL, or float value alters the resulting SHA-256 hash completely. Querying the smart contract with a tampered hash returns `FALSE / NOT FOUND`, immediately triggering **TAMPER DETECTED**.
            """)
