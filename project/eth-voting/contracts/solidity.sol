// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract Voting {
    struct Block {
        uint256 index;
        string timestamp;
        string trackingId;
        bytes32 previousHash;
        bytes32 blockHash;
    }

    mapping(uint256 => Block[]) public candidateChains;
    mapping(string => bool) public hasVoted;

    event BlockAdded(uint256 candidateId, uint256 index, string trackingId, bytes32 blockHash);
    event DebugTrackingID(string trackingId);  // ✅ Debug event instead of console.log

    constructor() {
        for (uint256 i = 1; i <= 3; i++) {
            candidateChains[i].push(Block(0, "GENESIS", "0", bytes32(0), bytes32(0)));
        }
    }

    function addBlock(uint256 candidateId, string memory timestamp, string memory trackingId) public {
        require(candidateId >= 1 && candidateId <= 3, "Invalid candidate ID");
        require(!hasVoted[trackingId], "Voter has already cast their vote!");

        Block[] storage chain = candidateChains[candidateId];
        uint256 index = chain.length;
        bytes32 previousHash = chain[chain.length - 1].blockHash;
        bytes32 blockHash = keccak256(abi.encodePacked(index, timestamp, trackingId, previousHash));

        chain.push(Block(index, timestamp, trackingId, previousHash, blockHash));
        hasVoted[trackingId] = true;

        emit BlockAdded(candidateId, index, trackingId, blockHash);
        emit DebugTrackingID(trackingId);  // ✅ Emit tracking ID for debugging
    }

    function getBlock(uint256 candidateId, uint256 index) public view returns (
        uint256 blockIndex,
        string memory blockTimestamp,
        string memory blockTrackingId,
        bytes32 blockPrevHash,
        bytes32 blockHash
    ) {
        require(index < candidateChains[candidateId].length, "Block does not exist");
        Block storage b = candidateChains[candidateId][index];
        return (b.index, b.timestamp, b.trackingId, b.previousHash, b.blockHash);
    }


    function getChainLength(uint256 candidateId) public view returns (uint256) {
        return candidateChains[candidateId].length;
    }

    function hasVoterVoted(string memory trackingId) public view returns (bool) {
        return hasVoted[trackingId];
    }
}
