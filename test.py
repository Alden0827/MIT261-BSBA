from pymongo import MongoClient
from config.settings import APP_TITLE, DEFAULT_PAGE_TITLE, MONGODB_URI, DB_NAME
import pandas as pd 

# Database connection
# client = MongoClient(MONGODB_URI)
client = MongoClient('mongodb://localhost:27017/')

db = client[DB_NAME]

def get_students_info(db, StudentID=None):
    """
    Returns a DataFrame of students with grades including these columns:
    ['_id', 'Name', 'Course', 'YearLevel']

    Column explanations:
    _id       → Student ID
    Name      → Student’s full name
    Course    → Course enrolled
    YearLevel → Year level of the student
    """
    pipeline = [
        {"$match": {"StudentID": StudentID} if StudentID else {}},
        {"$group": {"_id": "$StudentID"}},  # unique students with grades
        {
            "$lookup": {
                "from": "students",
                "localField": "_id",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},
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

    cursor = db.grades.aggregate(pipeline)
    df = pd.DataFrame(list(cursor))
    
    df.attrs['column_explanations'] = {
        "_id": "Student ID",
        "Name": "Student’s full name",
        "Course": "Course enrolled",
        "YearLevel": "Year level of the student"
    }
    
    return df

# Example usage
df = get_students_info(db, StudentID=500001)
print(df)
