import cv2
import face_recognition
import numpy as np
from firebase_admin import db
from datetime import datetime
import hashlib
import json

# Function to generate hash
def generate_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode()).hexdigest()

def login_voter(voter_id, image_path, passkey):
    try:
        # Fetch voter data from Firebase
        voter_data = db.reference(f"Voters/{voter_id}/registration_block/data").get()
        login_block = db.reference(f"Voters/{voter_id}/login_block").get()

        if not voter_data or not login_block:
            return {"status": "error", "message": "Voter not found"}

        # Verify Passkey
        if voter_data.get("passkey") != passkey:
            return {"status": "error", "message": "Incorrect passkey"}

        # Load image and compute face encoding
        img = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image)

        if not encodings:
            return {"status": "error", "message": "No face detected"}

        stored_encoding = np.array(voter_data["face_encoding"])
        match = face_recognition.compare_faces([stored_encoding], encodings[0],tolerance=0.45)[0]

        if not match:
            return {"status": "error", "message": "Face mismatch"}

        # Store login timestamp
        login_timestamp = datetime.now().isoformat()
        login_block["data"]["timestamps"].append(login_timestamp)

        # Generate new hash for login block
        updated_login_block_hash = generate_hash(login_block["data"])
        login_block["hash"] = updated_login_block_hash

        # Store updated login block in Firebase
        db.reference(f"Voters/{voter_id}/login_block").set(login_block)

        return {
            "status": "success",
            "message": "Login successful",
            "login_block_hash": updated_login_block_hash
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
