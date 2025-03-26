import cv2
import face_recognition
import pickle
import os
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': "https://face-detection-4e986-default-rtdb.asia-southeast1.firebasedatabase.app/",  # Replace with your database URL
})

# Import voter images
folderPath = 'Images'  # Folder for voter images
pathList = os.listdir(folderPath)
imgList = []
voterIds = []  # Store voter IDs

for path in pathList:
    img = cv2.imread(os.path.join(folderPath, path))
    if img is not None:  # Check if the image was loaded successfully
        imgList.append(img)
        voterIds.append(os.path.splitext(path)[0])  # Extract voter ID from filename (e.g., 12345.jpg -> 12345)
    else:
        print(f"Warning: Unable to load image {path}")

print("Voter IDs:", voterIds)

# Function to encode images
def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # Convert to RGB for face_recognition
        encodings = face_recognition.face_encodings(img)
        if encodings:  # Check if encodings were found
            encodeList.append(encodings[0])  # Generate encodings
        else:
            print("Warning: No face found in image.")
    return encodeList

# Generate encodings and save to file
print("Encoding started...")
encodeListKnown = findEncodings(imgList)
encodeListWithIds = [encodeListKnown, voterIds]
pickle.dump(encodeListWithIds, open("VoterEncodeFile.p", 'wb'))  # Save encodings and voter IDs
print("Encodings saved.")

# Save to file
file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListWithIds, file)
file.close()
print("Encodings Saved")