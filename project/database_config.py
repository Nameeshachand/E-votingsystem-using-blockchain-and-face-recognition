import firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    """Initialize Firebase connection."""
    service_account_path = "serviceAccountKey.json"
    if not firebase_admin._apps:  # Ensure Firebase is initialized only once
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': "https://face-detection-4e986-default-rtdb.asia-southeast1.firebasedatabase.app/"
        })

def get_database_reference():
    """Get Firebase database reference."""
    initialize_firebase()
    return db.reference()

def clear_firebase_data():
    """Clear all blockchain and voter data from Firebase."""
    try:
        ref = get_database_reference()
        ref.child("Blockchain").delete()
        ref.child("Voters").delete()
        return {"status": "success", "message": "Firebase data cleared"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
