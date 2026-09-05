# HH Goa 2026 Shortlisting Task 3 - Milestone 4: Blockchain Storage & Verification

This repository contains the complete implementation for **Milestone 4: Blockchain Fingerprint Storage & Verification**.

---

## 📌 Conceptual Architecture & Flow

```text
Local Input Image
       ↓
DeepFace + ArcFace Processing (Milestone 1)
       ↓
Google Lens Reverse Image Search via SerpApi (Milestone 2)
       ↓
Top Candidate Downloads & ArcFace Face Verification (Milestone 3)
       ↓
Canonical Verification Record Format (Milestone 4)
       ↓
SHA-256 Fingerprint Generation (Milestone 4)
       ↓
Smart Contract (`VerificationRegistry.sol`) on Local Blockchain (Milestone 4)
       ↓
Transaction Receipt (Tx Hash & Block Number)
       ↓
Later Tamper Verification (Recalculate SHA-256 vs On-Chain State) -> VALID / TAMPERED
```

---

## 📚 Key Concepts Explained (Beginner-Friendly)

### 1. Why use SHA-256?
SHA-256 (Secure Hash Algorithm 256-bit) converts any arbitrary input data into a fixed 64-character hexadecimal fingerprint (256 bits). It is **one-way** and **deterministic**: the exact same input data will *always* produce the exact same 64-character fingerprint. Changing even a single character or number produces a completely different fingerprint.

### 2. Why DON'T we store images on-chain?
Storing large binary files (like image files or large JSON blobs) directly on a blockchain is prohibitively expensive, slow, and bloats the blockchain ledger. Storing a 32-byte SHA-256 hash instead requires negligible gas and allows us to verify data integrity off-chain cleanly.

### 3. What does `bytes32` mean in Solidity?
In Solidity, `bytes32` represents a fixed-size array of 32 raw bytes (256 bits). It is the native data type used to store a 256-bit SHA-256 hash on Ethereum efficiently.

### 4. What is a Smart Contract?
A Smart Contract (`VerificationRegistry.sol`) is an executable program that runs deterministically on the blockchain ledger. Once deployed, its functions (`storeRecord`, `verifyRecord`) execute according to strict code logic.

### 5. What is an RPC Endpoint?
An RPC (Remote Procedure Call) endpoint (e.g. `http://127.0.0.1:8545`) is the HTTP network interface that allows Python applications (`web3.py`) to communicate with an Ethereum node.

### 6. What is a Blockchain Transaction & Transaction Hash?
A transaction is a signed request sent to the blockchain to alter state (e.g., executing `storeRecord`). The **Transaction Hash** (e.g., `0x52475674...`) is the unique cryptographic identifier of that executed transaction.

### 7. What the Blockchain Proves
- **Data Integrity & Non-Repudiation**: Proves that a specific verification record fingerprint was created and recorded at a specific block timestamp.
- **Tamper Detection**: Proves whether an off-chain verification record has been modified or altered after storage.

### 8. What the Blockchain DOES NOT Prove (Limitations)
- It does **NOT** prove that a social media post or profile is genuine or truthful.
- It does **NOT** guarantee that the source website is trustworthy.
- It does **NOT** imply that ArcFace face recognition is 100% infallible.
- It only proves that **the exact verification result fingerprint was recorded on-chain at block timestamp $T$**.

---

## 🛠️ How to Run Milestone 4

### 1. Start Local Blockchain Node (Ganache)
```bash
npx ganache --port 8545 --deterministic
```

### 2. Deploy Smart Contract (`VerificationRegistry.sol`)
```bash
.venv\Scripts\python.exe blockchain/deploy_local.py
```

### 3. Run Standalone Blockchain & Tamper Verification Demo
```bash
.venv\Scripts\python.exe blockchain/demo.py
```

### 4. Run Milestone 3 -> Milestone 4 Integration Test
```bash
.venv\Scripts\python.exe blockchain/integrate_m3.py
```

---

## 🧪 Verification & Tamper Test Summary

- **Contract Compilation**: Solidity `0.8.20` (`py-solc-x`)
- **Contract Address**: `0xe78A0F7E598Cc8b0Bb87894B0F60dD2a88d6a8Ab`
- **Original Record Fingerprint**: `ee850dc6dd9d4b9b1cc613ea54170470ebaa4e6aff194c02d88bffcc8cfeab09`
- **On-Chain Verification (Original)**: `TRUE (VALID / VERIFIED)`
- **Tampered Record (`face_distance: 0.5000`)**: `b4bf9cebc1042c5730507a6227c8ad228bbba40ed85981969c8a034a2a03948d`
- **On-Chain Verification (Tampered)**: `FALSE (TAMPER DETECTED)`
