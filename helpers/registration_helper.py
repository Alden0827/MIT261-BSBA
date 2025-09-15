import pandas as pd
from rapidfuzz import process, fuzz
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# def find_best_match(query, collection, limit=10):
#     """Search students by keywords in any order (case-insensitive)."""
#     words = query.strip().split()
#     # Build regex with lookaheads so all words must appear in any order
#     regex_pattern = "".join(f"(?=.*{word})" for word in words) + ".*"
#     regex_query = {"Name": {"$regex": regex_pattern, "$options": "i"}}
#     return list(collection.find(regex_query, {"Name": 1}).limit(limit))

def find_best_match(query=None, course=None, collection=None, limit=10):
    """
    Search students by optional Name and/or Course.
    - query: search string for Name (all words must appear).
    - course: optional course filter (partial match allowed).
    - collection: MongoDB students collection.
    - limit: max results to return.
    """
    if collection is None:
        raise ValueError("⚠️ You must pass a MongoDB collection (e.g., db.students).")

    filters = []

    # --- Name filter ---
    if query and isinstance(query, str):
        words = query.strip().split()
        regex_pattern = "".join(f"(?=.*{word})" for word in words) + ".*"
        filters.append({"Name": {"$regex": regex_pattern, "$options": "i"}})

    # --- Course filter ---
    if course and isinstance(course, str):
        filters.append({"Course": {"$regex": course, "$options": "i"}})

    # --- Build query ---
    if not filters:
        query_filter = {}
    elif len(filters) == 1:
        query_filter = filters[0]
    else:
        query_filter = {"$and": filters}

    # --- Execute query ---
    projection = {"Name": 1, "Course": 1}
    return list(collection.find(query_filter, projection).limit(limit))


if __name__  == "__main__":

    from pymongo import MongoClient
    from config.settings import MONGODB_URI, CACHE_MAX_AGE
    client = MongoClient(MONGODB_URI)

    db = client["mit261"]

    data = find_best_match("ALDEN", course="Computer Science", collection=db.students)
    print(data)
    pass