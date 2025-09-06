import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.settings import MONGODB_URI, DB_NAME
from pymongo import MongoClient


# connect
client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
users_col = db["userAccounts"]

# add fullName with default blank to all documents
result = users_col.update_many(
    {},  # match all documents
    {"$set": {"fullName": ""}}  # add new field
)

print(f"✅ Updated {result.modified_count} documents.")
