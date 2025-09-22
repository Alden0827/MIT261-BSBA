from pymongo import MongoClient
from config.settings import APP_TITLE, DEFAULT_PAGE_TITLE, MONGODB_URI, DB_NAME
import pandas as pd
import os
import pickle   # ✅ Needed for checkpoint save/load

# Database connection
# client = MongoClient(MONGODB_URI)
client = MongoClient('mongodb://localhost:27017/')
CACHE_DIR = "./cache"
db = client['mit261m']


from pymongo import MongoClient
import pandas as pd

def get_predicted_subjects(db, student_id, semester_id):
    """
    Predicts recommended and blocked subjects for a student for a given semester.
    Uses curriculum + student grades + prerequisites.
    """

    from helpers.data_helper import data_helper
    dh = data_helper({"db": db})

    # 1. Get student info
    student = db.students.find_one({"_id": student_id})
    if not student:
        return pd.DataFrame(), pd.DataFrame()
    student_course = student.get("Course")
    student_year = student.get("YearLevel")

    # 2. Get curriculum for the student's course
    curriculum_df = dh.get_curriculum(student_course)
    if curriculum_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    curriculum_df.columns = curriculum_df.columns.str.strip()  # cleanup

    # 3. Get student's grades
    grades_df = dh.get_grades(student_id=student_id)
    passed_subjects, taken_subjects = [], []
    if not grades_df.empty:
        grades_flat = grades_df.explode(['SubjectCodes', 'Grades'])
        passed_subjects = grades_flat[grades_flat['Grades'] >= 75]["SubjectCodes"].tolist()
        taken_subjects = grades_flat["SubjectCodes"].tolist()

    # 4. Get semester info
    semester_doc = db.semesters.find_one({"_id": semester_id})
    if not semester_doc:
        return pd.DataFrame(), pd.DataFrame()

    semester_name = semester_doc.get("Semester")   # e.g. "First", "Second", "Summer"
    school_year = semester_doc.get("SchoolYear")

    # 5. Filter curriculum for semester + year + not already taken
    print(curriculum_df)
    print('taken_subjects:',taken_subjects)
    potential_subjects = curriculum_df[
        (curriculum_df["semester"].str.lower() == semester_name.lower())
        & (curriculum_df["year"] == student_year)
        & (~curriculum_df["Subject Code"].isin(taken_subjects))
    ].copy()

    print('potential_subjects:',potential_subjects)

    available_subjects, blocked_subjects = [], []

    # 6. Evaluate prerequisites
    for _, row in potential_subjects.iterrows():
        prereqs = row.get("preRequisites", [])
        if not prereqs or all(pr in passed_subjects for pr in prereqs):
            available_subjects.append({
                "Subject Code": row["code"],
                "Description": row["name"],
                "Units": row["unit"],
                "Year Level": row["year"],
                "Semester": row["semester"],
                "SchoolYear": school_year
            })
        else:
            blocked_subjects.append({
                "Subject Code": row["code"],
                "Description": row["name"],
                "Units": row["unit"],
                "Year Level": row["year"],
                "Semester": row["semester"],
                "Prerequisites": ", ".join(prereqs),
                "SchoolYear": school_year
            })

    return pd.DataFrame(available_subjects), pd.DataFrame(blocked_subjects)


a = get_predicted_subjects(db=db, student_id=500001, semester_id=16)
print(a)

