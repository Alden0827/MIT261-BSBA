import sys
import pandas as pd
from pymongo import MongoClient

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------
try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    db = client['mit261']
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()


import pandas as pd

grades_col = db["grades"]
students_col = db["students"]
semesters_col = db["semesters"]

teacher_name = "Leonor Rivera"  # example

query = {"Teachers": teacher_name}
grades_cursor = grades_col.find(query)

rows = []
for g in grades_cursor:
    # look up related student
    student = students_col.find_one({"_id": g["StudentID"]}) or {}
    # look up related semester
    semester = semesters_col.find_one({"_id": g["SemesterID"]}) or {}

    # iterate through each subject/teacher/grade
    for idx, teacher in enumerate(g.get("Teachers", [])):
        if teacher == teacher_name:  # only keep rows for that teacher
            rows.append({
                "StudentID": g.get("StudentID"),
                "Name": student.get("Name"),
                "Course": student.get("Course"),
                "YearLevel": student.get("YearLevel"),
                "Semester": semester.get("Semester"),
                "SchoolYear": semester.get("SchoolYear"),
                "Teacher": teacher,
                "SubjectCode": g.get("SubjectCodes", [])[idx] if idx < len(g.get("SubjectCodes", [])) else None,
                "Grade": g.get("Grades", [])[idx] if idx < len(g.get("Grades", [])) else None,
                "Status": g.get("Status", [])[idx] if idx < len(g.get("Status", [])) else None,
            })

df = pd.DataFrame(rows)
df.to_excel("asdadasdasd.xlsx")