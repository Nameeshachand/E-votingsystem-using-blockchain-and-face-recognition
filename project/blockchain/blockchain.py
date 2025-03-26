import hashlib
import json
import time

class Block:
    def __init__(self, index, previous_hash, timestamp, voter_data, merkle_root, hash):
        self.index = index
        self.previous_hash = previous_hash
        self.timestamp = timestamp
        self.voter_data = voter_data  # Stores Aadhaar, Phone, Name, Voter ID, Face Encoding Hash
        self.merkle_root = merkle_root
        self.hash = hash

    def to_dict(self):
        return {
            "index": self.index,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "voter_data": self.voter_data,
            "merkle_root": self.merkle_root,
            "hash": self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, "0", int(time.time()), "Genesis Block", "0", self.hash_block("Genesis Block"))
        self.chain.append(genesis_block)

    def hash_block(self, block_data):
        return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()

    def calculate_merkle_root(self, data_list):
        if len(data_list) == 0:
            return ""
        if len(data_list) == 1:
            return data_list[0]

        new_level = []
        for i in range(0, len(data_list), 2):
            left = data_list[i]
            right = data_list[i + 1] if i + 1 < len(data_list) else left
            combined_hash = self.hash_block(left + right)
            new_level.append(combined_hash)
        return self.calculate_merkle_root(new_level)

    def add_block(self, voter_data):
        previous_block = self.chain[-1]
        index = len(self.chain)
        timestamp = int(time.time())
        data_hashes = [self.hash_block(str(value)) for value in voter_data.values()]
        merkle_root = self.calculate_merkle_root(data_hashes)
        block_hash = self.hash_block(f"{index}{previous_block.hash}{timestamp}{merkle_root}")

        new_block = Block(index, previous_block.hash, timestamp, voter_data, merkle_root, block_hash)
        self.chain.append(new_block)
        return new_block

    def verify_chain(self):
        for i in range(1, len(self.chain)):
            previous_block = self.chain[i - 1]
            current_block = self.chain[i]
            if current_block.previous_hash != previous_block.hash:
                return False
            if current_block.hash != self.hash_block(f"{current_block.index}{current_block.previous_hash}{current_block.timestamp}{current_block.merkle_root}"):
                return False
        return True

    def get_chain(self):
        return [block.to_dict() for block in self.chain]
