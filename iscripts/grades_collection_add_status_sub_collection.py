from pymongo import MongoClient
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))


uri = "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261"

def add_status_to_grades():
    client = MongoClient(uri)
    db = client["mit261"]
    grades_col = db["grades"]

    # Find all documents
    for doc in grades_col.find({}):
        # Skip if 'Status' already exists
        if "Status" in doc:
            continue

        subject_count = len(doc.get("SubjectCodes", []))
        status_list = [""] * subject_count  # default empty strings

        # Update the document
        grades_col.update_one(
            {"_id": doc["_id"]},
            {"$set": {"Status": status_list}}
        )
        print(f"Updated document _id={doc['_id']} with Status={status_list}")

    print("✅ All grades documents updated.")


add_status_to_grades()