# app/facerec.py
import cv2
import face_recognition
import numpy as np
from .db import get_db

def capture_face():
    cam = cv2.VideoCapture(0)
    while True:
        ret, frame = cam.read()
        cv2.imshow("Face Capture - Press 'q' to capture", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()

    faces = face_recognition.face_locations(frame)
    if faces:
        encoding = face_recognition.face_encodings(frame, faces)[0]
        return encoding
    return None

def register_face(username):
    db = get_db()
    encoding = capture_face()
    if encoding is not None:
        db.users.update_one({"username": username}, {"$set": {"face_encoding": encoding.tolist()}})
        return True
    return False

def verify_face(username):
    db = get_db()
    user = db.users.find_one({"username": username})
    if not user or "face_encoding" not in user:
        return False

    stored_encoding = np.array(user["face_encoding"])
    encoding = capture_face()
    if encoding is not None:
        return face_recognition.compare_faces([stored_encoding], encoding)[0]
    return False
