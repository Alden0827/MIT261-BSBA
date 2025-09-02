import pandas as pd
from dotenv import load_dotenv
import os
import pymongo
from pymongo import MongoClient
import time
import bcrypt
from config.constants import MONGODB_URI


pd.set_option('display.max_columns', None)

client = MongoClient(MONGODB_URI)

max_age = 3600  # 1 hour


def load_or_query(cache_file, query_func):
    cache_file = f"./cache/{cache_file}"
    """Load DataFrame from cache or run query function."""
    if os.path.exists(cache_file):
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age < max_age:
            return pd.read_pickle(cache_file)

    df = query_func()
    if not df.empty:
        df.to_pickle(cache_file)
    return df


def get_students(StudentID=None, limit=100000000):
    def query():
        db = client["mit261"]
        students_col = db["students"]
        grades_col = db["grades"]

        # Get unique student IDs that have grades
        filter_ids = {}
        if StudentID:
            filter_ids["_id"] = StudentID

        student_ids_with_grades = grades_col.distinct("StudentID", filter=filter_ids)

        if not student_ids_with_grades:
            return pd.DataFrame(columns=["_id", "Name", "Course", "YearLevel"])

        # Fetch only students who have grades
        cursor = students_col.find(
            {"_id": {"$in": student_ids_with_grades}},
            {"_id": 1, "Name": 1, "Course": 1, "YearLevel": 1}
        ).sort("Name", 1)

        if limit:
            cursor = cursor.limit(limit)

        return pd.DataFrame(list(cursor))

    return load_or_query("students_cache.pkl", query)



def get_subjects():
    def query():
        db = client["mit261"]
        collection = db["subjects"]
        cursor = collection.find({}, {"_id": 1, "Description": 1, "Units": 1, "Teacher": 1})
        df = pd.DataFrame(list(cursor))
        if not df.empty:
            df.rename(columns={"_id": "Subject Code"}, inplace=True)
            df["Subject Code"] = df["Subject Code"].astype(str)
        return df

    return load_or_query("subjects_cache.pkl", query)


def get_semesters():
    def query():
        db = client["mit261"]
        collection = db["semesters"]
        cursor = collection.find({}, {"_id": 1, "Semester": 1, "SchoolYear": 1})
        return pd.DataFrame(list(cursor))

    return load_or_query("semesters_cache.pkl", query)


def get_grades():
    def query():
        db = client["mit261"]
        collection = db["grades"]
        cursor = collection.find(
            {}, {"_id": 1, "StudentID": 1, "SubjectCodes": 1,
                 "Grades": 1, "Teachers": 1, "SemesterID": 1}
        )
        return pd.DataFrame(list(cursor))

    return load_or_query("grades_cache.pkl", query)


def get_student_grades_with_info(SubjectCode=None, Semester=None, SchoolYear=None, limit=1000):
    """
    Returns a DataFrame with columns:
    ["StudentID", "Name", "Course", "YearLevel", "Grade", "Semester", "SchoolYear"]
    'Grade' is the average per student.
    """
    cache_key = f"student_grades_info_{SubjectCode}_{Semester}_{SchoolYear}"

    def query():
        db = client["mit261"]
        grades_col = db["grades"]

        pipeline = [
            {"$unwind": "$Grades"},
            {"$unwind": "$SubjectCodes"},
            {
                "$lookup": {
                    "from": "students",
                    "localField": "StudentID",
                    "foreignField": "_id",
                    "as": "student_info"
                }
            },
            {"$unwind": "$student_info"},
            {
                "$lookup": {
                    "from": "semesters",
                    "localField": "SemesterID",
                    "foreignField": "_id",
                    "as": "semester_info"
                }
            },
            {"$unwind": "$semester_info"},
        ]

        # Optional filters
        match_stage = {}
        if SubjectCode:
            match_stage["SubjectCodes"] = SubjectCode
        if Semester:
            match_stage["semester_info.Semester"] = Semester
        if SchoolYear:
            match_stage["semester_info.SchoolYear"] = SchoolYear
        if match_stage:
            pipeline.append({"$match": match_stage})

        # Group by student to calculate average grade and keep semester info
        pipeline.append({
            "$group": {
                "_id": "$StudentID",
                "Name": {"$first": "$student_info.Name"},
                "Course": {"$first": "$student_info.Course"},
                "YearLevel": {"$first": "$student_info.YearLevel"},
                "Semester": {"$first": "$semester_info.Semester"},
                "SchoolYear": {"$first": "$semester_info.SchoolYear"},
                "AverageGrade": {"$avg": "$Grades"}
            }
        })

        # Project final column names
        pipeline.append({
            "$project": {
                "StudentID": "$_id",
                "Name": 1,
                "Course": 1,
                "YearLevel": 1,
                "Semester": 1,
                "SchoolYear": 1,
                "Grade": "$AverageGrade",
                "_id": 0
            }
        })

        # Limit results if needed
        if limit:
            pipeline.append({"$limit": limit})

        return pd.DataFrame(list(grades_col.aggregate(pipeline, allowDiskUse=True)))

    return load_or_query(cache_key, query)


def get_student_subjects_grades(StudentID=None, limit=1000):
    """
    Returns all subjects and grades for a specific student with:
    ["Subject Code", "Description", "Grade", "Semester", "SchoolYear"]
    """
    cache_key = f"student_subjects_grades_{StudentID}"

    def query():
        db = client["mit261"]
        grades_col = db["grades"]

        if StudentID is not None:
            student_id = int(StudentID)  # convert to native Python int
        else:
            student_id = None

        pipeline = []

        if student_id is not None:
            pipeline.append({"$match": {"StudentID": student_id}})

        pipeline.extend([
            {"$project": {
                "SubjectsGrades": {"$zip": {"inputs": ["$SubjectCodes", "$Grades"]}},
                "SemesterID": 1
            }},
            {"$unwind": "$SubjectsGrades"},
            {"$project": {
                "SubjectCode": {"$arrayElemAt": ["$SubjectsGrades", 0]},
                "Grade": {"$arrayElemAt": ["$SubjectsGrades", 1]},
                "SemesterID": 1
            }},
            {"$lookup": {
                "from": "subjects",
                "localField": "SubjectCode",
                "foreignField": "_id",
                "as": "subject_info"
            }},
            {"$unwind": "$subject_info"},
            {"$lookup": {
                "from": "semesters",
                "localField": "SemesterID",
                "foreignField": "_id",
                "as": "semester_info"
            }},
            {"$unwind": "$semester_info"},
            {"$project": {
                "Subject Code": "$SubjectCode",
                "Description": "$subject_info.Description",
                "Grade": 1,
                "Semester": "$semester_info.Semester",
                "SchoolYear": "$semester_info.SchoolYear",
                "_id": 0
            }}
        ])

        if limit:
            pipeline.append({"$limit": limit})

        return pd.DataFrame(list(grades_col.aggregate(pipeline, allowDiskUse=True)))

    return load_or_query(cache_key, query)


def get_instructor_subjects(instructor_name=None, limit=1000):
    """
    Returns a DataFrame with columns:
    ["Teacher", "Subject Code", "Description", "Units"]
    
    If instructor_name is provided, it filters subjects where Teacher contains the string (case-insensitive).
    """
    cache_key = f"instructor_subjects_cache_{instructor_name if instructor_name else 'all'}.pkl"

    def query():
        db = client["mit261"]
        collection = db["subjects"]

        filter_query = {}
        if instructor_name:
            # Case-insensitive wildcard search
            filter_query["Teacher"] = {"$regex": instructor_name, "$options": "i"}

        cursor = collection.find(
            filter_query, 
            {"_id": 1, "Description": 1, "Units": 1, "Teacher": 1}
        ).sort("Teacher", 1)

        df = pd.DataFrame(list(cursor))
        if df.empty:
            return df

        df.rename(columns={"_id": "Subject Code"}, inplace=True)
        df["Subject Code"] = df["Subject Code"].astype(str)

        if limit:
            df = df.head(limit)

        return df

    return load_or_query(cache_key, query)



def get_user(username):
    """
    Fetches a user from the userAccounts collection.
    """
    db = client["mit261"]
    users_collection = db["userAccounts"]
    return users_collection.find_one({"username": username})

def verify_password(password, hashed_password):
    """
    Verifies a password against a hashed password.
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

def generate_password_hash(password: str) -> bytes:
    """
    Generates a bcrypt hash for a given plain-text password.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        bytes: The hashed password as bytes (compatible with verify_password).
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed

# ===============================
# TEST RUN
# ===============================
if __name__ == "__main__":

    
    print( generate_password_hash("1234")) #   b'$2b$12$7gc.TcApIFGSEC3anIVHoufkm5L/vx.t0O5Vj8syaCAn7UOvW6Nyu'
    print( generate_password_hash("12345")) #   b'$2b$12$cyfm3cRoTZRzg6SMeL3.n.B.RZDy0k77aXU.YxCKQw/OU1kdozRoi'

    

