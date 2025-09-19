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


# Find all documents where Leonor Rivera is one of the teachers
cursor = db.grades.find({ "Teachers": "Leonor Rivera" })

rows = []
for doc in cursor:
    # Teachers, Subjects, Grades are all aligned by index
    for subj, grade, teacher in zip(doc["SubjectCodes"], doc["Grades"], doc["Teachers"]):
        if teacher == "Leonor Rivera":  # filter subjects under Leonor Rivera only
            rows.append({
                "StudentID": doc["StudentID"],
                "Subject": subj,
                "Grade": grade,
                "Teacher": teacher,
                "SemesterID": doc.get("SemesterID")
            })

df = pd.DataFrame(rows)

print(df["Subject"])
