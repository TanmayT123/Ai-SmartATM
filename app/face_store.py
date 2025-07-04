# app/face_store.py

from app.db import get_db

def save_user_encoding(phone, face_encoding):
    db = get_db()
    collection = db['face_encodings']

    existing = collection.find_one({'phone': phone})
    if existing:
        collection.update_one(
            {'phone': phone},
            {'$set': {'encoding': face_encoding.tolist()}}
        )
    else:
        collection.insert_one({
            'phone': phone,
            'encoding': face_encoding.tolist()
        })

def get_all_encodings():
    db = get_db()
    collection = db['face_encodings']
    data = collection.find()
    return {item['phone']: item['encoding'] for item in data}
