from pymongo import MongoClient
from config.settings import APP_TITLE, DEFAULT_PAGE_TITLE, MONGODB_URI, DB_NAME
import pandas as pd
import os
import pickle   # ✅ Needed for checkpoint save/load
from helpers.cache_helper import cache_meta, load_or_query

# Database connection
client = MongoClient(MONGODB_URI)
# client = MongoClient('mongodb://localhost:27017/')
CACHE_DIR = "./cache"
db = client['mit261']


from pymongo import MongoClient
import pandas as pd

def get_student_subjects_grades(db, StudentID=None, limit=1000):
    """
    Returns all subjects and grades for a specific student with:
    ["Subject Code", "Description", "Grade", "Semester", "SchoolYear"]
    """

    def query():
        if StudentID is None:
            return pd.DataFrame()

        student_id = int(StudentID)
        grade_docs = db.grades.find({"StudentID": student_id})  # ✅ Multiple documents

        rows = []
        for grade_doc in grade_docs:
            subject_codes = grade_doc.get("SubjectCodes", [])
            grades = grade_doc.get("Grades", [])
            semester_id = grade_doc.get("SemesterID")

            # Fetch semester info
            sem = db.semesters.find_one({"_id": semester_id})
            semester = sem["Semester"] if sem else None
            school_year = sem["SchoolYear"] if sem else None

            # Process each subject
            for code, grade in zip(subject_codes, grades):
                subj = db.subjects.find_one({"_id": code})
                desc = subj["Description"] if subj else None

                rows.append({
                    "Subject Code": code,
                    "Description": desc,
                    "Grade": grade,
                    "Semester": semester,
                    "SchoolYear": school_year
                })

        # Apply limit
        if limit:
            rows = rows[:limit]

        return pd.DataFrame(rows)

    return query()  # no caching


a = get_student_subjects_grades(db=db, StudentID=500002)
a.to_excel("grades.xlsx")

