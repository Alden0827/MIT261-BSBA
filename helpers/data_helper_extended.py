

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# -------------------- data_helper_extended.py --------------------

import os, time
import pandas as pd
from pymongo import MongoClient
from config.settings import MONGODB_URI, CACHE_MAX_AGE

client = MongoClient(MONGODB_URI)
max_age = 3600  # 1 hour cache

def load_or_query(cache_file: str, query_func) -> pd.DataFrame:
    """
    Load a DataFrame from cache or run a query function to fetch from MongoDB.
    
    Args:
        cache_file (str): Name of the pickle cache file.
        query_func (callable): Function that returns a pandas DataFrame.

    Returns:
        pd.DataFrame: The resulting DataFrame, either from cache or query.
    """
    cache_file = f"./cache/{cache_file}"
    if not os.path.exists("./cache"):
        os.makedirs("./cache")
    if os.path.exists(cache_file):
        file_age = time.time() - os.path.getmtime(cache_file)
        if file_age < CACHE_MAX_AGE:
            return pd.read_pickle(cache_file)

    df = query_func()
    if not df.empty:
        df.to_pickle(cache_file)
    return df

# -------------------- prospectus --------------------
def get_prospectus(studentId=None, programCode=None, curriculumYear=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve student prospectus records.
    
    Args:
        studentId (int, optional): Filter by student ID.
        programCode (str, optional): Filter by program code.
        curriculumYear (str, optional): Filter by curriculum year.
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame of prospectus documents.
    """
    cache_key = f"prospectus_{studentId}_{programCode}_{curriculumYear}"
    def query():
        db = client[MONGODB_DATABASE]
        col = db["prospectus"]
        filter_query = {}
        if studentId: filter_query["studentId"] = studentId
        if programCode: filter_query["programCode"] = programCode
        if curriculumYear: filter_query["curriculumYear"] = curriculumYear
        cursor = col.find(filter_query)
        return pd.DataFrame(list(cursor))[:limit]
    return load_or_query(cache_key, query)

# -------------------- faculty --------------------
def get_faculty(facultyName=None, department=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve faculty records.
    
    Args:
        facultyName (str, optional): Filter by faculty name (case-insensitive).
        department (str, optional): Filter by department name (case-insensitive).
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame of faculty documents.
    """
    cache_key = f"faculty_{facultyName}_{department}"
    def query():
        db = client[MONGODB_DATABASE]
        col = db["faculty"]
        filter_query = {}
        if facultyName:
            filter_query["facultyName"] = {"$regex": facultyName, "$options": "i"}
        if department:
            filter_query["department"] = {"$regex": department, "$options": "i"}
        cursor = col.find(filter_query)
        return pd.DataFrame(list(cursor))[:limit]
    return load_or_query(cache_key, query)

# -------------------- semester --------------------
def get_semester(schoolYear=None, term=None, status=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve semester records.
    
    Args:
        schoolYear (str, optional): Filter by school year.
        term (str, optional): Filter by term (e.g., "1st Semester").
        status (str, optional): Filter by status (OPEN, CLOSED, ONGOING, COMPLETED).
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame of semester documents.
    """
    cache_key = f"semester_{schoolYear}_{term}_{status}"
    def query():
        db = client[MONGODB_DATABASE]
        col = db["semester"]
        filter_query = {}
        if schoolYear: filter_query["schoolYear"] = schoolYear
        if term: filter_query["term"] = term
        if status: filter_query["status"] = status
        cursor = col.find(filter_query)
        return pd.DataFrame(list(cursor))[:limit]
    return load_or_query(cache_key, query)

# -------------------- classSchedule --------------------
def get_class_schedule(subjectId=None, facultyId=None, semesterId=None, section=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve class schedule records.
    
    Args:
        subjectId (int, optional): Filter by subject ID.
        facultyId (int, optional): Filter by faculty ID.
        semesterId (int, optional): Filter by semester ID.
        section (str, optional): Filter by section name (case-insensitive).
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame of class schedule documents.
    """
    cache_key = f"classSchedule_{subjectId}_{facultyId}_{semesterId}_{section}"
    def query():
        db = client[MONGODB_DATABASE]
        col = db["classSchedule"]
        filter_query = {}
        if subjectId: filter_query["subjectId"] = subjectId
        if facultyId: filter_query["facultyId"] = facultyId
        if semesterId: filter_query["semesterId"] = semesterId
        if section: filter_query["section"] = {"$regex": section, "$options": "i"}
        cursor = col.find(filter_query)
        return pd.DataFrame(list(cursor))[:limit]
    return load_or_query(cache_key, query)

# -------------------- enrollments --------------------
def get_enrollments(studentId=None, classOfferingId=None, status=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve enrollment records.
    
    Args:
        studentId (int, optional): Filter by student ID.
        classOfferingId (int, optional): Filter by class offering ID.
        status (str, optional): Filter by enrollment status (Enrolled, Dropped, Completed).
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame of enrollment documents.
    """
    cache_key = f"enrollments_{studentId}_{classOfferingId}_{status}"
    def query():
        db = client[MONGODB_DATABASE]
        col = db["enrollments"]
        filter_query = {}
        if studentId: filter_query["studentId"] = studentId
        if classOfferingId: filter_query["classOfferingId"] = classOfferingId
        if status: filter_query["status"] = status
        cursor = col.find(filter_query)
        return pd.DataFrame(list(cursor))[:limit]
    return load_or_query(cache_key, query)

def get_student_enrollments_with_info(studentId=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve enrollment records for a student, joined with class schedule, subject, faculty, and semester info.
    
    Args:
        studentId (int, optional): Filter by student ID.
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame with detailed student enrollment information.
    """
    cache_key = f"student_enrollments_info_{studentId}"
    def query():
        db = client[MONGODB_DATABASE]
        enroll_col = db["enrollments"]
        pipeline = []
        if studentId:
            pipeline.append({"$match": {"studentId": studentId}})
        pipeline.extend([
            {"$lookup": {"from": "classSchedule", "localField": "classOfferingId", "foreignField": "_id", "as": "class_info"}},
            {"$unwind": "$class_info"},
            {"$lookup": {"from": "subjects", "localField": "class_info.subjectId", "foreignField": "_id", "as": "subject_info"}},
            {"$unwind": "$subject_info"},
            {"$lookup": {"from": "faculty", "localField": "class_info.facultyId", "foreignField": "_id", "as": "faculty_info"}},
            {"$unwind": "$faculty_info"},
            {"$lookup": {"from": "semester", "localField": "class_info.semesterId", "foreignField": "_id", "as": "semester_info"}},
            {"$unwind": "$semester_info"},
            {"$project": {
                "_id": 0,
                "StudentID": "$studentId",
                "ClassOfferingID": "$classOfferingId",
                "Status": "$status",
                "Grade": "$grade",
                "Subject Code": "$subject_info._id",
                "Subject Description": "$subject_info.Description",
                "Units": "$subject_info.Units",
                "Faculty": "$faculty_info.facultyName",
                "Section": "$class_info.section",
                "Schedule": "$class_info.schedule",
                "Semester": "$semester_info.term",
                "SchoolYear": "$semester_info.schoolYear"
            }}
        ])
        if limit:
            pipeline.append({"$limit": limit})
        return pd.DataFrame(list(enroll_col.aggregate(pipeline, allowDiskUse=True)))
    return load_or_query(cache_key, query)

# -------------------- userAccounts --------------------
def get_user_accounts(role=None, linkedId=None, limit=1000) -> pd.DataFrame:
    """
    Retrieve user account records.
    
    Args:
        role (str, optional): Filter by role (student, faculty, registrar, admin).
        linkedId (int, optional): Filter by linked student or faculty ID.
        limit (int, optional): Maximum number of records to return.
    
    Returns:
        pd.DataFrame: DataFrame of user account documents.
    """
    cache_key = f"userAccounts_{role}_{linkedId}"
    def query():
        db = client[MONGODB_DATABASE]
        col = db["userAccounts"]
        filter_query = {}
        if role: filter_query["role"] = role
        if linkedId: filter_query["linkedId"] = linkedId
        cursor = col.find(filter_query)
        return pd.DataFrame(list(cursor))[:limit]
    return load_or_query(cache_key, query)


if __name__ == "__main__":
    print("🔍 Testing data_helper_extended functions...\n")

    try:
        print("Prospectus:")
        df = get_prospectus(limit=5)
        print(df.head(), "\n")

        print("Faculty:")
        df = get_faculty(limit=5)
        print(df.head(), "\n")

        print("Semester:")
        df = get_semester(limit=5)
        print(df.head(), "\n")

        print("Class Schedule:")
        df = get_class_schedule(limit=5)
        print(df.head(), "\n")

        print("Enrollments:")
        df = get_enrollments(limit=5)
        print(df.head(), "\n")

        print("Student Enrollments with Info:")
        df = get_student_enrollments_with_info(studentId=123, limit=5)
        print(df.head(), "\n")

        print("User Accounts:")
        df = get_user_accounts(limit=5)
        print(df.head(), "\n")

    except Exception as e:
        print("❌ Error while testing functions:", e)
