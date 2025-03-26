import cv2
import face_recognition
import numpy as np
import firebase_admin
from firebase_admin import db
import hashlib
import json
import os

# Function to generate SHA256 hash
def generate_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode()).hexdigest()

def register_voter(voter_id, image_path, name, aadhaar_id, phone, passkey):
    try:
        # Check if voter already exists
        voter_ref = db.reference(f"Voters/{voter_id}").get()
        if voter_ref:
            return {"status": "error", "message": "Voter already registered"}

        # Load image and compute face encoding
        img = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image)

        if not encodings:
            return {"status": "error", "message": "No face detected"}

        # Store voter details in Registration Block
        registration_data = {
            "voter_id": voter_id,
            "name": name,
            "aadhaar_id": aadhaar_id,
            "phone": phone,
            "passkey": passkey,
            "face_encoding": encodings[0].tolist()
        }

        registration_hash = generate_hash(registration_data)

        # Create an empty Login Block
        login_block_data = {
            "voter_id": voter_id,
            "timestamps": [],
            "previous_hash": registration_hash  # Links to Registration Block
        }

        login_block_hash = generate_hash(login_block_data)

        # Store voter data in Firebase
        voter_data = {
            "registration_block": {
                "data": registration_data,
                "hash": registration_hash,
                "previous_hash": "0"  # First block
            },
            "voter_login_block": {
                "data": login_block_data,
                "hash": login_block_hash
            }
        }

        db.reference(f"Voters/{voter_id}").set(voter_data)

        return {
            "status": "success",
            "message": "Voter Registered Successfully",
            "registration_hash": registration_hash,
            "login_block_hash": login_block_hash
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
