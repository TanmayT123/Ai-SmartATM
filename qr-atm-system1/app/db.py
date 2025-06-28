# app/db.py

from pymongo import MongoClient
from urllib.parse import quote_plus

def get_db():
    # Replace these with your actual MongoDB username and password
    username = quote_plus("smartatm")          # e.g., 'admin'
    password = quote_plus("Smart@123atm")      # special chars must be encoded!

    # MongoDB URI with properly escaped credentials
    uri = f"mongodb://{username}:{password}@localhost:27017/"

    # Create the MongoDB client and connect to database named 'qr_atm'
    client = MongoClient(uri)
    db = client['qr_atm']
    return db
