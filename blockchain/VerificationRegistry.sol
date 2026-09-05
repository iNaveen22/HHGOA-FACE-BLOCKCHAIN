// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title VerificationRegistry
 * @dev Stores SHA-256 verification fingerprints and source metadata on-chain.
 * Does NOT store raw image files or large payloads on-chain.
 */
contract VerificationRegistry {

    struct Record {
        bytes32 dataHash;
        string sourceUrl;
        uint256 timestamp;
        bool exists;
    }

    // Mapping from canonical SHA-256 hash (bytes32) to on-chain Record
    mapping(bytes32 => Record) public records;

    // Event emitted when a verification fingerprint is stored
    event RecordStored(
        bytes32 indexed dataHash,
        string sourceUrl,
        uint256 timestamp
    );

    /**
     * @dev Stores a new verification record on-chain.
     * @param dataHash SHA-256 fingerprint formatted as bytes32.
     * @param sourceUrl Source URL / domain of the verified candidate.
     */
    function storeRecord(bytes32 dataHash, string memory sourceUrl) public returns (bool) {
        require(dataHash != bytes32(0), "Data hash cannot be empty");
        
        records[dataHash] = Record({
            dataHash: dataHash,
            sourceUrl: sourceUrl,
            timestamp: block.timestamp,
            exists: true
        });

        emit RecordStored(dataHash, sourceUrl, block.timestamp);
        return true;
    }

    /**
     * @dev Checks whether a given fingerprint exists on-chain.
     * @param dataHash SHA-256 fingerprint formatted as bytes32.
     * @return bool True if record exists on-chain, False otherwise.
     */
    function verifyRecord(bytes32 dataHash) public view returns (bool) {
        return records[dataHash].exists;
    }

    /**
     * @dev Retrieves stored record details for a given fingerprint.
     * @param dataHash SHA-256 fingerprint formatted as bytes32.
     * @return dataHash The recorded SHA-256 hash.
     * @return sourceUrl The recorded source URL.
     * @return timestamp The block timestamp when the record was stored.
     */
    function getRecord(bytes32 dataHash) public view returns (bytes32, string memory, uint256) {
        require(records[dataHash].exists, "Record does not exist on-chain");
        Record memory rec = records[dataHash];
        return (rec.dataHash, rec.sourceUrl, rec.timestamp);
    }
}
