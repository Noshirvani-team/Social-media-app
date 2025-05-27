from pymongo import MongoClient
import os
import gridfs

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URL)
mongo_db = client["social_app"]
posts_collection = mongo_db["posts"]
fs = gridfs.GridFS(mongo_db)
