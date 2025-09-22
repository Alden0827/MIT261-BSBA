from pymongo import MongoClient
from config.settings import APP_TITLE, DEFAULT_PAGE_TITLE, MONGODB_URI, DB_NAME
import pandas as pd 

# Database connection
# client = MongoClient(MONGODB_URI)
client = MongoClient('mongodb://localhost:27017/')

db = client['mit261m']

def get_semesters(db, teacher=None):
    """
    Returns semesters available in the database.
    Optionally filters to only semesters where the specified teacher has subjects.

    :param db: MongoDB database object
    :param teacher: Optional teacher name to filter semesters
    :return: Dict with {_id: "Semester SchoolYear"}

    Sample returned data: {13: 'FirstSem 2024', 14: 'SecondSem 2024'}
    """
    if not teacher:
        semesters = db.semesters.find()
    else:
        # Get all subject codes taught by the teacher
        teacher_subjects = db.subjects.find({"Teacher": teacher})
        teacher_subject_codes = [s["_id"] for s in teacher_subjects]

        # Get grades that match the teacher's subjects
        grades_cursor = db.grades.find({"SubjectCodes": {"$in": teacher_subject_codes}})
        semester_ids = {g["SemesterID"] for g in grades_cursor if "SemesterID" in g}

        # Fetch only semesters corresponding to the filtered IDs
        semesters = db.semesters.find({"_id": {"$in": list(semester_ids)}})

    # Build dictionary {id: "Semester SchoolYear"}
    semester_dict = {s["_id"]: f"{s['Semester']} {s['SchoolYear']}" for s in semesters}

    # Sort by SchoolYear + Semester (if needed)
    semester_dict = dict(sorted(semester_dict.items(), key=lambda x: str(x[1])))

    return semester_dict


a = get_semesters(db,"Leonor Rivera")
print(list(a))

