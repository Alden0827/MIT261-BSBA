import sys, os
import random
from datetime import datetime
from pymongo import MongoClient

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------
try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    db = client['mit261']

    # client = MongoClient("mongodb://localhost:27017/")
    # db = client['mit261m']
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()



def populate(TARGET_SEMESTER_ID,TARGET_PROGRAM = "BSBA", school_year=1, semester_label ="second"):
    # -------------------------------------------------------------------
    # Parameters
    # -------------------------------------------------------------------
    
    # TARGET_SEMESTER_ID = 16 #firstSem 2025

    # Mock registrar/dean user
    REGISTERED_BY = {"userId": 1, "name": "Registrar Script"}
    APPROVED_BY = {"id": 2, "fullName": "Dean Approver"}

    # -------------------------------------------------------------------
    # Step 1: Fetch students enrolled in BSBA
    # -------------------------------------------------------------------
    students = list(db.students.find({"Course": {"$regex": TARGET_PROGRAM, "$options": "i"}}))

    if not students:
        print(f"⚠️ No students found for program {TARGET_PROGRAM}")
        sys.exit()

    print(f"📌 Found {len(students)} BSBA students.")

    # -------------------------------------------------------------------
    # Step 2: Get curriculum for BSBA
    # -------------------------------------------------------------------
    curriculum = db.curriculum.find_one({"programCode": TARGET_PROGRAM})

    if not curriculum:
        print(f"⚠️ No curriculum found for program {TARGET_PROGRAM}")
        sys.exit()

    all_subjects = curriculum.get("subjects", [])
    if not all_subjects:
        print("⚠️ Curriculum has no subjects.")
        sys.exit()

    # ✅ Keep only Year 1, First Semester subjects
    subjects = [
        s for s in all_subjects 
        if s.get("year") == school_year and s.get("semester", "").lower() == semester_label
    ]

    print(f"📚 Loaded {len(subjects)} subjects for Year 1 - First Semester (BSBA).")

    # -------------------------------------------------------------------
    # Step 3: Enroll each student
    # -------------------------------------------------------------------
    for student in students:
        student_id = student["_id"]

        # Check if already enrolled for semesterId = 16
        existing = db.enrollments.find_one({"StudentID": student_id, "SemesterID": TARGET_SEMESTER_ID})
        if existing:
            print(f"⏭️ Student {student_id} already has enrollment for semester {TARGET_SEMESTER_ID}")
            continue

        # Build subjects list for enrollment
        enrollment_subjects = []
        for subj in subjects:
            enrollment_subjects.append({
                "subjectCode": subj["code"],
                "description": subj["name"],
                "Units": subj["unit"],
                "teacher": None,
                "status": "Enrolled"
            })

        enrollment_doc = {
            "StudentID": student_id,
            "SemesterID": TARGET_SEMESTER_ID,
            "schoolYear": 2025,  # adjust dynamically if needed
            "status": "Enrolled",
            "registrationDate": datetime.utcnow(),
            "subjects": enrollment_subjects,
            "registeredBy": REGISTERED_BY,
            "approvedAt": datetime.utcnow(),
            "approvedBy": APPROVED_BY,
            "lastUpdated": datetime.utcnow(),
            "updatedBy": APPROVED_BY
        }

        db.enrollments.insert_one(enrollment_doc)
        print(f"✅ Inserted enrollment for student {student_id}")

        # -------------------------------------------------------------------
        # Step 4: Create grades document with dummy grades
        # -------------------------------------------------------------------
        subject_codes = [subj["code"] for subj in subjects]
        grades_list = [random.randint(55, 95) for _ in subjects]

        # Fetch teacher from subjects collection
        teachers_list = []
        for code in subject_codes:
            subj_doc = db.subjects.find_one({"_id": code})
            teachers_list.append(subj_doc["Teacher"] if subj_doc and "Teacher" in subj_doc else None)

        status_list = ["Final" for _ in subjects]

        grades_doc = {
            "StudentID": student_id,
            "SubjectCodes": subject_codes,
            "Grades": grades_list,
            "Teachers": teachers_list,
            "SemesterID": TARGET_SEMESTER_ID,
            "Status": status_list,
            "createdByScript": True
        }

        db.grades.insert_one(grades_doc)
        print(f"✅ Created grades record for student {student_id} with dummy grades.")

    print("🎉 Done populating BSBA enrollments and grades with dummy values for semesterId = 16.")




def assign_random_teachers_to_subjects():
    """
    Updates all subjects with Teacher=None or missing,
    assigns a random Philippine national hero as teacher.
    """
    heroes = [
        "José Rizal",
        "Andrés Bonifacio y de Castro",
        "Emilio Aguinaldo",
        "Apolinario Mabini",
        "Marcelo H. del Pilar",
        "Melchora Aquino",
        "Juan Luna",
        "Gabriela Silang",
        "Diego Silang",
        "Antonio Luna",
        "Graciano López Jaena",
        "Josefa Llanes Escoda",
        "Sultan Kudarat",
        "Lapu-Lapu",
        "Francisco Balagtas",
        "Gregorio del Pilar",
        "Vicente Lim",
        "Trinidad Tecson",
        "Leonor Rivera",
        "Felipe Agoncillo",
        "Ninoy Aquino",
        "Corazon Aquino",
        "Carlos P. Romulo",
        "Jose Abad Santos",
        "Emilio Jacinto",
        "Isabelo de los Reyes"
    ]


    subjects = db.subjects.find({"$or": [{"Teacher": None}, {"Teacher": {"$exists": False}}]})
    count = 0

    for subj in subjects:
        random_teacher = random.choice(heroes)
        db.subjects.update_one(
            {"_id": subj["_id"]},
            {"$set": {"Teacher": random_teacher}}
        )
        count += 1
        print(f"✅ Updated subject {subj['_id']} → {random_teacher}")

    print(f"🎉 Done! {count} subjects updated with random teachers.")
    return count

def roll_back(TARGET_SEMESTER_ID):
    data2 = db.enrollments.delete_many({"SemesterID": TARGET_SEMESTER_ID,"StudentID": {"$gte":500001}})
    data = db.grades.delete_many({"SemesterID": TARGET_SEMESTER_ID,"StudentID": {"$gte":500001}})
    print('roll_back',data,data2)

if __name__ == "__main__":
    # # assign_random_teachers_to_subjects()


    roll_back(TARGET_SEMESTER_ID=7)
    roll_back(TARGET_SEMESTER_ID=8)
    roll_back(TARGET_SEMESTER_ID=9)
    roll_back(TARGET_SEMESTER_ID=10)
    roll_back(TARGET_SEMESTER_ID=11)
    roll_back(TARGET_SEMESTER_ID=12)

    roll_back(TARGET_SEMESTER_ID=13)
    roll_back(TARGET_SEMESTER_ID=14)
    roll_back(TARGET_SEMESTER_ID=15)

    roll_back(TARGET_SEMESTER_ID=16)
    # roll_back(TARGET_SEMESTER_ID=17)

    populate(TARGET_SEMESTER_ID=7, school_year=1, semester_label ="first") #first 2022
    populate(TARGET_SEMESTER_ID=8, school_year=1, semester_label ="second") #second 2022
    # populate(TARGET_SEMESTER_ID=9, school_year=1, semester_label ="summer") #summer 2022

    populate(TARGET_SEMESTER_ID=10, school_year=2, semester_label ="first") #first 2023
    populate(TARGET_SEMESTER_ID=11, school_year=2, semester_label ="second") #second 2023
    # populate(TARGET_SEMESTER_ID=12, school_year=2, semester_label ="summer") #summer 2023

    populate(TARGET_SEMESTER_ID=13, school_year=3, semester_label ="first") #first 2024
    populate(TARGET_SEMESTER_ID=14, school_year=3, semester_label ="second") #second 2024
    # populate(TARGET_SEMESTER_ID=15, school_year=3, semester_label ="summer") #summer 2024

    populate(TARGET_SEMESTER_ID=16, school_year=4, semester_label ="first") #first 2025
