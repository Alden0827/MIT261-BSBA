import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from typing import Optional
import pandas as pd
from dotenv import load_dotenv
import pymongo
from pymongo import MongoClient
import time
import bcrypt
from config.settings import MONGODB_URI, CACHE_MAX_AGE
from helpers.cache_helper import cache_meta, load_or_query


pd.set_option('display.max_columns', None)

client = MongoClient(MONGODB_URI)

def student_find(query, collection, course=None, limit=10):
    """Search students by keywords in any order (case-insensitive). Optionally filter by course."""
    words = query.strip().split()
    regex_pattern = "".join(f"(?=.*{word})" for word in words) + ".*"
    regex_query = {"Name": {"$regex": regex_pattern, "$options": "i"}}

    # Filter by course if provided
    if course:
        regex_query["Course"] = course

    return list(collection.find(regex_query, {"Name": 1, "Course": 1, "YearLevel": 1}).limit(limit))

# def load_or_query(cache_file, query_func):
#     cache_file = f"./cache/{cache_file}"
#     """Load DataFrame from cache or run query function."""
#     if os.path.exists(cache_file):
#         file_age = time.time() - os.path.getmtime(cache_file)
#         if file_age < CACHE_MAX_AGE:
#             print('Load from cache!')
#             return pd.read_pickle(cache_file)


#     df = query_func()
#     if not df.empty:
#         df.to_pickle(cache_file)
#         pass
#     return df



# def fetch_students_bulk(
#     mongo_uri: str,
#     db_name: str,
#     collection_name: str,
#     batch_size: int = 5000,
#     query: Optional[dict] = None,
# ) -> pd.DataFrame:
#     """
#     Fetch documents from a MongoDB collection in batches and return as a single DataFrame.

#     Args:
#         mongo_uri (str): MongoDB connection URI.
#         db_name (str): Database name.
#         collection_name (str): Collection name.
#         batch_size (int): Number of documents per batch.
#         query (dict, optional): MongoDB filter query. Defaults to {}.

#     Returns:
#         pd.DataFrame: Consolidated DataFrame with all fetched documents.
#     """
#     client = MongoClient(mongo_uri)
#     collection = client[db_name][collection_name]

#     if query is None:
#         query = {}

#     total_docs = collection.count_documents(query)
#     all_data = []

#     print(f"Fetching {total_docs} documents in batches of {batch_size}...")

#     cursor = collection.find(query, batch_size=batch_size)
#     for i, doc in enumerate(cursor, 1):
#         all_data.append(doc)
#         if i % batch_size == 0 or i == total_docs:
#             print(f"Fetched {i}/{total_docs} documents...")

#     print("All documents fetched. Converting to DataFrame.")
#     df = pd.DataFrame(all_data)
#     return df


def get_students_collection(StudentID=None, limit=100000000):
    def query():
        db = client["mit261"]
        students_col = db["students"]

        query_filter = {"Course": "BSBA"}

        if StudentID:
            # Use direct match if single ID, or $in if list of IDs
            if isinstance(StudentID, list):
                query_filter["_id"] = {"$in": StudentID}
            else:
                query_filter["_id"] = StudentID

        cursor = students_col.find(
            query_filter,
            {"_id": 1, "Name": 1, "Course": 1, "YearLevel": 1}
        )

        if limit:
            cursor = cursor.limit(limit)

        return pd.DataFrame(list(cursor))

    return load_or_query("students_cache_x.pkl", query)

# def cache_meta(ttl=600000000):  # default no expiration
#     from functools import wraps
#     import hashlib
#     import pickle
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             print(f'-----------------------------------------------')
#             print(f'Func: {func.__name__}', end = '')

#             ttl_minutes = kwargs.pop('ttl', ttl)
#             args_tuple = tuple(arg for arg in args)
#             kwargs_tuple = tuple(sorted(kwargs.items()))
#             cache_key = hashlib.md5(pickle.dumps((args_tuple, kwargs_tuple))).hexdigest()
#             cache_name = f"./cache/{func.__name__}_{cache_key}.pkl"
#             os.makedirs("./cache/", exist_ok=True)
#             if os.path.exists(cache_name):
#                 file_mod_time = os.path.getmtime(cache_name)
#                 if (time.time() - file_mod_time) / 60 > ttl_minutes:
#                     os.remove(cache_name)
#                     result = func(*args, **kwargs)
#                 else:
#                     with open(cache_name, "rb") as f:
#                         result = pickle.load(f)
#                         print(' - from cache')
#                         return result 
#             else:
#                 result = func(*args, **kwargs)


#             with open(cache_name, "wb") as f:
#                 pickle.dump(result, f)

#             print(' - fresh')

#             return result
#         return wrapper
#     return decorator

@cache_meta(ttl=660000000) #60 minutes
def get_students(StudentID=None, limit=1000):
    # def query():
    db = client["mit261"]
    students_col = db["students"]
    grades_col = db["grades"]

    # Start pipeline from grades, since only students with grades matter
    pipeline = [
        {
            "$match": {  # filter by StudentID if provided
                **({"StudentID": StudentID} if StudentID else {})
            }
        },
        {"$group": {"_id": "$StudentID"}},  # unique students with grades
        {
            "$lookup": {  # join with students collection
                "from": "students",
                "localField": "_id",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},  # flatten student array
        {
            "$project": {
                "_id": "$student._id",
                "Name": "$student.Name",
                "Course": "$student.Course",
                "YearLevel": "$student.YearLevel"
            }
        },
        {"$sort": {"Name": 1}}
    ]

    if limit:
        pipeline.append({"$limit": limit})

    cursor = grades_col.aggregate(pipeline)  # NOTE: run on grades_col
    return pd.DataFrame(list(cursor))

def get_subjects(batch_size=1000):
    db = client["mit261"]
    collection = db["subjects"]

    cursor = collection.find({}, {"_id": 1, "Description": 1, "Units": 1, "Teacher": 1})

    docs, chunks = [], []
    for i, doc in enumerate(cursor, 1):
        docs.append(doc)
        if i % batch_size == 0:
            chunks.append(pd.DataFrame(docs))
            docs = []

    if docs:
        chunks.append(pd.DataFrame(docs))

    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    if not df.empty:
        df.rename(columns={"_id": "Subject Code"}, inplace=True)
        df["Subject Code"] = df["Subject Code"].astype(str)

    return df



@cache_meta(ttl=600000) #60 minutes
def get_semester_names():
    print('fetching semester from semesters collection as list')
    db = client["mit261"]
    collection = db["semesters"]
    return collection.distinct("Semester")

@cache_meta(ttl=600000) #60 minutes
def get_semesters(batch_size=1000):
    print('fetching semesters collection as DataFrame')
    db = client["mit261"]
    collection = db["semesters"]


    cursor = collection.find({}, {"_id": 1, "Semester": 1, "SchoolYear": 1})

    docs, chunks = [], []
    for i, doc in enumerate(cursor, 1):
        docs.append(doc)
        if i % batch_size == 0:
            chunks.append(pd.DataFrame(docs))
            docs = []

    if docs:
        chunks.append(pd.DataFrame(docs))

    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

@cache_meta(ttl=600000) #60 minutes
def get_school_years():
    db = client["mit261"]
    collection = db["semesters"]
    return collection.distinct("SchoolYear")


@cache_meta(ttl=600000) #60 minutes
def get_courses():
    db = client["mit261"]
    collection = db["students"]
    return collection.distinct("Course")


#     # return load_or_query("semesters_cache.pkl", query)

@cache_meta(ttl=600000) #60 minutes
def get_grades(batch_size=1000):
    db = client["mit261"]
    collection = db["grades"]

    print('Fetching data', end = '')
    cursor = collection.find(
        {},
        {"_id": 1, "StudentID": 1, "SubjectCodes": 1,
         "Grades": 1, "Teachers": 1, "SemesterID": 1}
    )

    docs, chunks = [], []
    for i, doc in enumerate(cursor, 1):
        docs.append(doc)
        if i % batch_size == 0:
            print('.',end = '')
            chunks.append(pd.DataFrame(docs))
            docs = []

    if docs:  # remaining docs
        chunks.append(pd.DataFrame(docs))

    return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

# # def get_grades():
# #     # def query():
# #     db = client["mit261"]
# #     collection = db["grades"]
# #     cursor = collection.find(
# #         {}, {"_id": 1, "StudentID": 1, "SubjectCodes": 1,
# #              "Grades": 1, "Teachers": 1, "SemesterID": 1}
# #     )
# #     return pd.DataFrame(list(cursor))

#     # return load_or_query("grades_cache.pkl", query)


# def get_student_grades_with_info(SubjectCode=None, Semester=None, SchoolYear=None, limit=1000):
#     """
#     Returns a DataFrame with columns:
#     ["StudentID", "Name", "Course", "YearLevel", "Grade", "Semester", "SchoolYear"]
#     'Grade' is the average per student.
#     """
#     cache_key = f"student_grades_info_{SubjectCode}_{Semester}_{SchoolYear}"

#     def query():
#         db = client["mit261"]
#         grades_col = db["grades"]

#         pipeline = [
#             {"$unwind": "$Grades"},
#             {"$unwind": "$SubjectCodes"},
#             {
#                 "$lookup": {
#                     "from": "students",
#                     "localField": "StudentID",
#                     "foreignField": "_id",
#                     "as": "student_info"
#                 }
#             },
#             {"$unwind": "$student_info"},
#             {
#                 "$lookup": {
#                     "from": "semesters",
#                     "localField": "SemesterID",
#                     "foreignField": "_id",
#                     "as": "semester_info"
#                 }
#             },
#             {"$unwind": "$semester_info"},
#         ]

#         # Optional filters
#         match_stage = {}
#         if SubjectCode:
#             match_stage["SubjectCodes"] = SubjectCode
#         if Semester:
#             match_stage["semester_info.Semester"] = Semester
#         if SchoolYear:
#             match_stage["semester_info.SchoolYear"] = SchoolYear
#         if match_stage:
#             pipeline.append({"$match": match_stage})

#         # Group by student to calculate average grade and keep semester info
#         pipeline.append({
#             "$group": {
#                 "_id": "$StudentID",
#                 "Name": {"$first": "$student_info.Name"},
#                 "Course": {"$first": "$student_info.Course"},
#                 "YearLevel": {"$first": "$student_info.YearLevel"},
#                 "Semester": {"$first": "$semester_info.Semester"},
#                 "SchoolYear": {"$first": "$semester_info.SchoolYear"},
#                 "AverageGrade": {"$avg": "$Grades"}
#             }
#         })

#         # Project final column names
#         pipeline.append({
#             "$project": {
#                 "StudentID": "$_id",
#                 "Name": 1,
#                 "Course": 1,
#                 "YearLevel": 1,
#                 "Semester": 1,
#                 "SchoolYear": 1,
#                 "Grade": "$AverageGrade",
#                 "_id": 0
#             }
#         })

#         # Limit results if needed
#         if limit:
#             pipeline.append({"$limit": limit})

#         return pd.DataFrame(list(grades_col.aggregate(pipeline, allowDiskUse=True)))

#     return load_or_query(cache_key, query)


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


def get_all_users():
    """
    Fetches all users from the userAccounts collection.
    """
    db = client["mit261"]
    users_collection = db["userAccounts"]
    # Exclude password hash for security
    return pd.DataFrame(list(users_collection.find({}, {"passwordHash": 0})))


def add_user(username, password, role, fullname):
    """
    Adds a new user to the userAccounts collection.
    Returns a tuple (success, message).
    """
    db = client["mit261"]
    users_collection = db["userAccounts"]

    # Check if user already exists
    if users_collection.find_one({"username": username}):
        return False, "User already exists."

    # Generate password hash
    password_hash = generate_password_hash(password)

    # Create new user document
    # For simplicity, UID is set to username. In a real-world scenario,
    # this should be a unique identifier.
    new_user = {
        "username": username,
        "passwordHash": password_hash,
        "role": role,
        "fullName": fullname,
        "UID": username
    }

    # Insert new user
    result = users_collection.insert_one(new_user)
    if result.inserted_id:
        return True, "User added successfully."
    else:
        return False, "Failed to add user."


def delete_user(username):
    """
    Deletes a user from the userAccounts collection.
    Returns a tuple (success, message).
    """
    db = client["mit261"]
    users_collection = db["userAccounts"]

    # Basic safeguard to prevent deleting a main admin account
    if username == 'admin':
        return False, "Cannot delete the primary admin user."

    result = users_collection.delete_one({"username": username})

    if result.deleted_count > 0:
        return True, "User deleted successfully."
    else:
        return False, "User not found or could not be deleted."


def update_user(username, fullname, role):
    """
    Updates a user's fullname and role.
    """
    db = client["mit261"]
    users_collection = db["userAccounts"]

    # Prevent role change for the primary admin
    if username == 'admin' and role != 'admin':
        return False, "Cannot change the role of the primary admin user."

    result = users_collection.update_one(
        {"username": username},
        {"$set": {"fullName": fullname, "role": role}}
    )

    if result.modified_count > 0:
        return True, "User updated successfully."

    return True, "No changes were made."


def change_password(username, new_password):
    """
    Changes a user's password.
    """
    db = client["mit261"]
    users_collection = db["userAccounts"]

    password_hash = generate_password_hash(new_password)
    result = users_collection.update_one(
        {"username": username},
        {"$set": {"passwordHash": password_hash}}
    )

    if result.modified_count > 0:
        return True, "Password updated successfully."
    else:
        return False, "User not found or password could not be updated."

# def generate_password_hash(password: str) -> bytes:
#     """
#     Generates a bcrypt hash for a given plain-text password.

#     Args:
#         password (str): The plain-text password to hash.

#     Returns:
#         bytes: The hashed password as bytes (compatible with verify_password).
#     """
#     password_bytes = password.encode('utf-8')
#     salt = bcrypt.gensalt()
#     hashed = bcrypt.hashpw(password_bytes, salt)
#     return hashed


def get_curriculum(program_code):
    """
    Returns the curriculum for a given program code.
    """
    def query():
        db = client["mit261"]
        curriculum_col = db["curriculum"]

        program_doc = curriculum_col.find_one({"programCode": program_code})

        if program_doc and "subjects" in program_doc:
            df = pd.DataFrame(program_doc["subjects"])
            # Rename columns to be consistent
            df.rename(columns={"code": "Subject Code", "name": "Description"}, inplace=True)
            return df
        else:
            return pd.DataFrame()

    # Define a cache key based on the program code
    cache_key = f"curriculum_{program_code}.pkl"
    return load_or_query(cache_key, query)


# ===============================
# TEST RUN
# ===============================
if __name__ == "__main__":

    
    # print( get_students_collection().head(1)) #   b'$2b$12$7gc.TcApIFGSEC3anIVHoufkm5L/vx.t0O5Vj8syaCAn7UOvW6Nyu'

    # print(get_students(StudentID=500001))
    # print(get_subjects())

    pass

