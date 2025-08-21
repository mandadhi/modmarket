# marketplace/db.py
import os
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ServerSelectionTimeoutError

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "modmarket")

_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=8000)
db = _client[MONGO_DB_NAME]

def ensure_indexes():
    # Products
    db.products.create_index([("status", ASCENDING)])
    db.products.create_index([("created_at", DESCENDING)])
    db.products.create_index([("download_count", DESCENDING)])
    db.products.create_index([("rating", DESCENDING)])
    db.products.create_index([("title", ASCENDING)])
    db.products.create_index([("tags", ASCENDING)])

    # Categories
    db.categories.create_index([("category", ASCENDING)], unique=True)
    

    # Developers
    db.developers.create_index([("user_id", ASCENDING)], unique=True)

    # Reviews
    db.reviews.create_index([("product_id", ASCENDING), ("created_at", DESCENDING)])
    db.reviews.create_index([("user_id", ASCENDING), ("product_id", ASCENDING)], unique=True)

    # Downloads (prevent multiple download-count bumps)
    db.downloads.create_index([("user_id", ASCENDING), ("product_id", ASCENDING)], unique=True)

    # Product files
    db.product_files.create_index([("product_id", ASCENDING)])
    db.product_files.create_index([("file_type", ASCENDING)])

try:
    _client.admin.command("ping")
    ensure_indexes()
except ServerSelectionTimeoutError:
    # If DB is unreachable at import-time, app can still boot; indexes will be created on first successful connection.
    pass
