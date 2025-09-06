from pymongo import MongoClient
from config.settings import MONGODB_URI
# MongoDB connection
client = MongoClient(MONGODB_URI)  # change if needed

db = client["mit261"]  # your database name
subjects_col = db["subjects"]  # collection for subjects
curricula_col = db["curriculum"]  # collection for curriculum

def fetch_subjects():
    """Fetch all documents from subjects collection"""
    return list(subjects_col.find({}))

def insert_subject(subject):
    """
    Insert subject into collection.
    If _id already exists, update the existing record instead of skipping.
    subject format:
    {
      "_id": "GE 200",
      "Description": "Understanding the Self",
      "Units": 3,
      "Teacher": None
    }
    """
    result = subjects_col.update_one(
        {"_id": subject["_id"]},   # filter
        {"$set": subject},         # update fields
        upsert=True                # insert if not exists
    )

    if result.matched_count > 0:
        print(f"Updated: {subject['_id']}")
    elif result.upserted_id:
        print(f"Inserted: {subject['_id']}")
    return True
    
def insert_subjects_from_curriculum(curriculum_id):
    """
    Extract subjects from curriculum document
    and insert into subjects collection.
    """
    curriculum = curricula_col.find_one({"_id": curriculum_id})
    if not curriculum:
        print("Curriculum not found!")
        return

    for subj in curriculum.get("subjects", []):
        subject_doc = {
            "_id": subj["code"],
            "Description": subj["name"],
            "Units": subj["unit"],
            "Teacher": None
        }
        insert_subject(subject_doc)

if __name__ == "__main__":
    # Example: insert subjects from a specific curriculum
    curriculum_oid = {"$oid": "68b6a4a4b4ad4b9a7a79e496"}  # replace with actual ObjectId
    from bson import ObjectId
    insert_subjects_from_curriculum(ObjectId("68b6a4a4b4ad4b9a7a79e496"))

    # Fetch and print subjects
    print(fetch_subjects())
