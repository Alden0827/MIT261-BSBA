# ---------------- populate_students.py ----------------
from pymongo import MongoClient
from faker import Faker
import random
from config.settings import MONGODB_URI, DB_NAME

# --- MongoDB connection ---
COLLECTION_NAME = "students"

client = MongoClient(MONGODB_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# --- Faker with Filipino locale ---
fake = Faker("en_PH")

# --- Get the last numeric _id ---
last_student = collection.find_one(sort=[("_id", -1)])
last_id = last_student["_id"] if last_student else 0

students_to_insert = []
for i in range(1, 101):  # generate 100 students
    new_id = last_id + i

    # Format: Lastname, Firstname M.
    first_name = fake.first_name()
    middle_initial = fake.first_name()[0] + "."
    last_name = fake.last_name()
    full_name = f"{last_name}, {first_name} {middle_initial}"

    student = {
        "_id": new_id,
        "Name": full_name,
        "Course": "BSBA",
        "YearLevel": 1
    }
    students_to_insert.append(student)

# --- Insert into MongoDB ---
if students_to_insert:
    result = collection.insert_many(students_to_insert)
    print(f"✅ Inserted {len(result.inserted_ids)} students into '{COLLECTION_NAME}' collection.")
else:
    print("⚠️ No students generated.")
