import requests
import os
import shutil
import firebase_admin
from firebase_admin import credentials, db
import pickle

# Constants
ENCODE_FILE = "EncodeFile.p"
IMAGES_DIR = "face_detection/images"

def reset_system():
    try:
        print("\n=== Starting System Reset ===")

        # 1. Clear Firebase data via Flask API
        print("Requesting server to clear Firebase data...")
        response = requests.post('http://127.0.0.1:5000/reset_system')
        
        if response.status_code == 200:
            print("✓ Firebase data cleared successfully")
        else:
            print(f"✗ Failed to clear Firebase data: {response.json().get('message', 'Unknown error')}")

        # 2. Delete EncodeFile.p
        print("Deleting EncodeFile.p...")
        if os.path.exists(ENCODE_FILE):
            os.remove(ENCODE_FILE)
            print("✓ EncodeFile.p deleted")
        else:
            print("✓ EncodeFile.p does not exist, skipping")

        # 3. Clear Images directory
        print("Resetting Images directory...")
        if os.path.exists(IMAGES_DIR):
            shutil.rmtree(IMAGES_DIR)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        print("✓ Images directory reset")

        # 4. Reset encodings
        print("Resetting encodings...")
        with open(ENCODE_FILE, 'wb') as file:
            pickle.dump([[], []], file)
        print("✓ Encodings reset and fresh EncodeFile.p created")

        print("\n=== System Reset Complete ===")

    except Exception as e:
        print(f"✗ Error during reset: {str(e)}")

if __name__ == "__main__":
    print("=== System Reset Tool ===")
    confirm = input("This will DELETE ALL voter data. Are you sure? (yes/no): ")
    if confirm.lower() == 'yes':
        reset_system()
    else:
        print("Reset cancelled.")
