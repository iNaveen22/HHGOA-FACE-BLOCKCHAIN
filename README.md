# HH Goa 2026 Shortlisting Task 3 - Face Processing, Reverse Search & Blockchain Verification Pipeline

This repository contains the complete, integrated implementation for **HH Goa 2026 Shortlisting Task 3** (Milestones 1 through 5).

---

## 📌 Project Architecture

```text
Local Input Image
       ↓
[Milestone 1] DeepFace + ArcFace Face Detection & Feature Extraction
       ↓
[Milestone 2] Real Google Lens Reverse Image Search via SerpApi
       ↓
[Milestone 3] Top Candidate Image Download & ArcFace Face Verification
       ↓
[Milestone 3] Select Best VERIFIED Candidate Match (Lowest ArcFace Distance)
       ↓
[Milestone 4] Format Canonical Verification Record (json.dumps sort_keys=True)
       ↓
[Milestone 4] Calculate Deterministic SHA-256 Fingerprint
       ↓
[Milestone 4] Submit Fingerprint Transaction to Smart Contract (`VerificationRegistry.sol`)
       ↓
[Milestone 4] On-Chain Fingerprint Re-Verification (`verifyRecord` -> TRUE)
       ↓
[Milestone 5] Final Structured Output (`final_result.json`) & Terminal CLI Summary
```

---

## 🚀 Key Features by Milestone

### 🔹 Milestone 1: Face Processing
- Uses `DeepFace` with the **ArcFace** model (512-D embedding vector).
- Detects bounding boxes and extracts faces using OpenCV detector backend.
- Performs face verification using DeepFace's built-in threshold mechanism without hardcoding custom thresholds.

### 🔹 Milestone 2: Genuine Reverse Image Search
- Uploads local image to SerpApi's `/image` endpoint to obtain a temporary `image_id`.
- Queries SerpApi's `google_lens` engine to retrieve live candidate web results.
- Extracts structured metadata: `position`, `title`, `source` domain, `page_url`, `image_url`, `thumbnail_url`, `image_width`, and `image_height`.

### 🔹 Milestone 3: Candidate Image Face Verification
- Downloads candidate images from primary `image_url` (with fallback to `thumbnail_url`).
- Handles network errors, timeouts, invalid images, and face-less candidates.
- Evaluates candidate faces against the original input face using ArcFace.
- Ranks candidate results so verified matches appear first (sorted by closest ArcFace distance).

### 🔹 Milestone 4: Blockchain Fingerprint Storage & Verification
- Creates canonical JSON records (`json.dumps(..., sort_keys=True, separators=(',', ':'))`).
- Computes SHA-256 hex digest and converts to `bytes32`.
- Deploys Solidity smart contract (`VerificationRegistry.sol`, version `0.8.20`) to local Ethereum blockchain (Ganache).
- Stores fingerprints on-chain with block timestamp.
- Verifies fingerprint existence on-chain and detects data modifications (Tamper Test).

### 🔹 Milestone 5: Integrated End-to-End Pipeline
- Connects Milestones 1–4 into a single CLI entry point (`main.py`).
- Enforces strict input validation and safeguard checks (does not store unverified candidates on-chain).
- Saves full structured output to `final_result.json`.

---

## 📥 Installation & Setup

### 1. Prerequisites
- Python 3.11
- Node.js & `npx` (for running Ganache local blockchain)

### 2. Environment Variables Setup
Copy `.env.example` to `.env` and add your SerpApi API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
SERPAPI_KEY=your_serpapi_api_key_here
BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545
BLOCKCHAIN_PRIVATE_KEY=
```

### 3. Install Python Dependencies
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 🏃 How to Run the Pipeline

### Step 1: Start Local Ganache Blockchain Server
In a separate terminal, start Ganache on port 8545:
```bash
npx ganache --port 8545 --deterministic
```

### Step 2: Deploy Smart Contract (`VerificationRegistry.sol`)
```bash
.venv\Scripts\python.exe blockchain/deploy_local.py
```

### Step 3: Run Main End-to-End Pipeline
```bash
.venv\Scripts\python.exe main.py --image test_images/person1_a.jpg --top 10
```

---

## 📊 Example CLI Terminal Output

```text
============================================================
  HH GOA 2026 - FACE VERIFICATION & BLOCKCHAIN PIPELINE   
============================================================

[*] STEP 1: Validating input image and detecting faces...
    - Input Image: test_images/person1_a.jpg
    [+] Face Detection: SUCCESS (1 face(s) detected)

[*] STEP 2: Executing Google Lens reverse image search (SerpApi)...
    [+] Google Lens Search: CONNECTED
    [+] Visual Matches Returned: 59

[*] STEP 3: Downloading top 10 candidates & running ArcFace verification...
    [+] VERIFIED BEST MATCH FOUND:
        - Title         : Zoid Kirsch on X: "The story of how I came to own a copy of ...
        - Source Domain : x.com
        - Page URL      : https://x.com/ZoidCTF/status/1414325266298540040
        - Image URL     : https://pbs.twimg.com/media/E6Cv6PCVIAM41zp.png
        - ArcFace Dist  : 0.0167 (Threshold: 0.6800)
        - Match Status  : ✓ FACE MATCH VERIFIED

[*] STEP 5: Generating canonical record & SHA-256 fingerprint...
    - Canonical Record : {"face_distance":0.0167,"face_match":true,"image_url":"https://pbs.twimg.com/media/E6Cv6PCVIAM41zp.png","source":"x.com","source_url":"https://x.com/ZoidCTF/status/1414325266298540040","title":"Zoid Kirsch on X: \"The story of how I came to own a copy of ..."}
    - SHA-256 Fingerprint : 7626db547c58e641fa20479c5e2c8a27127ec88b464a5e7b87dd119425038d2c

[*] STEP 6: Connecting to local blockchain & recording fingerprint...
    [+] Blockchain: CONNECTED (http://127.0.0.1:8545)
    [+] Contract Address: 0xe78A0F7E598Cc8b0Bb87894B0F60dD2a88d6a8Ab
    [+] Transaction Hash : 531f54f5fca737d44c400296eddb8b1b48263652b0cdb157ff1c549b960fe0bb
    [+] Block Number     : 5
    [+] On-Chain Verification Status: True
    [+] FINGERPRINT VERIFIED ON BLOCKCHAIN

============================================================
FINAL RESULT
============================================================
FACE MATCH:
✓ VERIFIED

BLOCKCHAIN RECORD:
✓ VERIFIED ON-CHAIN
============================================================
```

---

## ⚠️ Important Limitations & Disclaimer

> [!IMPORTANT]
> - **Blockchain Scope**: The blockchain stores a 32-byte SHA-256 fingerprint of the verification evidence. It proves **data integrity and time of recording on-chain**.
> - **Authenticity Disclaimer**: Recording a fingerprint on-chain does **NOT** prove that a web page or social media post is authentic, nor does it independently verify the real-world identity of a person.
> - **Model Wording**: Matching candidates are reported strictly as `FACE MATCH VERIFIED` under the ArcFace model configuration, rather than claiming definitive identity resolution.
> - **Benchmark Image Note**: Standard benchmark images (such as Lena) are used for technical pipeline validation.

---

## 🔒 Security Notes
- Real API keys and private keys must **never** be committed to version control.
- `.gitignore` is configured to exclude `.env`, `.venv/`, `candidate_downloads/`, `__pycache__/`, and temporary output files.
