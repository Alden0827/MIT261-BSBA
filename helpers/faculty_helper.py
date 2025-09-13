# helpers/grade_helper.py
from pymongo.collection import Collection
from typing import List, Optional

def assign_teacher_to_subject(db, student_id: int, semester_id: int, subject_code: str, teacher_name: str) -> bool:
    """
    Assign a teacher to a specific subject of a student in the grades collection.
    Returns True if the update was successful, False if subject not found.
    """
    grades_col: Collection = db["grades"]

    grade_doc = grades_col.find_one({"StudentID": student_id, "SemesterID": semester_id})
    if not grade_doc or subject_code not in grade_doc.get("SubjectCodes", []):
        return False

    index = grade_doc["SubjectCodes"].index(subject_code)
    grades_col.update_one(
        {"_id": grade_doc["_id"]},
        {"$set": {f"Teachers.{index}": teacher_name}}
    )
    return True


def set_student_grade(db, student_id: int, semester_id: int, subject_code: str, grade: int) -> bool:
    """
    Set/update a grade for a student in a specific subject.
    Returns True if updated, False if not found.
    """
    grades_col: Collection = db["grades"]

    grade_doc = grades_col.find_one({"StudentID": student_id, "SemesterID": semester_id})
    if not grade_doc or subject_code not in grade_doc.get("SubjectCodes", []):
        return False

    index = grade_doc["SubjectCodes"].index(subject_code)
    grades_col.update_one(
        {"_id": grade_doc["_id"]},
        {"$set": {f"Grades.{index}": grade}}
    )
    return True


def set_subject_status(db, student_id: int, semester_id: int, subject_code: str, status: str) -> bool:
    """
    Set/update the status of a subject for a student (e.g., '', 'Dropped', 'INC').
    Returns True if updated, False if not found.
    """
    grades_col: Collection = db["grades"]

    grade_doc = grades_col.find_one({"StudentID": student_id, "SemesterID": semester_id})
    if not grade_doc or subject_code not in grade_doc.get("SubjectCodes", []):
        return False

    # Ensure Status array exists and has the same length as SubjectCodes
    if "Status" not in grade_doc or len(grade_doc["Status"]) != len(grade_doc["SubjectCodes"]):
        grade_doc["Status"] = [""] * len(grade_doc["SubjectCodes"])
        grades_col.update_one({"_id": grade_doc["_id"]}, {"$set": {"Status": grade_doc["Status"]}})

    index = grade_doc["SubjectCodes"].index(subject_code)
    grades_col.update_one(
        {"_id": grade_doc["_id"]},
        {"$set": {f"Status.{index}": status}}
    )
    return True


def get_student_grades(db, student_id: int, semester_id: int) -> Optional[dict]:
    """
    Retrieve the full grade document for a student in a semester.
    """
    return db["grades"].find_one({"StudentID": student_id, "SemesterID": semester_id})


def get_teachers(db):
    """
    Fetch all teachers who taught subjects to BSBA students.
    Returns a DataFrame with columns: ['Teacher', 'Subject Code', 'Subject Description', 'Student Count']
    """

    # 1. Get all BSBA student IDs
    bsba_students = list(db.students.find({"Course": "BSBA"}, {"_id": 1}))
    if not bsba_students:
        return pd.DataFrame()

    student_ids = [s["_id"] for s in bsba_students]

    # 2. Get all grades for these students
    grades_cursor = db.grades.find(
        {"StudentID": {"$in": student_ids}},
        {"StudentID": 1, "SubjectCodes": 1, "Teachers": 1}
    )

    rows = []
    for doc in grades_cursor:
        for code, teacher in zip(doc.get("SubjectCodes", []), doc.get("Teachers", [])):
            rows.append({"Subject Code": code, "Teacher": teacher, "StudentID": doc["StudentID"]})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 3. Optional: join with subjects collection to get subject description
    subjects = db.subjects.find({}, {"_id": 1, "Description": 1})
    subj_map = {s["_id"]: s.get("Description", "") for s in subjects}
    df["Subject Description"] = df["Subject Code"].map(subj_map)

    # 4. Aggregate by teacher + subject
    summary = df.groupby(["Teacher", "Subject Code", "Subject Description"]).agg(
        Student_Count=("StudentID", "nunique")
    ).reset_index()

    return summary


if __name__ == "__main__":

    # Assign teacher
    # assign_teacher_to_subject(db, student_id=1, semester_id=6, subject_code="IT405", teacher_name="Prof. Alden Quiñones")

    # # Update grade
    # set_student_grade(db, student_id=1, semester_id=6, subject_code="IT405", grade=95)

    # # Set status
    # set_subject_status(db, student_id=1, semester_id=6, subject_code="IT405", status="Dropped")

    # # Fetch full record
    # doc = get_student_grades(db, student_id=1, semester_id=6)
    # print(doc["SubjectCodes"], doc["Grades"], doc["Teachers"], doc["Status"])

    data = get_teachers()
    print(data)
