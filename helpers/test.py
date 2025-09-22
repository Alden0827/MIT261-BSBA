import sys
import pandas as pd
from pymongo import MongoClient

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------
try:
    client = MongoClient('mongodb://localhost:27017/')
    db = client['mit261m']
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()


def get_teachers(db, teacher=None):
    """
    Returns a list of teacher names from the subjects collection.
    
    :param teacher: Optional string to filter by a specific teacher
    :return: List of teacher names
    """
    query = {}
    if teacher:
        query['Teacher'] = teacher
    
    # Use distinct to get unique teacher names
    teacher_names = db.subjects.distinct("Teacher", filter=query)
    return teacher_names



# Example usage
# a = get_teachers(teacher='Leonor Rivera')
a = get_teachers()
print(a)
