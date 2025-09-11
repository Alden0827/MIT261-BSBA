import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import defaultdict
import numpy as np
import os
import pandas as pd
import hashlib
import pickle
import time
from functools import wraps
import statistics
from config.settings import MONGODB_URI, MONGODB_DATABASE

print('Connecting to db..', end = '')

# ------------------------------
# Mongodb Connection/timeout
# ------------------------------
client = MongoClient(
    MONGODB_URI,
    # serverSelectionTimeoutMS=30000,  # 5 seconds for server selection
    # connectTimeoutMS=30000,          # 5 seconds to establish connection
    # socketTimeoutMS=30000           # 10 seconds for queries
)

db = client[MONGODB_DATABASE]

students_col = db["students"]
grades_col = db["grades"]
subjects_col = db["subjects"]
semesters_col = db["semesters"]

print(' - success')


# # test connection
try:
    client.admin.command("ping")
    print("✅ Connected successfully")
except Exception as e:
    print("❌ Connection failed:", e)

# ------------------------------
# Helper Functions
# ------------------------------
print("Initializing load_all_data!")

def avg(lst):
    return sum(lst) / len(lst) if lst else 0

# ------------------------------
# Cache Decorator
# ------------------------------
def cache_result(ttl=600000000):  # default no expiration
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f'-----------------------------------------------')
            print(f'Func: {func.__name__}', end = '')

            ttl_minutes = kwargs.pop('ttl', ttl)
            args_tuple = tuple(arg for arg in args)
            kwargs_tuple = tuple(sorted(kwargs.items()))
            cache_key = hashlib.md5(pickle.dumps((args_tuple, kwargs_tuple))).hexdigest()
            cache_name = f"./cache/{func.__name__}_{cache_key}.pkl"
            os.makedirs("./cache/", exist_ok=True)
            if os.path.exists(cache_name):
                file_mod_time = os.path.getmtime(cache_name)
                if (time.time() - file_mod_time) / 60 > ttl_minutes:
                    os.remove(cache_name)
                    result = func(*args, **kwargs)
                else:
                    with open(cache_name, "rb") as f:
                        result = pickle.load(f)
                        print(' - from cache')
                        print(result.head(5))
                        return result 
            else:
                result = func(*args, **kwargs)

            with open(cache_name, "wb") as f:
                pickle.dump(result, f)

            print(' - fresh')
            print(result.head(5))

            return result
        return wrapper
    return decorator

def cache_meta(ttl=600000000):  # default no expiration
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            print(f'-----------------------------------------------')
            print(f'Func: {func.__name__}', end = '')

            ttl_minutes = kwargs.pop('ttl', ttl)
            args_tuple = tuple(arg for arg in args)
            kwargs_tuple = tuple(sorted(kwargs.items()))
            cache_key = hashlib.md5(pickle.dumps((args_tuple, kwargs_tuple))).hexdigest()
            cache_name = f"./cache/{func.__name__}_{cache_key}.pkl"
            os.makedirs("./cache/", exist_ok=True)
            if os.path.exists(cache_name):
                file_mod_time = os.path.getmtime(cache_name)
                if (time.time() - file_mod_time) / 60 > ttl_minutes:
                    os.remove(cache_name)
                    result = func(*args, **kwargs)
                else:
                    with open(cache_name, "rb") as f:
                        result = pickle.load(f)
                        print(' - from cache')
                        return result 
            else:
                result = func(*args, **kwargs)


            with open(cache_name, "wb") as f:
                pickle.dump(result, f)

            print(' - fresh')

            return result
        return wrapper
    return decorator


# @cache_meta()
def load_all_data():
    students = {s["_id"]: s for s in students_col.find()} # {'Course':'BSBA'}
    semesters = {s["_id"]: s for s in semesters_col.find()}
    # students = {s["_id"]: s for s in students_col.find({}, {"Course": 1, "Name": 1})}
    # semesters = {s["_id"]: s for s in semesters_col.find({}, {"Semester": 1, "SchoolYear": 1})}

    return students, semesters

print("Loading metadata!", end = '')
# students, semesters = load_all_data()
print(" - Loaded!")
# students = ['aaaa']
# semesters = ['semesters']
# aaa = students_col.find({}, {"Course": 1, "Name": 1})
# print(aaa)
# ------------------------------
# Report Functions
# ------------------------------
# A. Student Performance Analytics
# @st.cache_data(ttl=None)
@cache_result()
def get_top_performers(school_year=None, semester=None):
    pipeline = [
        # Join with semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},  # flatten array
        # Join with students
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},
        # Apply filters
        {
            "$match": {
                **({"sem.SchoolYear": school_year} if school_year else {}),
                **({"sem.Semester": semester} if semester else {})
            }
        },
        # Only include records with grades
        {
            "$match": {
                "Grades.0": {"$exists": True}  # ensures Grades array is not empty
            }
        },
        # Compute average grade
        {
            "$addFields": {
                "Average": {"$avg": "$Grades"}
            }
        },
        # Project only needed fields
        {
            "$project": {
                "_id": 0,
                "Student": "$student.Name",
                "Course": "$student.Course",
                "YearLevel": "$student.YearLevel",
                "Semester": "$sem.Semester",
                "SchoolYear": "$sem.SchoolYear",
                "Average": 1
            }
        },
        # Sort and limit
        {"$sort": {"Average": -1}},
        {"$limit": 10}
    ]

    result = list(grades_col.aggregate(pipeline))
    df = pd.DataFrame(result)
    return df

# def get_top_performers(school_year=None, semester=None):
#     # 🔹 Preload lookup dicts (better: do this once at startup, not inside function)

#     print("Preload lookup semesters")
#     semesters = {s["_id"]: s for s in db.semesters.find()}


#     print("Preload lookup students")
#     # students = {s["_id"]: s for s in db.students.find().limit(20)}
#     students = {
#         s["_id"]: {"Name": s.get("Name"), "Course": s.get("Course")}
#         for s in list(db.students.find({}, {"Name": 1, "Course": 1}).limit(100000))
#     }

#     print("Loading records")
#     data = []
#     for g in grades_col.find():
#         student = students.get(g["StudentID"])
#         sem = semesters.get(g["SemesterID"])

#         if not student or not sem:
#             continue

#         # 🔹 Apply filters
#         if school_year and sem.get("SchoolYear") != school_year:
#             continue
#         if semester and sem.get("Semester") != semester:
#             continue

#         grades = g.get("Grades", [])
#         if not grades:  # skip if no grades
#             continue

#         data.append({
#             "Student": student.get("Name"),
#             "Course": student.get("Course"),
#             "YearLevel": student.get("YearLevel"),
#             "Semester": sem.get("Semester"),
#             "SchoolYear": sem.get("SchoolYear"),
#             "Average": statistics.mean(grades)
#         })

#     df = pd.DataFrame(data)
#     if df.empty:
#         return df
#     return df.sort_values("Average", ascending=False).head(10)


@cache_result()
def get_failing_students(school_year=None, semester=None):
    # Convert numpy types to plain Python types
    if school_year is not None:
        school_year = int(school_year)  # ensure BSON-safe
    if semester is not None:
        semester = str(semester)        # ensure BSON-safe

    pipeline = [
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},
        {
            "$match": {
                **({"sem.SchoolYear": school_year} if school_year else {}),
                **({"sem.Semester": semester} if semester else {}),
                "Grades.0": {"$exists": True}
            }
        },
        {
            "$project": {
                "_id": 0,
                "Student": "$student.Name",
                "Course": "$student.Course",
                "Semester": "$sem.Semester",
                "SchoolYear": "$sem.SchoolYear",
                "Subjects Taken": {"$size": "$Grades"},
                "Failures": {
                    "$size": {
                        "$filter": {
                            "input": "$Grades",
                            "as": "g",
                            "cond": {"$lt": ["$$g", 75]}
                        }
                    }
                }
            }
        },
        {
            "$addFields": {
                "FailureRate": {
                    "$cond": [
                        {"$gt": ["$Subjects Taken", 0]},
                        {"$divide": ["$Failures", "$Subjects Taken"]},
                        0
                    ]
                }
            }
        },
        {"$match": {"FailureRate": {"$gt": 0.3}}},
        {"$sort": {"Failures": -1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    df = pd.DataFrame(result)

    if not df.empty:
        df["Failure Rate"] = (df["FailureRate"] * 100).round(0).astype(int).astype(str) + "%"
        df = df.drop(columns=["FailureRate"])

    return df


@cache_result()
def get_students_with_improvement(selected_semester="All", selected_sy="All"):
    match_stage = {"Grades.0": {"$exists": True}}  # skip students with no grades

    if selected_sy != "All":
        match_stage["sem.SchoolYear"] = int(selected_sy)  # ensure BSON-safe int
    if selected_semester != "All":
        match_stage["sem.Semester"] = str(selected_semester)

    pipeline = [
        # Join with semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},
        # Join with students
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},
        # Apply filters
        {"$match": match_stage},
        # Compute average grade per (student, semester)
        {
            "$project": {
                "_id": 0,
                "StudentID": "$StudentID",
                "Student": "$student.Name",
                "SchoolYear": "$sem.SchoolYear",
                "Semester": "$sem.Semester",
                "AvgGrade": {"$avg": "$Grades"}
            }
        },
        # Group all semesters for each student
        {
            "$group": {
                "_id": "$StudentID",
                "Student": {"$first": "$Student"},
                "history": {
                    "$push": {
                        "SchoolYear": "$SchoolYear",
                        "Semester": "$Semester",
                        "AvgGrade": "$AvgGrade"
                    }
                }
            }
        }
    ]

    results = list(grades_col.aggregate(pipeline))

    # Now handle improvement logic in Python (small dataset)
    improved = []
    for r in results:
        history = sorted(
            r["history"],
            key=lambda x: (x["SchoolYear"], x["Semester"])  # sort by SY + Semester
        )
        if len(history) > 1 and history[-1]["AvgGrade"] > history[0]["AvgGrade"]:
            improved.append({
                "Student": r["Student"],
                "Initial Avg": history[0]["AvgGrade"],
                "Latest Avg": history[-1]["AvgGrade"],
                "Improvement": history[-1]["AvgGrade"] - history[0]["AvgGrade"],
                "SchoolYear": history[-1]["SchoolYear"],
                "Semester": history[-1]["Semester"],
            })

    return pd.DataFrame(improved).sort_values("Improvement", ascending=False)


@cache_result()
def get_distribution_of_grades(selected_semester="All", selected_sy="All"):
    match_stage = {}
    if selected_sy != "All":
        match_stage["sem.SchoolYear"] = int(selected_sy)  # ensure safe int
    if selected_semester != "All":
        match_stage["sem.Semester"] = str(selected_semester)

    pipeline = [
        # Expand grades array -> one row per grade
        {"$unwind": "$Grades"},
        # Join with semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},
        # Apply filters (if any)
        {"$match": match_stage} if match_stage else {"$match": {}},
        # Project only needed fields
        {
            "$project": {
                "_id": 0,
                "Grade": "$Grades",
                "Semester": "$sem.Semester",
                "SchoolYear": "$sem.SchoolYear"
            }
        }
    ]

    result = list(grades_col.aggregate(pipeline))
    return pd.DataFrame(result)


# B. Subject and Teacher Analytics
@cache_result()
def get_hardest_subject(course=None, school_year=None):
    match_stage = {}
    if course:
        match_stage["student.Course"] = course
    if school_year:
        match_stage["sem.SchoolYear"] = int(school_year)

    pipeline = [
        # Join with semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},
        # Join with students
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},
        # Apply filters only if present
        *( [{"$match": match_stage}] if match_stage else [] ),
        # Unwind grades + subjects
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx"}},
        {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx2"}},
        {"$match": {"$expr": {"$eq": ["$idx", "$idx2"]}}},
        # Count fails + totals per subject
        {
            "$group": {
                "_id": "$SubjectCodes",
                "Fails": {"$sum": {"$cond": [{"$lt": ["$Grades", 75]}, 1, 0]}},
                "Total": {"$sum": 1}
            }
        },
        # Join with subjects
        {
            "$lookup": {
                "from": "subjects",
                "localField": "_id",
                "foreignField": "_id",
                "as": "subj"
            }
        },
        {"$unwind": {"path": "$subj", "preserveNullAndEmptyArrays": True}},
        # Compute failure rate
        {
            "$project": {
                "Subject": "$_id",
                "Description": "$subj.Description",
                "Fails": 1,
                "Total": 1,
                "Failure Rate": {
                    "$cond": [
                        {"$gt": ["$Total", 0]},
                        {"$multiply": [{"$divide": ["$Fails", "$Total"]}, 100]},
                        0
                    ]
                }
            }
        },
        {"$sort": {"Failure Rate": -1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    df = pd.DataFrame(result)

    if df.empty:
        return pd.DataFrame()

    df["Failure Rate %"] = df["Failure Rate"].round(0).astype(int).astype(str) + "%"
    return df.reset_index(drop=True)


@cache_result()
def get_easiest_subjects(course=None, school_year=None):
    """
    Returns DataFrame with:
      - Subject
      - Description
      - High Performers (>=90)
      - High Rate (% numeric 0–100)
      - Students (total)
    Filters: course, school_year
    """

    # Only add filters if provided
    match_stage = {}
    if course:
        match_stage["student.Course"] = course
    if school_year:
        match_stage["sem.SchoolYear"] = int(school_year)

    pipeline = [
        # Join semesters first
        {"$lookup": {
            "from": "semesters",
            "localField": "SemesterID",
            "foreignField": "_id",
            "as": "sem"
        }},
        {"$unwind": "$sem"},

        # Join students
        {"$lookup": {
            "from": "students",
            "localField": "StudentID",
            "foreignField": "_id",
            "as": "student"
        }},
        {"$unwind": "$student"},

        # Apply filters only if present
        *( [{"$match": match_stage}] if match_stage else [] ),

        # Unwind grades + subjects together
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx"}},
        {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx2"}},
        {"$match": {"$expr": {"$eq": ["$idx", "$idx2"]}}},

        # Group by subject
        {
            "$group": {
                "_id": "$SubjectCodes",
                "HighCount": {"$sum": {"$cond": [{"$gte": ["$Grades", 90]}, 1, 0]}},
                "Total": {"$sum": 1}
            }
        },

        # Lookup subject info
        {"$lookup": {
            "from": "subjects",
            "localField": "_id",
            "foreignField": "_id",
            "as": "subj"
        }},
        {"$unwind": {"path": "$subj", "preserveNullAndEmptyArrays": True}},

        # Compute high rate
        {"$project": {
            "Subject": "$_id",
            "Description": "$subj.Description",
            "High Performers": "$HighCount",
            "Students": "$Total",
            "High Rate": {
                "$cond": [
                    {"$gt": ["$Total", 0]},
                    {"$multiply": [{"$divide": ["$HighCount", "$Total"]}, 100]},
                    0
                ]
            }
        }},

        {"$sort": {"High Rate": -1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    df = pd.DataFrame(result)

    if df.empty:
        return pd.DataFrame()

    df["High Grades"] = df["High Rate"].round(0).astype(int).astype(str) + "%"
    return df.reset_index(drop=True)

@cache_result()
def get_avg_grades_per_teacher(school_year=None, semester=None):
    match_stage = {}
    if school_year:
        match_stage["sem.SchoolYear"] = int(school_year)
    if semester:
        match_stage["sem.Semester"] = semester

    pipeline = [
        # Join semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},

        # Apply filters only if provided
        *( [{"$match": match_stage}] if match_stage else [] ),

        # Unwind teachers and grades
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx"}},
        {"$unwind": {"path": "$Teachers", "includeArrayIndex": "idx2"}},

        # Make sure teacher and grade indices align
        {"$match": {"$expr": {"$eq": ["$idx", "$idx2"]}}},

        # Group by teacher
        {
            "$group": {
                "_id": "$Teachers",
                "Average Grade": {"$avg": "$Grades"},
                "Count": {"$sum": 1}
            }
        },
        {"$sort": {"Average Grade": -1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    df = pd.DataFrame(result)

    if df.empty:
        return pd.DataFrame()

    df = df.rename(columns={"_id": "Teacher"})
    df["Semester"] = semester if semester else "All"
    df["SchoolYear"] = school_year if school_year else "All"

    return df.reset_index(drop=True)

@cache_result()
def get_teachers_with_high_failures(school_year=None, semester=None):
    match_stage = {}
    if school_year:
        match_stage["sem.SchoolYear"] = int(school_year)
    if semester:
        match_stage["sem.Semester"] = semester

    pipeline = [
        # Join semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},

        # Apply filters (only if provided)
        *( [{"$match": match_stage}] if match_stage else [] ),

        # Unwind Grades and Teachers with indices
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx"}},
        {"$unwind": {"path": "$Teachers", "includeArrayIndex": "idx2"}},

        # Match teacher-grade pairs (same index)
        {"$match": {"$expr": {"$eq": ["$idx", "$idx2"]}}},

        # Group by teacher
        {
            "$group": {
                "_id": "$Teachers",
                "Total": {"$sum": 1},
                "Failures": {"$sum": {"$cond": [{"$lt": ["$Grades", 75]}, 1, 0]}}
            }
        },

        # Compute Failure Rate
        {
            "$project": {
                "Teacher": "$_id",
                "Total": 1,
                "Failures": 1,
                "Failure Rate": {
                    "$cond": [
                        {"$gt": ["$Total", 0]},
                        {"$round": [{"$multiply": [{"$divide": ["$Failures", "$Total"]}, 100]}, 2]},
                        0
                    ]
                }
            }
        },

        {"$sort": {"Failure Rate": -1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    df = pd.DataFrame(result)

    if df.empty:
        return pd.DataFrame()

    df["Semester"] = semester if semester else "All"
    df["SchoolYear"] = school_year if school_year else "All"

    return df.reset_index(drop=True)

# C. Course and Curriculum Insights
@cache_result()
def get_grade_trend_per_course():
    pipeline = [
        # Join with semesters
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},

        # Join with students
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},

        # Exclude records without grades
        {"$match": {"Grades.0": {"$exists": True}}},

        # Compute per-record average
        {
            "$project": {
                "Course": "$student.Course",
                "SchoolYear": "$sem.SchoolYear",
                "Average": {"$avg": "$Grades"}
            }
        },

        # Group by Course + SchoolYear
        {
            "$group": {
                "_id": {"Course": "$Course", "SchoolYear": "$SchoolYear"},
                "Average": {"$avg": "$Average"}
            }
        },

        # Reshape
        {
            "$project": {
                "Course": "$_id.Course",
                "SchoolYear": "$_id.SchoolYear",
                "Average": 1,
                "_id": 0
            }
        },

        # Sort for trends
        {"$sort": {"Course": 1, "SchoolYear": 1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    return pd.DataFrame(result)


# @cache_result()
def get_subject_load_intensity():
    pipeline = [
        # Join students
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},

        # Project course + subject load (array length of SubjectCodes)
        {
            "$project": {
                "Course": "$student.Course",
                "Load": {"$size": {"$ifNull": ["$SubjectCodes", []]}}
            }
        },

        # Group by course and compute average load
        {
            "$group": {
                "_id": "$Course",
                "Load": {"$avg": "$Load"}
            }
        },

        # Reshape result
        {
            "$project": {
                "Course": "$_id",
                "Load": 1,
                "_id": 0
            }
        },
        {"$sort": {"Course": 1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    return pd.DataFrame(result)


@cache_result()
def get_ge_vs_major(school_year=None):
    pipeline = [
        # Join semesters collection to get SchoolYear
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "semester"
            }
        },
        {"$unwind": "$semester"},
    ]

    # Optional filter
    if school_year:
        pipeline.append({"$match": {"semester.SchoolYear": school_year}})

    pipeline += [
        {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx1"}},
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx2"}},
        {"$match": {"$expr": {"$eq": ["$idx1", "$idx2"]}}},
        {
            "$project": {
                "SchoolYear": "$semester.SchoolYear",  # carry over
                "Type": {
                    "$cond": [
                        {"$regexMatch": {"input": "$SubjectCodes", "regex": "^GE"}},
                        "GE",
                        "Major"
                    ]
                },
                "Grade": {"$toDouble": "$Grades"}
            }
        },
        {
            "$group": {
                "_id": {
                    "SchoolYear": "$SchoolYear",
                    "Type": "$Type"
                },
                "Average": {"$avg": "$Grade"},
                "Count": {"$sum": 1}
            }
        },
        {
            "$project": {
                "SchoolYear": "$_id.SchoolYear",
                "Type": "$_id.Type",
                "Average": 1,
                "Count": 1,
                "_id": 0
            }
        },
        {"$sort": {"SchoolYear": 1, "Type": 1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    return pd.DataFrame(result)



# D. Semester and Academic Year Analysis
@cache_meta()
def get_lowest_gpa_semester():
    # Step 1: Find the semester with lowest GPA
    pipeline = [
        {
            "$project": {
                "SemesterID": 1,
                "Avg": {"$avg": "$Grades"}
            }
        },
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},
        {
            "$group": {
                "_id": {"SemesterID": "$SemesterID", "Semester": "$sem.Semester", "SchoolYear": "$sem.SchoolYear"},
                "Avg": {"$avg": "$Avg"}
            }
        },
        {"$sort": {"Avg": 1}},
        {"$limit": 1}
    ]

    lowest = list(grades_col.aggregate(pipeline))
    if not lowest:
        return pd.DataFrame()

    sem_id = lowest[0]["_id"]["SemesterID"]
    semester = lowest[0]["_id"]["Semester"]
    school_year = lowest[0]["_id"]["SchoolYear"]
    sem_avg = lowest[0]["Avg"]

    # Step 2: Compute GPA per subject in that semester
    pipeline_subjects = [
        {"$match": {"SemesterID": sem_id}},
        {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx"}},
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx2"}},
        {"$match": {"$expr": {"$eq": ["$idx", "$idx2"]}}},
        {
            "$group": {
                "_id": "$SubjectCodes",
                "GPA": {"$avg": "$Grades"},
                "Count": {"$sum": 1}
            }
        },
        {"$project": {"SubjectCode": "$_id", "GPA": 1, "Count": 1, "_id": 0}},
        {"$sort": {"GPA": 1}}
    ]

    subjects = list(grades_col.aggregate(pipeline_subjects))

    # Merge into a single DataFrame
    header = pd.DataFrame([{
        "Semester": semester,
        "SchoolYear": school_year,
        "SemesterGPA": sem_avg
    }])
    subjects_df = pd.DataFrame(subjects)

    return header, subjects_df


@cache_meta()
def get_best_gpa_semester():
    # Step 1: Find the semester with highest GPA
    pipeline = [
        {
            "$project": {
                "SemesterID": 1,
                "Avg": {"$avg": "$Grades"}
            }
        },
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},
        {
            "$group": {
                "_id": {"SemesterID": "$SemesterID", "Semester": "$sem.Semester", "SchoolYear": "$sem.SchoolYear"},
                "Avg": {"$avg": "$Avg"}
            }
        },
        {"$sort": {"Avg": -1}},   # ✅ sort descending for best GPA
        {"$limit": 1}
    ]

    best = list(grades_col.aggregate(pipeline))
    if not best:
        return pd.DataFrame(), pd.DataFrame()

    sem_id = best[0]["_id"]["SemesterID"]
    semester = best[0]["_id"]["Semester"]
    school_year = best[0]["_id"]["SchoolYear"]
    sem_avg = best[0]["Avg"]

    # Step 2: Compute GPA per subject in that semester
    pipeline_subjects = [
        {"$match": {"SemesterID": sem_id}},
        {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx"}},
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx2"}},
        {"$match": {"$expr": {"$eq": ["$idx", "$idx2"]}}},
        {
            "$group": {
                "_id": "$SubjectCodes",
                "GPA": {"$avg": "$Grades"},
                "Count": {"$sum": 1}
            }
        },
        {"$project": {"SubjectCode": "$_id", "GPA": 1, "Count": 1, "_id": 0}},
        {"$sort": {"GPA": -1}}   # ✅ sort subjects best → worst
    ]

    subjects = list(grades_col.aggregate(pipeline_subjects))

    # Merge into DataFrames
    header = pd.DataFrame([{
        "Semester": semester,
        "SchoolYear": school_year,
        "SemesterGPA": sem_avg
    }])
    subjects_df = pd.DataFrame(subjects)

    return header, subjects_df

@cache_result()
def get_grade_deviation_across_semesters():
    pipeline = [
        # Unwind subjects + grades together
        {"$unwind": {"path": "$SubjectCodes", "includeArrayIndex": "idx1"}},
        {"$unwind": {"path": "$Grades", "includeArrayIndex": "idx2"}},
        {"$match": {"$expr": {"$eq": ["$idx1", "$idx2"]}}},

        # Attach semester info (if needed later)
        {
            "$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "sem"
            }
        },
        {"$unwind": "$sem"},

        # Project only needed fields
        {
            "$project": {
                "Subject": "$SubjectCodes",
                "Semester": "$sem._id",
                "Grade": "$Grades"
            }
        },

        # Group by subject and collect all grades
        {
            "$group": {
                "_id": "$Subject",
                "Grades": {"$push": "$Grade"}
            }
        }
    ]

    result = list(grades_col.aggregate(pipeline))

    # Compute stats in Python
    data = []
    for r in result:
        grades = r["Grades"]
        if not grades:
            continue
        mean = float(pd.Series(grades).mean())
        stddev = float(pd.Series(grades).std())
        count = len(grades)
        data.append({
            "Subject": r["_id"],
            "Mean": mean,
            "StdDev": stddev,
            "Count": count
        })

    return pd.DataFrame(data).sort_values("StdDev", ascending=False).reset_index(drop=True)


# E. Student Demographics
@cache_result()
def get_year_level_distribution():
    pipeline = [
        {
            "$group": {
                "_id": "$YearLevel",  # Group by YearLevel
                "Count": {"$sum": 1}  # Count number of students per YearLevel
            }
        },
        {
            "$project": {
                "YearLevel": "$_id",
                "Count": 1,
                "_id": 0
            }
        },
        {
            "$sort": {"YearLevel": 1}  # Optional: sort by year level
        }
    ]

    result = list(students_col.aggregate(pipeline))
    df = pd.DataFrame(result)
    return df

@cache_result()
def get_student_count_per_course():
    pipeline = [
        {
            "$group": {
                "_id": "$Course",       # Group by Course
                "Count": {"$sum": 1}    # Count number of students per course
            }
        },
        {
            "$project": {
                "Course": "$_id",       # Rename _id to Course
                "Count": 1,
                "_id": 0
            }
        },
        {
            "$sort": {"Count": -1}      # Optional: sort by student count descending
        }
    ]

    result = list(students_col.aggregate(pipeline))
    df = pd.DataFrame(result)
    return df
    
@cache_result()
def get_performance_by_year_level():
    pipeline = [
        # Join with students collection
        {
            "$lookup": {
                "from": "students",
                "localField": "StudentID",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},

        # Compute average grade per student
        {
            "$project": {
                "YearLevel": "$student.YearLevel",
                "Average": {"$avg": "$Grades"}
            }
        },

        # Group by year level and average across students
        {
            "$group": {
                "_id": "$YearLevel",
                "Average": {"$avg": "$Average"}
            }
        },

        # Sort nicely
        {"$sort": {"_id": 1}}
    ]

    result = list(grades_col.aggregate(pipeline))
    return pd.DataFrame(result).rename(columns={"_id": "YearLevel"})

@cache_meta()
def get_Schoolyear_options():
    return db.semesters.distinct("SchoolYear")

@cache_meta()
def get_course_options():
    return db.students.distinct("Course")

@cache_meta()
def get_semester_options():
    return db.semesters.distinct("Semester")


if __name__ == "__main__":
    # from app import st
    data  = get_student_count_per_course()
    print(data)

