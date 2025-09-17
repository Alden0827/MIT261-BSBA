import pandas as pd
from rapidfuzz import process, fuzz
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pymongo.collection import Collection
import pandas as pd
from cache_helper import cache_meta
from datetime import datetime
from typing import List
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from bson.objectid import ObjectId
from pymongo import MongoClient

# MongoDB Connection
try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    db = client['mit261']
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()



def find_best_match(query=None, course=None, collection=None, limit=200):

    if collection is None:
        raise ValueError("⚠️ You must pass a MongoDB collection (e.g., db.students).")

    filters = []

    # --- Name filter ---
    if query and isinstance(query, str):
        words = query.strip().split()
        regex_pattern = "".join(f"(?=.*{word})" for word in words) + ".*"
        filters.append({"Name": {"$regex": regex_pattern, "$options": "i"}})

    # --- Course filter ---
    if course and isinstance(course, str):
        filters.append({"Course": {"$regex": course, "$options": "i"}})

    # --- Build query ---
    if not filters:
        query_filter = {}
    elif len(filters) == 1:
        query_filter = filters[0]
    else:
        query_filter = {"$and": filters}

    # --- Execute query ---
    projection = {"Name": 1, "Course": 1}
    return list(collection.find(query_filter, projection).limit(limit))

def get_enrolled_students(course=None, semester_id=None):
    """
    Fetches students enrolled in a specified or the latest semester (from enrollments),
    with optional filter for course.
    """
    students_df = pd.DataFrame(columns=['StudentID', 'Name', 'Year Level', 'Total Units'])

    try:
        # Determine semester
        if semester_id is None:
            latest_semester_doc = db['semesters'].find_one(sort=[('_id', -1)])
            if not latest_semester_doc:
                print("⚠️ No semesters found.")
                return students_df
            semester_id_to_use = latest_semester_doc['_id']
        else:
            semester_id_to_use = semester_id

        # Fetch enrollments
        enrollments_cursor = db['enrollments'].find({
            'semesterId': semester_id_to_use,
            'status': 'Enrolled'
        })
        enrollment_docs = list(enrollments_cursor)

        if not enrollment_docs:
            print(f"⚠️ No students found enrolled in semester ID {semester_id_to_use}.")
            return students_df

        students_data = []

        for enrollment in enrollment_docs:
            student_id = enrollment['studentId']
            student_doc = db['students'].find_one({'_id': student_id})
            if not student_doc:
                continue

            # Total units
            total_units = sum(subj.get("Units", 0) for subj in enrollment.get("subjects", []))

            # Apply course filter
            if course and student_doc.get("Course") != course:
                continue

            students_data.append({
                'StudentID': student_id,
                'Name': student_doc.get('Name'),
                'Year Level': student_doc.get('YearLevel'),
                'Total Units': total_units
            })

        if students_data:
            students_df = pd.DataFrame(students_data)

    except Exception as e:
        print(f"❌ An error occurred: {e}")

    return students_df

def approve_enrollee(student_id: str, semester_id: int, subject_codes: List[str], approved_by_user: dict):
    """
    Approves a pending enrollment, moves status to 'Enrolled',
    and creates a single grade entry (with arrays) for the semester.
    """
    enrollment = db.enrollments.find_one({"studentId": student_id, "semesterId": semester_id})

    if not enrollment or enrollment.get("status") != "Pending":
        print(f"❌ No pending enrollment found for student {student_id} in semester {semester_id}.")
        return None

    # ✅ Mark enrollment as Enrolled
    db.enrollments.update_one(
        {"_id": enrollment["_id"]},
        {
            "$set": {
                "status": "Enrolled",
                "approvedBy": {
                    "id": approved_by_user["_id"],
                    "fullName": approved_by_user["fullName"]
                },
                "approvedAt": datetime.utcnow(),
            }
        }
    )

    # ✅ Prepare grade document
    subjects = enrollment.get("subjects", [])
    subject_codes_list = [subj["subjectCode"] for subj in subjects]
    grades_list = [0] * len(subjects)
    teachers_list = [""] * len(subjects)
    status_list = [""] * len(subjects)

    grade_doc = {
        "StudentID": student_id,
        "SubjectCodes": subject_codes_list,
        "Grades": grades_list,
        "Teachers": teachers_list,
        "SemesterID": semester_id,
        "Status": status_list
    }

    # ✅ Auto-increment `_id` for grades
    last_grade = db.grades.find_one(sort=[("_id", -1)])
    next_id = (last_grade["_id"] + 1) if last_grade else 1
    grade_doc["_id"] = next_id

    # ✅ Insert single grade entry
    db.grades.insert_one(grade_doc)

    print(f"✅ Enrollment approved and grade record created for {len(subjects)} subjects.")
    return enrollment["_id"]

def add_pending_enrollee(student_id, semester_id, subject_codes=None, registered_by_user=None):
    """
    Adds a new student enrollment with Pending status for approval.

    Args:
        student_id (str): ID of the student.
        semester_id (int/str): ID of the semester.
        subject_codes (list, optional): List of subject IDs to pre-assign (default: None).
        registered_by_user (dict, optional): User who registered (e.g., {"_id": 1, "fullName": "Registrar"}).
    """
    try:
        # Fetch semester details
        semester = db.semesters.find_one({"_id": semester_id})
        if not semester:
            raise ValueError(f"Semester with ID {semester_id} not found.")

        subjects = []
        if subject_codes:
            for code in subject_codes:
                subj = db.subjects.find_one({"_id": code})
                if subj:
                    subjects.append({
                        "subjectCode": subj["_id"],
                        "description": subj["Description"],
                        "Units": subj["Units"],
                        "teacher": subj["Teacher"],
                        "status": "Pending"   # Mark subject as pending
                    })

        enrollment_doc = {
            "studentId": student_id,
            "semesterId": semester_id,
            "schoolYear": semester["SchoolYear"],
            "status": "Pending",  # Overall enrollment status
            "registrationDate": datetime.utcnow(),
            "subjects": subjects,
            "registeredBy": {
                "userId": registered_by_user["_id"] if registered_by_user else None,
                "name": registered_by_user["fullName"] if registered_by_user else None
            }
        }

        result = db.enrollments.insert_one(enrollment_doc)
        print(f"✅ Pending enrollment added with ID {result.inserted_id}")
        return result.inserted_id

    except Exception as e:
        print(f"❌ Error adding pending enrollee: {e}")
        return None

def discard_pending_enrollee(student_id, semester_id, discarded_by_user=None, reason=None):
    """
    Discards a pending enrollment request.

    Args:
        student_id (str): ID of the student.
        semester_id (int/str): ID of the semester.
        discarded_by_user (dict, optional): User who discarded (e.g., {"_id": 1, "fullName": "Registrar"}).
        reason (str, optional): Reason for discarding.
    """
    try:
        result = db.enrollments.update_one(
            {
                "studentId": student_id,
                "semesterId": semester_id,
                "status": "Pending"   # Only discard if still pending
            },
            {
                "$set": {
                    "status": "Discarded",
                    "discardedDate": datetime.utcnow(),
                    "discardedBy": {
                        "userId": discarded_by_user["_id"] if discarded_by_user else None,
                        "name": discarded_by_user["fullName"] if discarded_by_user else None
                    },
                    "discardReason": reason
                }
            }
        )

        if result.modified_count > 0:
            print(f"✅ Pending enrollment for student {student_id} discarded.")
            return True
        else:
            print(f"⚠️ No pending enrollment found for student {student_id} in semester {semester_id}.")
            return False

    except Exception as e:
        print(f"❌ Error discarding pending enrollee: {e}")
        return False

def get_pending_enrollees(semester_id=None, course=None):
    """
    Fetch students with pending enrollment status for review.
    """
    students_df = pd.DataFrame(columns=['StudentID', 'Name', 'Year Level', 'Course', 'Requested Units'])

    try:
        query = {"status": "Pending"}
        if semester_id:
            query["semesterId"] = semester_id

        pending_docs = list(db.enrollments.find(query))
        if not pending_docs:
            print("⚠️ No pending enrollees found.")
            return students_df

        students_data = []
        for enrollment in pending_docs:
            
            student_doc = db.students.find_one({"_id": enrollment["studentId"]})
            print('data:',student_doc)
            if not student_doc:
                print('skip student_doc')
                continue
            # Apply course filter
            
            if course and student_doc.get("Course") != course:
                print('skip course')
                continue

            requested_units = sum(subj.get("Units", 0) for subj in enrollment.get("subjects", []))
            

            students_data.append({
                "StudentID": enrollment["studentId"],
                "Name": student_doc.get("Name"),
                "Year Level": student_doc.get("YearLevel"),
                "Course": student_doc.get("Course"),
                "Requested Units": requested_units
            })

        if students_data:
            students_df = pd.DataFrame(students_data)

    except Exception as e:
        print(f"❌ Error fetching pending enrollees: {e}")

    return students_df


def get_discarded_enrollees(semester_id=None):
    """
    Fetch students whose enrollment requests were discarded.
    """
    try:
        query = {"status": "Discarded"}
        if semester_id:
            query["semesterId"] = semester_id

        discarded_docs = list(db.enrollments.find(query))
        return pd.DataFrame(discarded_docs) if discarded_docs else pd.DataFrame()

    except Exception as e:
        print(f"❌ Error fetching discarded enrollees: {e}")
        return pd.DataFrame()

def update_enrollment(student_id, semester_id, add_subjects=None, drop_subjects=None, updated_by_user=None):
    """
    Update an enrollment (add/drop subjects) and sync grades collection.
    Prevents duplicate subject additions.
    """
    try:
        enrollment = db.enrollments.find_one(
            {"studentId": student_id, "semesterId": semester_id, "status": "Enrolled"}
        )
        if not enrollment:
            print(f"⚠️ No active enrollment found for student {student_id} in semester {semester_id}.")
            return False

        subjects = enrollment.get("subjects", [])

        # === 1. DROP subjects from enrollment ===
        if drop_subjects:
            subjects = [s for s in subjects if s["subjectCode"] not in drop_subjects]

        # === 2. ADD subjects to enrollment (skip duplicates) ===
        existing_codes = {s["subjectCode"] for s in subjects}  # set for fast lookup
        if add_subjects:
            for code in add_subjects:
                if code in existing_codes:
                    print(f"⚠️ Subject {code} already exists in enrollment, skipping.")
                    continue
                subj = db.subjects.find_one({"_id": code})
                if subj:
                    subjects.append({
                        "subjectCode": subj["_id"],
                        "description": subj["Description"],
                        "Units": subj["Units"],
                        "teacher": subj["Teacher"],
                        "status": "Enrolled"
                    })
                    existing_codes.add(code)

        # === 3. Update enrollment document ===
        result = db.enrollments.update_one(
            {"_id": enrollment["_id"]},
            {
                "$set": {
                    "subjects": subjects,
                    "lastUpdated": datetime.utcnow(),
                    "updatedBy": {
                        "userId": updated_by_user["_id"] if updated_by_user else None,
                        "name": updated_by_user["fullName"] if updated_by_user else None
                    }
                }
            }
        )

        # === 4. Sync grades document ===
        grade_doc = db.grades.find_one({"StudentID": student_id, "SemesterID": semester_id})
        if grade_doc:
            subject_codes = [s["subjectCode"] for s in subjects]
            grades = [0] * len(subjects)
            teachers = [""] * len(subjects)
            status = [""] * len(subjects)

            db.grades.update_one(
                {"_id": grade_doc["_id"]},
                {"$set": {
                    "SubjectCodes": subject_codes,
                    "Grades": grades,
                    "Teachers": teachers,
                    "Status": status
                }}
            )
            print(f"📘 Grades synced for student {student_id}.")
        else:
            print(f"⚠️ No grades doc found for student {student_id} in semester {semester_id}.")

        if result.modified_count > 0:
            print(f"✅ Enrollment updated for student {student_id}.")
            return True
        else:
            print(f"⚠️ No changes applied to enrollment for student {student_id}.")
            return False

    except Exception as e:
        print(f"❌ Error updating enrollment: {e}")
        return False

def is_already_enrolled(student_id, semester_id):
    """
    Check if a student is already enrolled (to prevent duplicates).
    """
    try:
        exists = db.enrollments.find_one({
            "studentId": student_id,
            "semesterId": semester_id,
            "status": {"$in": ["Pending", "Enrolled"]}
        })
        return exists is not None
    except Exception as e:
        print(f"❌ Error checking enrollment status: {e}")
        return False

if __name__ == "__main__":
    # Example test data
    test_student_id = 500002   # Replace with a valid student _id from your DB
    test_semester_id = 17       # Replace with an existing semester _id
    test_subjects = ["GE 402", "GE 302"]  # Replace with real subject IDs
    registrar_user = {"_id": 1, "fullName": "Registrar Test"}
    approver_user = {"_id": 2, "fullName": "Dean Approver"}

    print("\n=== SIMULATION START ===")

    # 1. Add a pending enrollment
    print("\n➡️ Adding Pending Enrollment...")
    pending_id = add_pending_enrollee(
        student_id=test_student_id,
        semester_id=test_semester_id,
        subject_codes=test_subjects,
        registered_by_user=registrar_user
    )

    # 2. Fetch pending enrollees
    print("\n➡️ Fetching Pending Enrollees...")
    df_pending = get_pending_enrollees(semester_id=test_semester_id)
    print(df_pending)

    # # 3. Approve pending enrollment
    pending_id = ObjectId("68ca2102b184ab6d79c7f3cc")
    if pending_id:
        print("\n➡️ Approving Enrollment...")
        approved_id = approve_enrollee(
            student_id=test_student_id,
            semester_id=test_semester_id,
            subject_codes=test_subjects,
            approved_by_user=approver_user
        )
        print(f"✅ Enrollment Approved with ID {approved_id}")

    # # 4. Update enrollment (add/drop subjects)
    print("\n➡️ Updating Enrollment (Add one, Drop one)...")
    update_result = update_enrollment(
        student_id=test_student_id,
        semester_id=test_semester_id,
        add_subjects=["GE 403"],   # Add another subject
        drop_subjects=["GE 402"],  # Drop one subject
        updated_by_user=approver_user
    )
    print("Update Success:", update_result)

    # # 5. Fetch enrolled students
    print("\n➡️ Fetching Enrolled Students...")
    df_enrolled = get_enrolled_students(course="BSBA", semester_id=test_semester_id)
    print(df_enrolled)

    # # 6. Discard a pending enrollment (simulate another request)
    print("\n➡️ Discarding Pending Enrollment...")
    discard_result = discard_pending_enrollee(
        student_id=test_student_id,
        semester_id=test_semester_id,
        discarded_by_user=registrar_user,
        reason="Incomplete requirements"
    )
    print("Discard Success:", discard_result)

    # # 7. Fetch discarded enrollees
    print("\n➡️ Fetching Discarded Enrollees...")
    df_discarded = get_discarded_enrollees(semester_id=test_semester_id)
    print(df_discarded)

    # # 8. Print final enrollment record with subjects and grades
    print("\n➡️ Final Enrollment Record with Grades")
    enrollment = db.enrollments.find_one(
        {"studentId": test_student_id, "semesterId": test_semester_id, "status": "Enrolled"}
    )
    if enrollment:
        subjects = enrollment.get("subjects", [])
        for subj in subjects:
            # Assign mock grades if not present
            if "grade" not in subj:
                subj["grade"] = 80 + (hash(subj["subjectCode"]) % 20)  # random-ish grade
        # Save back to DB with grades
        db.enrollments.update_one({"_id": enrollment["_id"]}, {"$set": {"subjects": subjects}})
        
        # Print results
        print(f"Student: {enrollment['studentId']} | Semester: {enrollment['semesterId']}")
        for subj in subjects:
            print(f"   {subj['subjectCode']} - {subj['description']} | Units: {subj['Units']} | Grade: {subj['grade']}")

        # Compute GPA / average grade
        grades = [s["grade"] for s in subjects if "grade" in s]
        avg_grade = sum(grades) / len(grades) if grades else None
        print(f"\n📊 GPA / Average Grade: {avg_grade:.2f}" if avg_grade else "No grades found.")


    # print("\n=== SIMULATION END ===")



if __name__  == "__main__":

    pass