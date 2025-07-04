# app/face_store.py

from app.db import get_db

def save_user_encoding(user_id, face_encoding):
    db = get_db()
    collection = db['face_encodings']

    existing = collection.find_one({'user_id': user_id})
    if existing:
        collection.update_one({'user_id': user_id}, {'$set': {'encoding': face_encoding.tolist()}})
    else:
        collection.insert_one({'user_id': user_id, 'encoding': face_encoding.tolist()})

def get_all_encodings():
    db = get_db()
    collection = db['face_encodings']
    data = collection.find()
    return {item['user_id']: item['encoding'] for item in data}
