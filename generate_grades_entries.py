import json
import random
from pymongo import MongoClient
from config.settings import MONGODB_URI
# MongoDB connection
client = MongoClient(MONGODB_URI)  # <-- change if needed
db = client["mit261"]

students_col = db["students"]
curriculum_col = db["curriculum"]

# 1. Get all BSBA students
students = list(students_col.find({"Course": "BSBA"}))

# 2. Get BSBA subjects from curriculum
curriculum = curriculum_col.find_one({"programCode": "BSBA"})
subjects = [sub["code"] for sub in curriculum["subjects"]]

# Teacher pool
teacher_pool = ["Albert Eingstein", "Jose Riza", "Apolinario Mabini"]

# 3. Generate grades JSON
grades_data = []
semester_id = 1  # default (you may modify logic if needed)

for idx, student in enumerate(students, start=1):
    student_grades = {
        "_id": idx,  # sequential id for grades collection
        "StudentID": student["_id"],
        "SubjectCodes": subjects,
        "Grades": [random.randint(75, 95) for _ in subjects],  # random grades
        "Teachers": [random.choice(teacher_pool) for _ in subjects],  # randomize per subject
        "SemesterID": semester_id
    }
    grades_data.append(student_grades)

# Save to data.json
with open("data.json", "w", encoding="utf-8") as f:
    json.dump(grades_data, f, indent=4, ensure_ascii=False)

print(f"✅ Generated grades for {len(students)} BSBA students into data.json")
