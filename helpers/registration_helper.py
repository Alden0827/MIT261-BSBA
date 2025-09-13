import pandas as pd
from rapidfuzz import process, fuzz
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pymongo import MongoClient
from config.settings import MONGODB_URI, CACHE_MAX_AGE
client = MongoClient(MONGODB_URI)
db = client["mit261"]
def find_best_match(query, collection, limit=10):
    """Search students by keywords in any order (case-insensitive)."""
    words = query.strip().split()
    # Build regex with lookaheads so all words must appear in any order
    regex_pattern = "".join(f"(?=.*{word})" for word in words) + ".*"
    regex_query = {"Name": {"$regex": regex_pattern, "$options": "i"}}
    return list(collection.find(regex_query, {"Name": 1}).limit(limit))
if __name__  == "__main__":
    students_col = db["students"]
    # data = find_best_match("Alden",students_col)
    print(data)