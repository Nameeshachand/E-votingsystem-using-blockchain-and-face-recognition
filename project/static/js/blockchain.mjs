export class Block {
    constructor(index, timestamp, candidate,merkleRoot, previousHash = '') {
      this.index = index;
      this.timestamp = timestamp;
      this.data = {
        candidate: candidate,
      };
      this.merkleRoot= merkleRoot;
      this.previousHash = previousHash;
      this.hash = '';
    }
  
    async calculateHash() {
      const dataString = JSON.stringify({
        index: this.index,
        timestamp: this.timestamp,
        data: this.data,
        previousHash: this.previousHash,
      });
      const encoder = new TextEncoder();
      const dataBuffer = encoder.encode(dataString);
      const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
      return Array.from(new Uint8Array(hashBuffer))
        .map((byte) => byte.toString(16).padStart(2, '0'))
        .join('');
    }
  
    async setHash() {
      this.hash = await this.calculateHash();
    }
  
    calculateMerkleRoot() {
      const { voterId, candidate } = this.data;
      const input = `${voterId}${candidate}`;
      return CryptoJS.SHA256(input).toString();
  }
  
  async addBlock(newBlock) {
    newBlock.previousHash = this.getLatestBlock().hash;
    newBlock.merkleRoot= currentUser.merkleRoot;
        console.log(newBlock.previousHash);
        await newBlock.setHash();
        this.chain.push(newBlock);
        console.log("New block added:", newBlock); // Debug log
      
    } 
  
  }
  
  export class Blockchain {
    constructor() {
      this.chain = [this.createGenesisBlock()];
    }
  
    createGenesisBlock() {
      const genesisBlock = new Block(0, new Date().toISOString(), 'Genesis Block', '0');
      genesisBlock.hash = '0'; // Predefined hash for genesis block
      return genesisBlock;
    }
  
    getLatestBlock() {
      return this.chain[this.chain.length - 1];
    }
  
    async addBlock(newBlock) {
      newBlock.previousHash = this.getLatestBlock().hash;
      await newBlock.setHash();
      this.chain.push(newBlock);
    }
  
    async isChainValid() {
      for (let i = 1; i < this.chain.length; i++) {
        const currentBlock = this.chain[i];
        const previousBlock = this.chain[i - 1];
  
        if (currentBlock.hash !== (await currentBlock.calculateHash())) {
          return false;
        }
  
        if (currentBlock.previousHash !== previousBlock.hash) {
          return false;
        }
      }
      return true;
    }
  }
  