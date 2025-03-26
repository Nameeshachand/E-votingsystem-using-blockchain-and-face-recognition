import requests
import firebase_admin
from firebase_admin import credentials, db

# Firebase Configuration
FIREBASE_CREDENTIALS = "serviceAccountKey.json"
FIREBASE_URL = "https://face-detection-4e986-default-rtdb.asia-southeast1.firebasedatabase.app/"

def reset_voting_data():
    try:
        print("\n=== Starting Voting Data Reset ===")

        # 1️⃣ Clear Firebase Candidate Blockchains & Used Voters via Flask API
        print("Requesting server to clear Blockchain & Used Voters data...")
        response = requests.post('http://127.0.0.1:5000/reset_blockchains')

        if response.status_code == 200:
            print("✓ Blockchain & Used Voter data cleared successfully")
        else:
            print(f"✗ Failed to clear voting data: {response.json().get('message', 'Unknown error')}")

        print("\n=== Voting Data Reset Complete ===")

    except Exception as e:
        print(f"✗ Error during reset: {str(e)}")

if __name__ == "__main__":
    print("=== Voting Blockchain Reset Tool ===")
    confirm = input("This will DELETE ALL voting blockchain data and used voter IDs. Are you sure? (yes/no): ")
    
    if confirm.lower() == 'yes':
        reset_voting_data()
    else:
        print("Reset cancelled.")
