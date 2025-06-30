import face_recognition
import numpy as np
import base64
import cv2
from app.db import get_db
from bson.objectid import ObjectId

def verify_face_from_base64(user_id, base64_img):
    # Decode the base64 image to an array
    img_bytes = base64.b64decode(base64_img)
    np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    # Convert image from BGR to RGB
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Detect face and encode
    faces = face_recognition.face_locations(rgb_frame)
    if not faces:
        return False

    encoding = face_recognition.face_encodings(rgb_frame, faces)[0]

    # Fetch stored encoding from DB
    db = get_db()
    users = db['users']
    user = users.find_one({'_id': ObjectId(user_id)})
    if not user or 'face_encoding' not in user:
        return False

    stored_encoding = np.array(user['face_encoding'])

    # Compare
    results = face_recognition.compare_faces([stored_encoding], encoding)
    return results[0]

def save_face_encoding(user_id, frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    faces = face_recognition.face_locations(rgb_frame)
    if not faces:
        return False

    encoding = face_recognition.face_encodings(rgb_frame, faces)[0]
    db = get_db()
    db.users.update_one(
        {'_id': ObjectId(user_id)},
        {'$set': {'face_encoding': encoding.tolist()}}
    )
    return True