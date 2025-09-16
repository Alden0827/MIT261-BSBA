

# helpers/grade_helper.py
from pymongo.collection import Collection
from typing import List, Optional
import pandas as pd
from cache_helper import cache_meta

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from pymongo import MongoClient

# MongoDB Connection
try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net") # Or your connection string
    db = client['mit261']
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit()


def assign_teacher_to_subject(student_id: int, semester_id: int, subject_code: str, teacher_name: str) -> bool:
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


def set_student_grade(student_id: int, semester_id: int, subject_code: str, grade: int) -> bool:
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


def set_subject_status(student_id: int, semester_id: int, subject_code: str, status: str) -> bool:
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

@cache_meta()
def get_student_grades(student_id: int, semester_id: int) -> Optional[dict]:
    """
    Retrieve the full grade document for a student in a semester.
    """
    return db["grades"].find_one({"StudentID": student_id, "SemesterID": semester_id})

@cache_meta()
def get_teachers(course: str = None):
    """
    Fetches all teachers who taught subjects to students of a specific course.
    If no course is specified, it fetches all teachers.
    Returns a DataFrame with columns: ['Teacher', 'Subject Code', 'Subject Description', 'Student Count']
    """

    # Build the filter based on whether a course is provided
    query_filter = {}
    if course:
        query_filter["Course"] = course

    # 1. Get student IDs based on the filter
    students_cursor = db.students.find(query_filter, {"_id": 1})
    student_ids = [s["_id"] for s in students_cursor]

    # If no students are found (either for the specific course or in general)
    if not student_ids:
        return pd.DataFrame()

    # 2. Get all grades for these students
    grades_cursor = db.grades.find(
        {"StudentID": {"$in": student_ids}},
        {"StudentID": 1, "SubjectCodes": 1, "Teachers": 1}
    )

    rows = []
    for doc in grades_cursor:
        # The zip function handles cases where the arrays are of unequal length or empty.
        for code, teacher in zip(doc.get("SubjectCodes", []), doc.get("Teachers", [])):
            if code and teacher:  # Ensure both code and teacher exist
                rows.append({"Subject Code": code, "Teacher": teacher, "StudentID": doc["StudentID"]})

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # 3. Join with subjects collection to get subject description
    subjects = db.subjects.find({}, {"_id": 1, "Description": 1})
    subj_map = {s["_id"]: s.get("Description", "") for s in subjects}
    df["Subject Description"] = df["Subject Code"].map(subj_map)
    
    # 4. Aggregate by teacher + subject
    summary = df.groupby(["Teacher", "Subject Code", "Subject Description"]).agg(
        Student_Count=("StudentID", "nunique")
    ).reset_index()

    return summary

# @cache_meta()
def get_latest_semester_students(course=None, semester_id=None, avg_grades_lte=None):
    """
    Fetches students registered in a specified or the latest semester,
    with optional filters for course and average grades.

    Args:
        db: The MongoDB database object.
        course (str, optional): The course name to filter by. Defaults to None.
        semester_id (int, optional): The ID of the semester to fetch students from. 
                                     If None, the latest semester is used.
        avg_grades_lte (int, optional): The maximum average grade a student can have.
                                        Students with an average grade less than or equal to this
                                        value will be included.

    Returns:
        pd.DataFrame: A DataFrame with student information or an empty DataFrame if no
                      students are found. Columns are [StudentID, Name, Year Level, Total Units].
    """
    students_df = pd.DataFrame(columns=['StudentID', 'Name', 'Year Level', 'Total Units'])

    try:
        # Determine the semester to use
        if semester_id is None:
            latest_semester_doc = db['semesters'].find_one(sort=[('_id', -1)])
            if not latest_semester_doc:
                print("No semesters found.")
                return students_df
            semester_id_to_use = latest_semester_doc['_id']
        else:
            semester_id_to_use = semester_id
        
        # Get all grades documents for the specified or latest semester
        grades_cursor = db['grades'].find({'SemesterID': semester_id_to_use})
        grades_docs = list(grades_cursor)
        
        if not grades_docs:
            print(f"No students found registered in semester ID {semester_id_to_use}.")
            return students_df

        # Calculate total grades, number of subjects, and total units for each student
        student_data_temp = {}
        subject_units_cache = {}

        for doc in grades_docs:
            student_id = doc['StudentID']
            if student_id not in student_data_temp:
                student_data_temp[student_id] = {'TotalGrades': 0, 'NumSubjects': 0, 'TotalUnits': 0, 'SubjectCodes': set()}
            
            # Sum up grades for the student
            student_data_temp[student_id]['TotalGrades'] += sum(doc.get('Grades', []))
            student_data_temp[student_id]['NumSubjects'] += len(doc.get('SubjectCodes', []))

            # Collect subject codes to fetch units later
            student_data_temp[student_id]['SubjectCodes'].update(doc.get('SubjectCodes', []))

        # Fetch units for all unique subjects at once
        all_subject_codes = set()
        for student_info in student_data_temp.values():
            all_subject_codes.update(student_info['SubjectCodes'])

        subjects_cursor = db['subjects'].find({'_id': {'$in': list(all_subject_codes)}})
        for subject in subjects_cursor:
            subject_units_cache[subject['_id']] = subject.get('Units', 0)

        # Calculate total units and average grades
        student_ids_to_fetch = []
        for student_id, student_info in student_data_temp.items():
            total_units = sum(subject_units_cache.get(code, 0) for code in student_info['SubjectCodes'])
            student_data_temp[student_id]['TotalUnits'] = total_units

            average_grade = student_info['TotalGrades'] / student_info['NumSubjects'] if student_info['NumSubjects'] > 0 else 0
            student_data_temp[student_id]['AverageGrade'] = average_grade

            # Apply the new avg_grades_lte condition
            if avg_grades_lte is None or average_grade <= avg_grades_lte:
                student_ids_to_fetch.append(student_id)

        if not student_ids_to_fetch:
            print("No students found matching the average grade filter.")
            return students_df

        query = {'_id': {'$in': student_ids_to_fetch}}
        if course:
            query['Course'] = course

        # Fetch student details and build the DataFrame
        students_cursor = db['students'].find(query)
        students_data = []
        for student in students_cursor:
            student_id = student['_id']
            students_data.append({
                'StudentID': student_id,
                'Name': student.get('Name'),
                'Year Level': student.get('YearLevel'),
                'Total Units': student_data_temp.get(student_id, {}).get('TotalUnits', 0)
            })
        
        students_df = pd.DataFrame(students_data)
        
    except Exception as e:
        print(f"An error occurred: {e}")
    
    
    return students_df
if __name__ == "__main__":

    # Assign teacher
    # assign_teacher_to_subject(db, student_id=1, semester_id=6, subject_code="IT405", teacher_name="Prof. Alden Quiñones")

    # # Update grade
    # success = set_student_grade(student_id=1, semester_id=6, subject_code="IT405", grade=95)
    # print(success)

    # # Set status
    # success = set_subject_status(student_id=500001, semester_id=6, subject_code="IT405", status="Dropped")
    # print(success)

    # # Fetch full record
    # doc = get_student_grades(student_id=1, semester_id=6)
    # print(doc["SubjectCodes"], doc["Grades"], doc["Teachers"], doc["Status"])

    # data = get_teachers('BSBA')
    # print(data)
    
    df_filtered = get_latest_semester_students(course="BSBA",semester_id=17,avg_grades_lte=85)
    print(df_filtered)

    