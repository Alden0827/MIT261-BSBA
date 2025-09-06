import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random
from pymongo import MongoClient
from config.settings import MONGODB_URI

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client["mit261"]

students_col = db["students"]
curriculum_col = db["curriculum"]
grades_col = db["grades"]

# 1. Get all BSBA students
students = list(students_col.find({"Course": "BSBA"}))

# 2. Get BSBA subjects from curriculum
curriculum = curriculum_col.find_one({"programCode": "BSBA"})
subjects = [sub["code"] for sub in curriculum["subjects"]]

# Teacher pool
teacher_pool = ["Albert Eingstein", "Jose Riza", "Apolinario Mabini"]

# 3. Find the last _id in grades collection
last_record = grades_col.find_one(sort=[("_id", -1)])
last_id = last_record["_id"] if last_record else 0  # start from 0 if empty

# 4. Generate grades and insert into collection
semester_id = 1  # default (you may modify logic if needed)

grades_data = []
for idx, student in enumerate(students, start=1):
    student_grades = {
        "_id": last_id + idx,  # continue from last id
        "StudentID": student["_id"],
        "SubjectCodes": subjects,
        "Grades": [random.randint(75, 95) for _ in subjects],
        "Teachers": [random.choice(teacher_pool) for _ in subjects],
        "SemesterID": semester_id
    }
    grades_data.append(student_grades)

# Insert to grades collection
if grades_data:
    grades_col.insert_many(grades_data)
    print(f"✅ Inserted {len(students)} new grade records starting from ID {last_id + 1}")
else:
    print("⚠️ No students found to insert grades.")
