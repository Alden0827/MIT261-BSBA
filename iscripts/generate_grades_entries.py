# reset grades 

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import random
from pymongo import MongoClient
from config.settings import MONGODB_URI

# MongoDB connection
client = MongoClient(MONGODB_URI)
db = client["mit261"]

students_col = db["students"]
curriculum_col = db["curriculum"]
semesters_col = db["semesters"]
grades_col = db["grades"]

# delete first before inserting
grades_col.delete_many({"StudentID": {"$gte": 500001}})

# 1. Get all BSBA students
students = list(students_col.find({"Course": "BSBA"}))

# 2. Get BSBA subjects from curriculum
curriculum = curriculum_col.find_one({"programCode": "BSBA"})
subjects = [(sub["year"], sub["semester"], sub["code"]) for sub in curriculum["subjects"]]

# Derive base year from curriculumYear (e.g., "2025-2026" -> 2025)
base_year = int(curriculum["curriculumYear"].split("-")[0])

# 3. Build semester lookup {(Semester, SchoolYear): SemesterID}
semester_lookup = {}
for sem_doc in semesters_col.find({}).sort("_id", 1):
    semester_lookup[(sem_doc["Semester"], sem_doc["SchoolYear"])] = sem_doc["_id"]

# Teacher pool
teacher_pool = [
    "Prof. Marsha Bautista",
    "Prof. Ivy Ligoan",
    "Prof. Ramon Tan",
    "Prof. Olivia Ligoan",
    "Prof. Tony Lim"
]

# 4. Find the last _id in grades collection
last_record = grades_col.find_one(sort=[("_id", -1)])
last_id = last_record["_id"] if last_record else 0  # start from 0 if empty

grades_data = []
next_id = last_id + 1

# Group subjects per semester
for student in students:
    semesters_group = {}
    for year_level, sem, code in subjects:
        # Normalize semester names
        if sem == "First":
            sem_name = "FirstSem"
        elif sem == "Second":
            sem_name = "SecondSem"
        else:
            sem_name = sem  # e.g., "Summer"

        # Derive school year based on curriculum base year
        school_year = base_year + (year_level - 1)

        key = (sem_name, school_year)
        if key not in semester_lookup:
            raise ValueError(f"❌ Semester not found in lookup: {key}")

        sem_id = semester_lookup[key]

        if sem_id not in semesters_group:
            semesters_group[sem_id] = {
                "_id": next_id,
                "StudentID": student["_id"],
                "SubjectCodes": [],
                "Grades": [],
                "Teachers": [],
                "SemesterID": sem_id
            }
            next_id += 1

        semesters_group[sem_id]["SubjectCodes"].append(code)
        semesters_group[sem_id]["Grades"].append(random.randint(70, 95))
        semesters_group[sem_id]["Teachers"].append(random.choice(teacher_pool))

    grades_data.extend(semesters_group.values())

# Insert to grades collection
if grades_data:
    grades_col.insert_many(grades_data)
    print(f"✅ Inserted {len(grades_data)} grade records starting from ID {last_id + 1}")
else:
    print("⚠️ No students found to insert grades.")


# semesters collection:
# {
#   "_id": 16,
#   "Semester": "FirstSem",
#   "SchoolYear": 2025
# },
# {
#   "_id": 17,
#   "Semester": "SecondSem",
#   "SchoolYear": 2025
# },
# {
#   "_id": 18,
#   "Semester": "Summer",
#   "SchoolYear": 2025
# },


# {
#   "_id": 19,
#   "Semester": "FirstSem",
#   "SchoolYear": 2026
# },
# {
#   "_id": 20,
#   "Semester": "SecondSem",
#   "SchoolYear": 2026
# },
# {
#   "_id": 21,
#   "Semester": "Summer",
#   "SchoolYear": 2026
# },

# {
#   "_id": 22,
#   "Semester": "FirstSem",
#   "SchoolYear": 2027
# },
# {
#   "_id": 23,
#   "Semester": "SecondSem",
#   "SchoolYear": 2027
# },
# {
#   "_id": 24,
#   "Semester": "Summer",
#   "SchoolYear": 2027
# },

# {
#   "_id": 25,
#   "Semester": "FirstSem",
#   "SchoolYear": 2028
# },
# {
#   "_id": 26,
#   "Semester": "SecondSem",
#   "SchoolYear": 2028
# },
# {
#   "_id": 27,
#   "Semester": "Summer",
#   "SchoolYear": 2028
# }


# curriculum collection'

# {
#   "_id": {
#     "$oid": "68b6a4a4b4ad4b9a7a79e496"
#   },
#   "programCode": "BSBA",
#   "programName": "BACHELOR OF SCIENCE IN BUSINESS ADMINISTRATION",
#   "curriculumYear": "2025-2026",
#   "subjects": [
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "GE 200",
#       "name": "Understanding the Sell",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "GE 203",
#       "name": "Life and Works of Rizal",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "GE 204",
#       "name": "Gender and Society",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "GE 201",
#       "name": "Reading in Philippine History",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "GE 303",
#       "name": "Philippine Popular Culture",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "BACC 1",
#       "name": "Basic Microeconomics",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "PE 1",
#       "name": "Physical Activities Towards Health and Fitness 1 - Movement Competency Training",
#       "lec": 2,
#       "lab": 0,
#       "unit": 2,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "First",
#       "code": "NSTP 1",
#       "name": "Civic Welfare Training Services 1",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "GE 402",
#       "name": "Mathematics in the Modern World",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "GE 302",
#       "name": "Ethics",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "GE 403",
#       "name": "Science, Technology and Society",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "GE 301",
#       "name": "Arts Appreciation",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "GE 501",
#       "name": "Living in the IT Era",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "Mktg 1",
#       "name": "Principles of Marketing",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "PE 2",
#       "name": "Physical Activities Towards Health and Fitness 2 - Excercise-based Fitness Activities",
#       "lec": 2,
#       "lab": 0,
#       "unit": 2,
#       "preRequisites": [
#         "PE 1"
#       ]
#     },
#     {
#       "year": 1,
#       "semester": "Second",
#       "code": "NSTP 2",
#       "name": "Civic Welfare Training Services 2",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "NSTP 1"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "GE 104",
#       "name": "Purposive Communication",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "GE 102",
#       "name": "The Contemporary World",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "MM 1",
#       "name": "Marketing Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Mktg 1"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "MM 2",
#       "name": "Product Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Mktg 1"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "BACC 2",
#       "name": "International Business & Trade",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Mktg 1"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "ELEC 1",
#       "name": "E-Commerce & Internet Marketing",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Mktg 1"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "First",
#       "code": "PE 3",
#       "name": "Physical Activities Towards Health and Fitness 3 - Dance",
#       "lec": 2,
#       "lab": 0,
#       "unit": 2,
#       "preRequisites": [
#         "PE 1"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "ACCTG 11",
#       "name": "Fundamentals of Accounting 1",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "Math 201",
#       "name": "Business Statistics",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "GE 402"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "BACC 3",
#       "name": "Human Resource Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "BACC 4",
#       "name": "Business Law (Obligation and Contracts)",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "MM 3",
#       "name": "Distribution Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "MM 1",
#         "MM 2"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "MM 4",
#       "name": "Marketing Research",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "MM 1",
#         "MM 2"
#       ]
#     },
#     {
#       "year": 2,
#       "semester": "Second",
#       "code": "PE 4",
#       "name": "Physical Activities Towards Health and Fitness 4 - Sports",
#       "lec": 2,
#       "lab": 0,
#       "unit": 2,
#       "preRequisites": [
#         "PE 3"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "First",
#       "code": "Thesis 1",
#       "name": "Methods of Business Research Writing",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Math 201"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "First",
#       "code": "BACC 5",
#       "name": "Social Responsibility & Good Governance",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 3,
#       "semester": "First",
#       "code": "MM 5",
#       "name": "Advertising",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "ELEC 1"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "First",
#       "code": "MM 6",
#       "name": "Retail Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "MM 3"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "First",
#       "code": "BACC 6",
#       "name": "Income Taxation",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "ACCTG 11"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "Second",
#       "code": "Thesis 2",
#       "name": "Business Research",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Thesis 1"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "Second",
#       "code": "Math 202",
#       "name": "Qualitative Techniques in Business",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 3,
#       "semester": "Second",
#       "code": "ELEC 2",
#       "name": "Franchising",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "ELEC 1"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "Second",
#       "code": "MM 7",
#       "name": "Pricing Strategy",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "MM 4"
#       ]
#     },
#     {
#       "year": 3,
#       "semester": "Second",
#       "code": "CBMEC 1",
#       "name": "Operations Management (TQM)",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": []
#     },
#     {
#       "year": 4,
#       "semester": "First",
#       "code": "CBMEC 2",
#       "name": "Strategic Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "CBMEC 1"
#       ]
#     },
#     {
#       "year": 4,
#       "semester": "First",
#       "code": "BACC 7",
#       "name": "Feasibility Study",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "ACCTG 11"
#       ]
#     },
#     {
#       "year": 4,
#       "semester": "First",
#       "code": "MM 8",
#       "name": "Professional Salesmanship",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "Mktg 1"
#       ]
#     },
#     {
#       "year": 4,
#       "semester": "First",
#       "code": "ELEC 3",
#       "name": "Entrepreneurial Management",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "CBMEC 1"
#       ]
#     },
#     {
#       "year": 4,
#       "semester": "First",
#       "code": "ELEC 4",
#       "name": "New Market Development",
#       "lec": 3,
#       "lab": 0,
#       "unit": 3,
#       "preRequisites": [
#         "MM2"
#       ]
#     },
#     {
#       "year": 4,
#       "semester": "Second",
#       "code": "MM 9",
#       "name": "Internship / Work Integrated Learning (600 hrs)",
#       "lec": 6,
#       "lab": 0,
#       "unit": 6,
#       "preRequisites": [
#         "Graduating"
#       ]
#     }
#   ]
# }