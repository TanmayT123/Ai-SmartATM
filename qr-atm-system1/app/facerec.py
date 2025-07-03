import face_recognition
import numpy as np
import base64
import cv2
from io import BytesIO
from PIL import Image
from app.face_store import save_user_encoding, get_all_encodings

# ---------------------------
# Helper: Convert base64 → image (RGB)
# ---------------------------
def decode_base64_image(base64_string):
    try:
        header, encoded = base64_string.split(",", 1)
    except ValueError:
        encoded = base64_string
    img_data = base64.b64decode(encoded)
    image = Image.open(BytesIO(img_data))
    rgb_image = image.convert("RGB")  # Ensure it's in RGB mode
    return np.array(rgb_image)

# ---------------------------
# REGISTER FACE (Save encoding to MongoDB)
# ---------------------------
def register_face_from_base64(base64_image, user_id):
    image = decode_base64_image(base64_image)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        return False  # ❌ No face detected

    face_encoding = encodings[0]
    save_user_encoding(user_id, face_encoding)  # Save to MongoDB
    return True

# ---------------------------
# VERIFY FACE (Compare with MongoDB stored encodings)
# ---------------------------
def verify_face_from_base64(base64_image, tolerance=0.45):
    image = decode_base64_image(base64_image)
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        return False  # ❌ No face detected

    current_encoding = encodings[0]

    all_encodings = get_all_encodings()  # {user_id: [128 floats]}
    for user_id, stored_encoding in all_encodings.items():
        stored_encoding_np = np.array(stored_encoding)
        matches = face_recognition.compare_faces([stored_encoding_np], current_encoding, tolerance=tolerance)
        if matches[0]:
            return True  # ✅ Face matched

    return False  # ❌ No match
