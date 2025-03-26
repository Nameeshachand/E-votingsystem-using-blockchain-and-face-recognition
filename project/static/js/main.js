// main.js

// 1) Initialize Web3 & your contract
// Import web3 using a bare module specifier.

console.log("Web3 version:", Web3.version);



const contractAddress = "0x9033Fbd71E9104aFFa714872c75f4130Ba1434f5";

const contractABI =   [
  {
    "inputs": [],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": false,
        "internalType": "uint256",
        "name": "candidateId",
        "type": "uint256"
      },
      {
        "indexed": false,
        "internalType": "uint256",
        "name": "index",
        "type": "uint256"
      },
      {
        "indexed": false,
        "internalType": "string",
        "name": "trackingId",
        "type": "string"
      },
      {
        "indexed": false,
        "internalType": "bytes32",
        "name": "blockHash",
        "type": "bytes32"
      }
    ],
    "name": "BlockAdded",
    "type": "event"
  },
  {
    "anonymous": false,
    "inputs": [
      {
        "indexed": false,
        "internalType": "string",
        "name": "trackingId",
        "type": "string"
      }
    ],
    "name": "DebugTrackingID",
    "type": "event"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "name": "candidateChains",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "index",
        "type": "uint256"
      },
      {
        "internalType": "string",
        "name": "timestamp",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "trackingId",
        "type": "string"
      },
      {
        "internalType": "bytes32",
        "name": "previousHash",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "blockHash",
        "type": "bytes32"
      }
    ],
    "stateMutability": "view",
    "type": "function",
    "constant": true
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "name": "hasVoted",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function",
    "constant": true
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "candidateId",
        "type": "uint256"
      },
      {
        "internalType": "string",
        "name": "timestamp",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "trackingId",
        "type": "string"
      }
    ],
    "name": "addBlock",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "candidateId",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "index",
        "type": "uint256"
      }
    ],
    "name": "getBlock",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "blockIndex",
        "type": "uint256"
      },
      {
        "internalType": "string",
        "name": "blockTimestamp",
        "type": "string"
      },
      {
        "internalType": "string",
        "name": "blockTrackingId",
        "type": "string"
      },
      {
        "internalType": "bytes32",
        "name": "blockPrevHash",
        "type": "bytes32"
      },
      {
        "internalType": "bytes32",
        "name": "blockHash",
        "type": "bytes32"
      }
    ],
    "stateMutability": "view",
    "type": "function",
    "constant": true
  },
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "candidateId",
        "type": "uint256"
      }
    ],
    "name": "getChainLength",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function",
    "constant": true
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "trackingId",
        "type": "string"
      }
    ],
    "name": "hasVoterVoted",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function",
    "constant": true
  }
]

let web3;
let contract;  // Declare contract globally

if (typeof window.ethereum !== 'undefined') {
    web3 = new Web3(window.ethereum);
    window.ethereum.request({ method: 'eth_requestAccounts' })
        .then(accounts => {
            console.log("✅ MetaMask Connected:", accounts);

            contract = new web3.eth.Contract(contractABI, contractAddress, { from: accounts[0] });
            console.log("✅ Smart Contract Loaded:", contract);
        })
        .catch(err => console.error("❌ User denied MetaMask access:", err));
} else {
    console.error("❌ MetaMask not found! Using fallback provider.");
    web3 = new Web3(new Web3.providers.HttpProvider("http://127.0.0.1:7545"));

    contract = new web3.eth.Contract(contractABI, contractAddress);
    console.log("✅ Smart Contract Loaded via Ganache:", contract);
}

  // Fetch Voter ID from Flask session
  async function fetchVoterId() {
    try {
        const response = await fetch('/api/get_voter_id');
        const data = await response.json();
        
        if (data.status === "success" && data.voter_id) {
            document.getElementById("voterIdInput").value = data.voter_id;
            console.log("✅ Voter ID Fetched:", data.voter_id);
        } else {
            console.warn("⚠️ No voter ID found in session.");
        }
    } catch (err) {
        console.error("❌ Error fetching voter ID:", err);
    }
}


// 3️⃣ Cast Vote Function (Multi-Chaining)
async function castVote() {
  const voteButton = document.getElementById('voteButton');
  voteButton.disabled = true;

  const candidateSelect = document.getElementById('candidateSelect');
  const selectedCandidate = candidateSelect.value;
  const voterId = document.getElementById("voterIdInput").value;

  if (!voterId) {
      alert("⚠️ Voter ID missing. Please log in again.");
      voteButton.disabled = false;
      return;
  }
  if (selectedCandidate === "select") {
      alert("⚠️ Please select a candidate.");
      voteButton.disabled = false;
      return;
  }

  try {
      // Fetch Tracking ID from Firebase
      const trackingIdResponse = await fetch(`/api/get_trackingID?voter_id=${voterId}`);
      const trackingData = await trackingIdResponse.json();
      
      if (trackingData.status !== "success") {
          alert("❌ Error fetching Tracking ID. Try again.");
          voteButton.disabled = false;
          return;
      }

      let trackingId = trackingData.tracking_id;

      // ✅ Log the received tracking ID for debugging
      console.log("📌 Tracking ID received from Firebase:", trackingId);

      // Display Tracking ID on the UI
      document.getElementById("trackingIdDisplay").innerText = `Tracking ID: ${trackingId}`;

      if (!trackingId || typeof trackingId !== "string") {
          alert("❌ Invalid Tracking ID received!");
          voteButton.disabled = false;
          return;
      }

      const timestamp = new Date().toISOString();
      let candidateId;

      switch (selectedCandidate) {
          case "Candidate 1": candidateId = 1; break;
          case "Candidate 2": candidateId = 2; break;
          case "Candidate 3": candidateId = 3; break;
          default:
              alert("Invalid candidate selected.");
              voteButton.disabled = false;
              return;
      }

      // **Check if voter has already voted**
      const hasVoted = await contract.methods.hasVoterVoted(trackingId).call();
      if (hasVoted) {
          alert("❌ You have already voted.");
          voteButton.disabled = false;
          return;
      }

      const accounts = await web3.eth.getAccounts();
      
      console.log("Sending transaction with:", { candidateId, timestamp, trackingId });

      await contract.methods.addBlock(
          candidateId,
          timestamp,
          trackingId
      ).send({ from: accounts[0] });

      alert("✅ Vote successfully cast!");
      candidateSelect.value = 'select';

      await updateResultSummary();

  } catch (error) {
      console.error('❌ Vote error:', error);
      alert('❌ Error casting vote. Please try again.');
  } finally {
      voteButton.disabled = false;

  }
}


async function updateResultSummary() {
  console.log("....updating result summary....")
  try {
      const c1Length = await contract.methods.getChainLength(1).call();
      const c2Length = await contract.methods.getChainLength(2).call();
      const c3Length = await contract.methods.getChainLength(3).call();
      
      console.log("Candidate 1 Votes:", c1Length);
      console.log("Candidate 2 Votes:", c2Length);
      console.log("Candidate 3 Votes:", c3Length);
      
      document.getElementById("candidate1Votes").innerText = c1Length - 1; 
      document.getElementById("candidate2Votes").innerText = c2Length - 1; 
      document.getElementById("candidate3Votes").innerText = c3Length - 1; 
  } catch (err) {
      console.error("❌ Error updating vote summary:", err);
  }
}



// 5️⃣ View Blockchain Function
async function viewBlockchain() {
  console.log("🔍 Viewing blockchain...");
  
  const container = document.getElementById('blockchainContainer');
  container.innerHTML = ''; // Clear previous content

  for (let candidateId = 1; candidateId <= 3; candidateId++) {
      try {
          const chainLength = await contract.methods.getChainLength(candidateId).call();
          const candidateName = (candidateId === 1) ? "Candidate 1" :
                                (candidateId === 2) ? "Candidate 2" : "Candidate 3";
          let html = `<h3>${candidateName}'s Blockchain</h3>`;

          for (let i = 0; i < chainLength; i++) {
              const block = await contract.methods.getBlock(candidateId, i).call();
              const blockData = {
                  Index: block[0],
                  Timestamp: block[1],
                  TrackingID: block[2],
                  PreviousHash: block[3],
                  Hash: block[4]
              };
              html += `<pre>${JSON.stringify(blockData, null, 2)}</pre>`;
          }
          container.innerHTML += html;

      } catch (error) {
          console.error(`❌ Error fetching chain for Candidate ${candidateId}:`, error);
      }
  }
}

// 8️⃣ Initialize Event Listeners on Page Load
document.addEventListener('DOMContentLoaded', async () => {
  console.log("📌 Page Loaded. Initializing system...");

  await fetchVoterId();

  document.getElementById('voteButton').addEventListener('click', castVote);
  document.getElementById('viewChainButton').addEventListener('click', viewBlockchain);
  document.getElementById('clearVotingChainsButton').addEventListener('click', clearVotingChains);
  document.getElementById('backButton').addEventListener('click', () => {
      window.location.href = 'http://127.0.0.1:5000/';
  });

  // ✅ Auto-update vote table on page load
  await updateResultSummary();
});


// Run update function on page load