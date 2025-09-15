# import sys, os
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# from config.settings import MONGODB_URI, DB_NAME

# from pymongo import MongoClient


# from rapidfuzz import process

# def find_best_match(query, collection):
#     # Get all names from students collection
#     names = [doc["Name"] for doc in collection.find({}, {"Name": 1})]

#     # Find best match
#     best_match = process.extractOne(query, names)  # (name, score, index)
#     return best_match



# client = MongoClient(MONGODB_URI)
# db = client["mit261"]
# students_col = db["students"]

# query_name = "Quinones, Alden"
# match = find_best_match(query_name, students_col)

# if match:
#     best_name, score, _ = match
#     print(f"Best match: {best_name} ({score:.1f}%)")

#     # fetch full student record
#     student = students_col.find_one({"Name": best_name})
#     print(student)
