import matplotlib.pyplot as plt
from pymongo import MongoClient
from collections import defaultdict
import numpy as np
from functools import wraps
import os
import pandas as pd
import hashlib
import pickle
import time
from functools import wraps

print('Connecting to db..')
# ------------------------------
# MongoDB Connection
# ------------------------------
uri = "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261"
# client = MongoClient(uri)

# ------------------------------
# Mongodb timeout
# ------------------------------
client = MongoClient(
    uri,
    # serverSelectionTimeoutMS=30000,  # 5 seconds for server selection
    # connectTimeoutMS=30000,          # 5 seconds to establish connection
    # socketTimeoutMS=30000           # 10 seconds for queries
)

db = client["mit261"]

students_col = db["students"]
grades_col = db["grades"]
subjects_col = db["subjects"]
semesters_col = db["semesters"]

print('Connected to db..')


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


@cache_meta()
def load_all_data():
    students = {s["_id"]: s for s in students_col.find()} # {'Course':'BSBA'}
    semesters = {s["_id"]: s for s in semesters_col.find()}
    return students, semesters

print("Loading metadata!", end = '')
students, semesters = load_all_data()
print(" - Loaded!")


# ------------------------------
# Report Functions
# ------------------------------
# A. Student Performance Analytics
# @st.cache_data(ttl=None)
@cache_result()
def get_top_performers(school_year=None, semester=None):
    data = []
    for g in grades_col.find():
        student = students.get(g["StudentID"])
        sem = semesters.get(g["SemesterID"])
        if student and sem:
            # apply filters
            if school_year and sem["SchoolYear"] != school_year:
                continue
            if semester and sem["Semester"] != semester:
                continue

            data.append({
                "Student": student["Name"],
                "Course": student["Course"],
                "YearLevel": student["YearLevel"],
                "Semester": sem["Semester"],
                "SchoolYear": sem["SchoolYear"],
                "Average": avg(g["Grades"])
            })

    df = pd.DataFrame(data)
    if df.empty:
        return df
    return df.sort_values("Average", ascending=False).head(10)


@cache_result()
def get_failing_students(school_year=None, semester=None):
    data = []
    for g in grades_col.find():
        student = students.get(g["StudentID"])
        sem = semesters.get(g["SemesterID"])
        if student and sem:
            # 🔹 Apply filters if provided
            if school_year and sem["SchoolYear"] != school_year:
                continue
            if semester and sem["Semester"] != semester:
                continue

            # 🔹 Skip if student has no grades yet
            if not g.get("Grades") or len(g["Grades"]) == 0:
                continue

            fails = sum(1 for x in g["Grades"] if x < 75)
            if fails / len(g["Grades"]) > 0.3:  # more than 30% failing
                data.append({
                    "Student": student["Name"],
                    "Course": student["Course"],
                    "Semester": sem["Semester"],
                    "SchoolYear": sem["SchoolYear"],
                    "Failures": fails,
                    "Subjects Taken": len(g["Grades"]),
                    "Failure Rate": f"{fails/len(g['Grades']):.0%}"
                })

    df = pd.DataFrame(data)
    if df.empty:
        return df
    return df.sort_values("Failures", ascending=False)

@cache_result()
def get_students_with_improvement(selected_semester="All", selected_sy="All"):
    history = defaultdict(list)
    
    for g in grades_col.find():
        sem = semesters.get(g["SemesterID"])
        if not sem:
            continue
        
        # Apply filters
        if selected_sy != "All" and sem["SchoolYear"] != selected_sy:
            continue
        if selected_semester != "All" and sem["Semester"] != selected_semester:
            continue
        
        # Store SemesterID and average grade
        history[g["StudentID"]].append((g["SemesterID"], avg(g["Grades"])))
    
    improved = []
    for sid, records in history.items():
        records.sort(key=lambda x: x[0])  # Sort by SemesterID
        if len(records) > 1 and records[-1][1] > records[0][1]:
            student = students.get(sid)
            if student:
                latest_sem = semesters.get(records[-1][0])
                improved.append({
                    "Student": student["Name"],
                    "Initial Avg": records[0][1],
                    "Latest Avg": records[-1][1],
                    "Improvement": records[-1][1] - records[0][1],
                    "SchoolYear": latest_sem["SchoolYear"] if latest_sem else "",
                    "Semester": latest_sem["Semester"] if latest_sem else ""
                })
    return pd.DataFrame(improved).sort_values("Improvement", ascending=False)



@cache_result()
def get_distribution_of_grades(selected_semester="All", selected_sy="All"):
    data = []
    for g in grades_col.find():
        sem = semesters.get(g["SemesterID"])
        if not sem:
            continue

        # Apply filters
        if selected_sy != "All" and sem["SchoolYear"] != selected_sy:
            continue
        if selected_semester != "All" and sem["Semester"] != selected_semester:
            continue

        for grade in g["Grades"]:
            data.append({
                "Grade": grade,
                "Semester": sem["Semester"],
                "SchoolYear": sem["SchoolYear"]
            })

    return pd.DataFrame(data)  # <-- Return a DataFrame


# B. Subject and Teacher Analytics
@cache_result()
def get_hardest_subject(course=None, school_year=None):
    failures = defaultdict(lambda: [0, 0])  # fails, total

    for g in grades_col.find():
        student = students.get(g["StudentID"])
        sem = semesters.get(g["SemesterID"])

        if not student or not sem:
            continue

        # --- Apply filters ---
        if course and student.get("Course") != course:
            continue
        if school_year and sem.get("SchoolYear") != school_year:
            continue

        for subj, grade in zip(g["SubjectCodes"], g["Grades"]):
            failures[subj][1] += 1
            if grade < 75:
                failures[subj][0] += 1

    data = []
    for subj, (f, t) in failures.items():
        subj_info = subjects_col.find_one({"_id": subj})
        failure_rate = (f / t) if t > 0 else 0

        data.append({
            "Subject": subj,
            "Description": subj_info["Description"] if subj_info else "",
            "Failure Rate %": f"{failure_rate:.0%}",   # display
            "Failure Rate": float(failure_rate * 100), # numeric
            "Fails": f,
            "Total": t
        })


    df = pd.DataFrame(data)

    if df.empty:
        # st.info("No records found!")
        return pd.DataFrame()

    df["Failure Rate"] = pd.to_numeric(df["Failure Rate"], errors="coerce").astype(float)
    return df.sort_values("Failure Rate", ascending=False).reset_index(drop=True)


@cache_result()
def get_easiest_subjects(course=None, school_year=None):
    """
    Returns DataFrame with:
      - Subject
      - Description
      - High Grades (>=90)   -> formatted string like '23%'
      - High Rate            -> numeric percent (0-100) for plotting
      - Students
    Filters: course (Course name) and school_year (SchoolYear string)
    """
    success = defaultdict(lambda: [0, 0])  # success_count, total_count

    for g in grades_col.find():
        student = students.get(g["StudentID"])
        sem = semesters.get(g["SemesterID"])

        if not student or not sem:
            continue

        # Apply filters
        if course and student.get("Course") != course:
            continue
        if school_year and sem.get("SchoolYear") != school_year:
            continue

        for subj, grade in zip(g["SubjectCodes"], g["Grades"]):
            success[subj][1] += 1
            if grade >= 90:
                success[subj][0] += 1

    data = []
    for subj, (s, t) in success.items():
        subj_info = subjects_col.find_one({"_id": subj})
        high_rate = (s / t) if t > 0 else 0.0

        data.append({
            "Subject": subj,
            "Description": subj_info["Description"] if subj_info else "",
            "High Grades (>=90)": f"{high_rate:.0%}",   # for table display
            "High Rate": float(high_rate * 100),        # numeric percent for chart
            "Students": t
        })

    df = pd.DataFrame(data)
    
    # ensure numeric dtype for plotting
    if df.empty:
        # st.info("No records found.")
        return pd.DataFrame()
    df["High Rate"] = pd.to_numeric(df["High Rate"], errors="coerce").astype(float)

    return df.sort_values("High Rate", ascending=False).reset_index(drop=True)

@cache_result()
def get_avg_grades_per_teacher(school_year=None, semester=None):
    teacher_grades = defaultdict(list)
    
    query = {}
    if school_year:
        query["SchoolYear"] = school_year
    if semester:
        query["Semester"] = semester

    for g in grades_col.find(query):
        sem = g.get("Semester")
        year = g.get("SchoolYear")
        for teacher, grade in zip(g["Teachers"], g["Grades"]):
            teacher_grades[teacher].append(grade)

    data = []
    for teacher, grades in teacher_grades.items():
        avg_grade = sum(grades)/len(grades) if grades else 0
        data.append({
            "Teacher": teacher,
            "Average Grade": avg_grade,
            "Semester": semester if semester else "All",
            "SchoolYear": school_year if school_year else "All"
        })

    return pd.DataFrame(data).sort_values("Average Grade", ascending=False)

@cache_result()
def get_teachers_with_high_failures():
    teacher_fails = defaultdict(lambda: [0, 0])  # fails, total
    for g in grades_col.find():
        for teacher, grade in zip(g["Teachers"], g["Grades"]):
            teacher_fails[teacher][1] += 1
            if grade < 75:
                teacher_fails[teacher][0] += 1
    data = [
        {
            "Teacher": t,
            "Failures": f,
            "Total": t_count,
            "Failure Rate": round((f / t_count if t_count > 0 else 0)*100,2),
        }
        for t, (f, t_count) in teacher_fails.items()
    ]
    return pd.DataFrame(data).sort_values("Failure Rate", ascending=False)

# C. Course and Curriculum Insights
@cache_result()
def get_grade_trend_per_course():
    data = []
    for g in grades_col.find():
        student = students.get(g["StudentID"])
        sem = semesters.get(g["SemesterID"])
        if student and sem:
            data.append({
                "Course": student["Course"],
                "SchoolYear": sem["SchoolYear"],
                "Average": avg(g["Grades"])
            })

    df = pd.DataFrame(data)

    # --- Exclude zero averages ---
    df = df[df["Average"] != 0]

    # Group by course & school year and take the mean
    return df.groupby(["Course", "SchoolYear"])["Average"].mean().reset_index()


@cache_result()
def get_subject_load_intensity():
    data = []
    for g in grades_col.find():
        student = students.get(g["StudentID"])
        if student:
            data.append({"Course": student["Course"], "Load": len(g["SubjectCodes"])})
    df = pd.DataFrame(data)
    return df.groupby("Course")["Load"].mean().reset_index()

@cache_result()
def get_ge_vs_major():
    data = []
    for g in grades_col.find():
        for subj, grade in zip(g["SubjectCodes"], g["Grades"]):
            subj_type = "GE" if subj.startswith("GE") else "Major"
            data.append({"Type": subj_type, "Grade": grade})
    df = pd.DataFrame(data)
    return df.groupby("Type")["Grade"].mean().reset_index()

# D. Semester and Academic Year Analysis
@cache_result()
def get_lowest_gpa_semester():
    data = []
    for g in grades_col.find():
        sem = semesters.get(g["SemesterID"])
        if sem:
            data.append({"Semester": sem["Semester"], "SchoolYear": sem["SchoolYear"], "Avg": avg(g["Grades"])})
    df = pd.DataFrame(data)
    return df.groupby(["Semester","SchoolYear"])["Avg"].mean().reset_index().sort_values("Avg").head(1)

@cache_result()
def get_best_gpa_semester():
    df = get_lowest_gpa_semester()
    return df.sort_values("Avg", ascending=False).head(1)

@cache_result()
def get_grade_deviation_across_semesters():
    data = []
    for g in grades_col.find():
        sem = semesters.get(g["SemesterID"])
        if sem:
            for subj, grade in zip(g["SubjectCodes"], g["Grades"]):
                data.append({"Subject": subj, "Semester": sem["_id"], "Grade": grade})
    df = pd.DataFrame(data)
    return df.groupby("Subject")["Grade"].std().reset_index().rename(columns={"Grade":"StdDev"}).sort_values("StdDev", ascending=False)

# E. Student Demographics
@cache_result()
def get_year_level_distribution():
    df = pd.DataFrame(list(students_col.find()))
    return df["YearLevel"].value_counts().reset_index().rename(columns={"index":"YearLevel","YearLevel":"Count"})

@cache_result()
def get_student_count_per_course():
    df = pd.DataFrame(list(students_col.find()))
    return df["Course"].value_counts().reset_index().rename(columns={"index":"Course","Course":"Count"})

@cache_result()
def get_performance_by_year_level():
    data = []
    for g in grades_col.find():
        student = students.get(g["StudentID"])
        if student:
            data.append({"YearLevel": student["YearLevel"], "Average": avg(g["Grades"])})
    df = pd.DataFrame(data)
    return df.groupby("YearLevel")["Average"].mean().reset_index()

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
    data  = get_Schoolyear_options()
    print(data)

