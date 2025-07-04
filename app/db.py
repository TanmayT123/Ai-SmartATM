from pymongo import MongoClient

def get_db():
    uri = "mongodb+srv://smartatm:Smart%40123atm@qr-atm.hanobry.mongodb.net/"
    client = MongoClient(uri)
    db = client['qr_atm']
    return db