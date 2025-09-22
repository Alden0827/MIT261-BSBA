import sys, os
import random
from pymongo import MongoClient

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------
try:
    # client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    # db = client['mit261']

    client = MongoClient('mongodb://localhost:27017/')
    db = client['mit261m']

    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()


# -------------------------------------------------------------------
# Function: Update all grades for given students within a score range
# -------------------------------------------------------------------
def update_grades_scores(StudentIDs, GradeRange):
    """
    Update all grades for the given list of StudentIDs.
    Each grade will be replaced with a random integer within GradeRange.
    
    Args:
        StudentIDs (list[int]): List of student IDs to update.
        GradeRange (list[int]): [min, max] grade range.
    """
    min_grade, max_grade = GradeRange

    for student_id in StudentIDs:
        grade_docs = list(db.grades.find({"StudentID": student_id}))

        if not grade_docs:
            print(f"⚠️ No grade documents found for student {student_id}")
            continue

        for gdoc in grade_docs:
            subject_count = len(gdoc.get("SubjectCodes", []))

            if subject_count == 0:
                print(f"⚠️ Student {student_id} grade doc {_id} has no subjects.")
                continue

            # Generate new grades
            new_grades = [random.randint(min_grade, max_grade) for _ in range(subject_count)]

            # Update the document
            db.grades.update_one(
                {"_id": gdoc["_id"]},
                {"$set": {"Grades": new_grades}}
            )

            print(f"✅ Updated grades for Student {student_id}, Semester {gdoc.get('SemesterID')} → {new_grades}")


def set_grade_status(StudentID, Subjects, Grades, Statuses):
    """
    Update specific subjects' grades and statuses for a student.

    Args:
        StudentID (int/str): The student's ID
        Subjects (list): List of subject codes (e.g., ['GE 203','GE 204'])
        Grades (list): List of grades (e.g., [0,0,0])
        Statuses (list): List of statuses (e.g., ['INC','INC'])
    """
    if not (len(Subjects) == len(Grades) == len(Statuses)):
        raise ValueError("Subjects, Grades, and Statuses must be the same length")

    grade_doc = db.grades.find_one({"StudentID": StudentID})
    if not grade_doc:
        print(f"⚠️ No grades record found for StudentID {StudentID}")
        return

    subject_codes = grade_doc.get("SubjectCodes", [])
    grades = grade_doc.get("Grades", [])
    status_list = grade_doc.get("Status", [])

    updated = False
    for subj, new_grade, new_status in zip(Subjects, Grades, Statuses):
        if subj in subject_codes:
            idx = subject_codes.index(subj)
            grades[idx] = new_grade
            status_list[idx] = new_status
            updated = True
            print(f"✅ Updated {subj}: Grade={new_grade}, Status={new_status}")
        else:
            print(f"⏭️ Subject {subj} not found for StudentID {StudentID}")

    if updated:
        db.grades.update_one(
            {"_id": grade_doc["_id"]},
            {"$set": {"Grades": grades, "Status": status_list}}
        )
        print(f"🎉 Grades updated successfully for StudentID {StudentID}")


# -------------------------------------------------------------------
# Example Usage
# -------------------------------------------------------------------
if __name__ == "__main__":


    # deans listers
    StudentIDs = [500011, 500012, 500013, 500014,500015,500016,500017,500018,500019,500020]
    GradeRange = [90, 99]  # random grades between 60 and 90
    update_grades_scores(StudentIDs, GradeRange)
    print("🎉 Grade updates complete.")


    #INC
    # set_grade_status(
    #     StudentID=500001,
    #     Subjects=['GE 203','GE 204', 'GE 201'],
    #     Grades=[0, 0, 0],
    #     Statuses=['INC','INC','INC']
    # )
    # set_grade_status(
    #     StudentID=500002,
    #     Subjects=['GE 203','GE 204'],
    #     Grades=[0, 0],
    #     Statuses=['INC','INC']
    # )

    # set_grade_status(
    #     StudentID=500003,
    #     Subjects=['GE 203','GE 204'],
    #     Grades=[0, 0],
    #     Statuses=['INC','INC']
    # )
