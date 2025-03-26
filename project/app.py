from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import cv2
import face_recognition
import numpy as np
import firebase_admin
from firebase_admin import credentials, db
import hashlib
import json
import os
from flask import send_from_directory
from datetime import datetime
import shutil
import pickle
import string
import time
import csv
import os

LOG_FILE = "performance_data.csv"

if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["voter_id", "action", "latency", "timestamp"])

def log_metrics(voter_id, action, start_time):
    """
    Logs performance metrics (time taken for operations) into a CSV file.
    """
    end_time = time.time()
    latency = end_time - start_time  # Calculate processing time
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")  # Format timestamp
    
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([voter_id, action, latency, timestamp])
        
    print("Writing metrics to:", os.path.abspath(LOG_FILE))
    print(f"✅ Logged: {action} took {latency:.4f} seconds")


#initialize Flask 
app = Flask(__name__, static_folder="static", template_folder="templates")

app.secret_key = "supersecretkey"
CORS(app)

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    "databaseURL": "https://face-detection-4e986-default-rtdb.asia-southeast1.firebasedatabase.app/"
})

# Function to generate Merkle Root Hash

# Directory for Storing Images
IMAGES_DIR = "Images"
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

ENCODE_FILE = "EncodeFile.p"

# Initialize empty lists if file doesn't exist
encodeListKnown = []
voterIds = []

def generate_merkle_root(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode()).hexdigest()

# Home Page
@app.route("/")
def home():
    return render_template("home.html")

# Registration Page
@app.route("/register")
def register():
    return render_template("register.html")

# Login Page
@app.route("/login")
def login():
    return render_template("login.html")

# Voting Dashboard (Only accessible if logged in)

@app.route("/static/js/<path:filename>")
def serve_js(filename):
    return send_from_directory("static/js", filename, mimetype="application/javascript")

@app.route("/api/get_voter_id", methods=["GET"])
def get_voter_id():
    if "voter_id" in session:
        return jsonify({"status": "success", "voter_id": session["voter_id"]})
    else:
        return jsonify({"status": "error", "message": "Voter ID not found in session"}), 404

@app.route("/index")
def index():
    if 'voter_id' not in session:
        return redirect(url_for('login'))
    return render_template("index.html", voter_id=session['voter_id'])


# Function to generate hash for both blocks
def generate_hash(data):
    json_data = json.dumps(data, sort_keys=True)
    return hashlib.sha256(json_data.encode()).hexdigest()
    
    
# We'll keep a global in-memory set to track collisions across this server's lifetime.
# In production, store used IDs in Firebase or another persistent DB.
collision_db = set()

def quantize_face_embedding(face_encoding_floats):
    """
    Convert face embedding (e.g., 128 floats) into 128 bits by a simple sign-bit approach.
    For each float, 1 bit = (val >= 0 ? 1 : 0).
    Returns 16 bytes (128 bits) as a bytes object.
    """
    bits = 0
    for val in face_encoding_floats:
        bit = 1 if val >= 0 else 0
        bits = (bits << 1) | bit
    
    # Convert to 16 bytes big-endian
    return bits.to_bytes(16, byteorder='big')

def base62_encode(num, length=10):
    """
    Converts a number to a Base62 alphanumeric representation (0-9, A-Z, a-z).
    Ensures a fixed length output.
    """
    characters = string.digits + string.ascii_uppercase + string.ascii_lowercase  # 62 characters
    base = len(characters)
    encoded = []

    for _ in range(length):
        encoded.append(characters[num % base])
        num //= base

    return ''.join(encoded[::-1])

def generate_short_id(leaf_hash_hex, face_encoding_floats):
    """
    Generate a 10-character alphanumeric unique tracking ID by:
    1) Hashing voter details (Merkle root).
    2) Quantizing the face encoding.
    3) Checking Firebase for collision.
    4) Ensuring a unique tracking ID is stored in Firebase.
    """

    # Convert the 64-hex-char Merkle root hash into a 256-bit integer
    leaf_int_256 = int(leaf_hash_hex, 16)  
    leaf_hash_128 = leaf_int_256 & ((1 << 128) - 1)  # Truncate to 128 bits

    # Convert face encoding into 128-bit representation
    face_bits_128 = quantize_face_embedding(face_encoding_floats)
    face_int_128 = int.from_bytes(face_bits_128, 'big')

    # XOR the two 128-bit values
    combined_128 = leaf_hash_128 ^ face_int_128

    # Convert the result to an alphanumeric ID using Base62 encoding
    alphanumeric_id = base62_encode(combined_128 % (62**10), 10)

    # 🔥 Step 1: Check Firebase for collisions
    used_ids_ref = db.reference("UsedTrackingIDs").get() or {}

    if alphanumeric_id in used_ids_ref:
        attempt = 1
        new_id = alphanumeric_id
        while new_id in used_ids_ref and attempt < 10000:  # Avoid infinite loops
            toggled = combined_128 ^ attempt  # Slight modification to resolve collisions
            new_id = base62_encode(toggled % (62**10), 10)
            attempt += 1
        alphanumeric_id = new_id

    # 🔥 Step 2: Store new unique tracking ID in Firebase
    db.reference(f"UsedTrackingIDs/{alphanumeric_id}").set({"status": "used"})

    return alphanumeric_id


FACE_DISTANCE_THRESHOLD = 0.38
# Prevent Duplicate Registration
@app.route("/api/register", methods=["POST"])
def register_voter():
    try:
        voter_id = request.form.get("voter_id")
        name = request.form.get("name")
        aadhaar_id = request.form.get("aadhaar_id")
        phone = request.form.get("phone")
        passkey = request.form.get("passkey")
        face_image = request.files["face_image"]
        
        start_time = time.time()

        if not all([name, voter_id, aadhaar_id, phone, passkey, face_image]):
            return jsonify({"status": "error", "message": "All fields are required"}), 400
        
        # Fetch all voters
        voters_ref = db.reference("Voters").get()

        # Ensure voters_ref is not None before accessing it
        if voters_ref:
            for voter in voters_ref.values():
                if voter["registration_block"]["data"]["phone"] == phone:
                    return jsonify({"status": "error", "message": "Phone number already registered"}), 409
                if voter["registration_block"]["data"]["aadhaar_id"] == aadhaar_id:
                    return jsonify({"status": "error", "message": "Aadhaar ID already registered"}), 409

        # Check if voter ID already exists
        voter_ref = db.reference(f"Voters/{voter_id}").get()
        if voter_ref:
            return jsonify({"status": "error", "message": "Voter already registered"}), 409

        # Save Image
        image_path = f"face_detection/images/{voter_id}.jpg"
        face_image.save(image_path)

        # Face Encoding
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image, model="cnn")

        if len(encodings) == 0:
            os.remove(image_path)
            return jsonify({"status": "error", "message": "No face detected"}), 400
        
        face_encoding = encodings[0].tolist()

        # Check if face is already registered
        if voters_ref:
            for voter in voters_ref.values():
                existing_encoding = np.array(voter["registration_block"]["data"]["face_encoding"])
                distance = np.linalg.norm(existing_encoding - face_encoding)
                if distance < FACE_DISTANCE_THRESHOLD:
                    return jsonify({"status": "error", "message": "Face already registered under a different voter ID"}), 409
                

        # **REGISTRATION BLOCK**
        registration_data = {
            "voter_id": voter_id,
            "name": name,
            "aadhaar_id": aadhaar_id,
            "phone": phone,
            "passkey": passkey,
            "face_encoding": face_encoding
        }

        registration_hash = generate_hash(registration_data)
        # Convert the face_encoding list-of-floats to a short ID
        unique_tracking_id = generate_short_id(registration_hash, face_encoding)


        # **LOGIN BLOCK (Initially Empty)**
        login_block_data = {
            "voter_id": voter_id,
            "timestamps": [0],
            "previous_hash": registration_hash  # Links to Registration Block
        }

        login_block_hash = generate_hash(login_block_data)

        # **Store Data in Firebase**
        voter_data = {
            "registration_block": {
                "data": registration_data,
                "hash": registration_hash,
                "previous_hash": "0", # First block
                "tracking_id": unique_tracking_id
            },
            "voter_login_block": {
                "data": login_block_data,
                "hash": login_block_hash
            }
        }

        db.reference(f"Voters/{voter_id}").set(voter_data)
        log_metrics(voter_id, "register", start_time)

        return jsonify({
            "status": "success",
            "message": "Voter Registered Successfully",
            "tracking_id": unique_tracking_id, 
            "login_block_hash": login_block_hash
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# API: Login a voter and store timestamp in the blockchain
@app.route("/api/login", methods=["POST"])
def login_voter():
    try:
        voter_id = request.form.get("voter_id")
        passkey = request.form.get("passkey")
        face_image = request.files.get("face_image")
        
        start_time = time.time()

        if not all([voter_id, passkey, face_image]):
            return jsonify({"status": "error", "message": "Voter ID, Passkey, and Face Image required"}), 400

        # 🔥 Fetch ONLY the specific voter details
        voter_data = db.reference(f"Voters/{voter_id}/registration_block/data").get()
        login_block = db.reference(f"Voters/{voter_id}/voter_login_block").get()

        if not voter_data or not login_block:
            return jsonify({"status": "error", "message": "Voter not found"}), 404

        # 🔑 Step 1: Verify Passkey First
        if voter_data.get("passkey") != passkey:
            return jsonify({"status": "error", "message": "Incorrect passkey. Login denied."}), 401

        # 🏆 Step 2: Fetch ONLY This User's Stored Face Encoding
        stored_encoding = np.array(voter_data["face_encoding"])  # Convert stored list to numpy array

        # 🖼 Step 3: Load and Encode New Face for Comparison
        image_path = f"face_detection/temp.jpg"
        face_image.save(image_path)
        image = cv2.imread(image_path)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        encodings = face_recognition.face_encodings(rgb_image, model="cnn")

        if not encodings:
            return jsonify({"status": "error", "message": "No face detected"}), 400

        new_encoding = np.array(encodings[0])  # Convert new encoding to numpy array

        # 🔍 Step 4: Use Euclidean Distance for Comparison (instead of simple match)
        distance = np.linalg.norm(stored_encoding - new_encoding)

        if distance > FACE_DISTANCE_THRESHOLD:
            return jsonify({"status": "error", "message": f"Face mismatch. Login denied. Distance: {distance:.2f}"}), 401

        # ✅ Step 5: Successful Login → Store timestamp in login block
        login_timestamp = datetime.now().isoformat()
        login_block["data"]["timestamps"].append(login_timestamp)

        # 🔗 Step 6: Update Login Block Hash
        updated_login_block_hash = generate_hash(login_block["data"])
        login_block["hash"] = updated_login_block_hash

        # 📌 Step 7: Store Updated Login Block in Firebase
        db.reference(f"Voters/{voter_id}/voter_login_block").set(login_block)

        # 🔓 Step 8: Manage Session and Return Success
        log_metrics(voter_id, "login", start_time)
        
        session["voter_id"] = voter_id
        return jsonify({
            "status": "success",
            "message": "Login Successful",
            "login_block_hash": updated_login_block_hash,
            "redirect": "/index"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# API: Logout
@app.route("/logout")
def logout():
    session.pop("voter_id", None)
    return redirect(url_for('home'))

@app.route("/reset_system", methods=["POST", "OPTIONS"])
def reset_system():
    if request.method == "OPTIONS":
        return jsonify({"status": "success"}), 200
    
    try:
        print("\n=== Starting system reset ===")
        
        # Clear Firebase data
        print("Clearing Firebase...")
        db.reference('Voters').delete()
        print("✓ Firebase data cleared")
        
        print("Clearing Firebase tracking IDs...")
        db.reference("UsedTrackingIDs").delete()  # ✅ Clears all used tracking IDs
        print("✓ Tracking IDs reset successfully")

        # Delete EncodeFile.p
        print("Deleting EncodeFile.p...")
        if os.path.exists(ENCODE_FILE):
            os.remove(ENCODE_FILE)
            print("✓ EncodeFile.p deleted")

        # Clear Images directory
        print("Resetting Images directory...")
        if os.path.exists(IMAGES_DIR):
            shutil.rmtree(IMAGES_DIR)
        os.makedirs(IMAGES_DIR, exist_ok=True)
        print("✓ Images directory reset")

        # Reset encodings
        with open(ENCODE_FILE, 'wb') as file:
            pickle.dump([[], []], file)
        print("✓ Fresh EncodeFile.p created")

        return jsonify({"status": "success", "message": "System reset complete"})

    except Exception as e:
        print(f"Reset error: {str(e)}")
        return jsonify({"status": "error", "message": f"Error during reset: {str(e)}"}), 500

@app.route("/api/get_trackingID", methods=["GET"])
def get_merkle_root():
    voter_id = request.args.get("voter_id")

    if not voter_id:
        return jsonify({"status": "error", "message": "Voter ID required"}), 400

    # Fetch voter data from Firebase
    voter_data = db.reference(f"Voters/{voter_id}").get()

    if not voter_data or "registration_block" not in voter_data:
        return jsonify({"status": "error", "message": "Tracking ID not found"}), 404  

    # Retrieve tracking ID directly from Firebase
    tracking_id = voter_data["registration_block"].get("tracking_id", None)

    if not tracking_id:
        return jsonify({"status": "error", "message": "Tracking ID not available"}), 404

    print(f"📌 Fetching Tracking ID for {voter_id}: {tracking_id}")  # Debug log

    return jsonify({"status": "success", "tracking_id": tracking_id})

@app.route("/api/log_metrics", methods=["POST"])
def log_metrics_endpoint():
    """
    Receives performance data from the client (JS) and
    appends it to performance_data.csv using the same format.
    """
    try:
        data = request.get_json()
        voter_id = data.get("voter_id", "unknown")
        action = data.get("action", "unknown")
        latency = data.get("latency", 0.0)

        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(LOG_FILE, "a", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([voter_id, action, latency, timestamp])

        print(f"✅ Logged metric from client: {action}, {latency:.4f}s")
        return jsonify({"status": "success", "message": "Metrics logged"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
@app.route("/api/store_used_voter", methods=["POST"])
def store_used_voter():
    try:
        data = request.get_json()
        voter_id = data.get("voter_id")

        if not voter_id:
            return jsonify({"status": "error", "message": "Voter ID is required"}), 400

        # Store voter ID in Firebase
        db.reference(f"UsedVoterIDs/{voter_id}").set({"status": "used"})

        return jsonify({"status": "success", "message": "Voter ID stored"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/check_used_voter", methods=["GET"])
def check_used_voter():
    try:
        voter_id = request.args.get("voter_id")

        if not voter_id:
            return jsonify({"status": "error", "message": "Voter ID is required"}), 400

        # Check in Firebase
        voter_status = db.reference(f"UsedVoterIDs/{voter_id}").get()

        if voter_status:
            return jsonify({"status": "used", "message": "Voter has already voted"})
        else:
            return jsonify({"status": "not_used", "message": "Voter has not voted"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    



if __name__ == "__main__":
    app.run(debug=True, port=5000)
