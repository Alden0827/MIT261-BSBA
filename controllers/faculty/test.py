from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import pandas as pd
from typing import Dict, List, Any

def get_subjects_by_teacher(db: MongoClient, teacher_name: str) -> pd.DataFrame:
    """
    Retrieves and processes subject data for a specific teacher from a MongoDB database
    by using the 'grades' collection to link subjects and semesters.

    This function first finds all grade entries for a given teacher, then retrieves
    the associated subjects and semesters, and finally merges all the data into a
    single, coherent DataFrame.

    Args:
        db (MongoClient): The MongoDB database connection object.
        teacher_name (str): The name of the teacher to search for.

    Returns:
        pd.DataFrame: A pandas DataFrame containing the merged subject, semester,
                      and grade data, or an empty DataFrame if no subjects are found.
    """
    # 1. Find all grade entries for the specified teacher
    try:
        grades: List[Dict] = list(db.grades.find({"Teachers": teacher_name}))
    except Exception as e:
        print(f"Error querying grades collection: {e}")
        return pd.DataFrame()

    if not grades:
        print(f"No grade entries found for teacher: {teacher_name}")
        return pd.DataFrame()

    # 2. Extract unique subject codes and semester IDs from the grade entries
    all_subject_codes = set()
    all_semester_ids = set()
    for entry in grades:
        if "SubjectCodes" in entry:
            for code in entry["SubjectCodes"]:
                all_subject_codes.add(code)
        if "SemesterID" in entry:
            all_semester_ids.add(entry["SemesterID"])

    # 3. Fetch related subjects and semesters
    subjects: List[Dict] = list(db.subjects.find({"_id": {"$in": list(all_subject_codes)}}))
    semesters: List[Dict] = list(db.semesters.find({"_id": {"$in": list(all_semester_ids)}}))

    # 4. Create DataFrames and rename columns for merging
    grades_df = pd.DataFrame(grades)
    subjects_df = pd.DataFrame(subjects).rename(columns={"_id": "SubjectCodes"})
    semesters_df = pd.DataFrame(semesters).rename(columns={"_id": "SemesterID"})

    # Ensure all DataFrames have the necessary columns before merging
    for df, cols in [(grades_df, ["SubjectCodes", "SemesterID"]), (subjects_df, ["SubjectCodes"]), (semesters_df, ["SemesterID"])]:
        for col in cols:
            if col not in df.columns:
                df[col] = None

    # 5. Explode the grades DataFrame to handle multiple subjects/grades per entry
    grades_df = grades_df.explode(["SubjectCodes", "Grades", "Teachers", "Status"])
    
    # 6. Merge the DataFrames
    merged = pd.merge(grades_df, subjects_df, how="left", on="SubjectCodes")
    merged = pd.merge(merged, semesters_df, how="left", on="SemesterID")

    # 7. Build DisplayName safely using f-strings
    merged["DisplayName"] = merged.apply(
        lambda row: (
            f"{row.get('SubjectCodes', 'N/A')} - {row.get('Description', 'N/A')} "
            f"({row.get('Semester', 'N/A')}, {row.get('SchoolYear', 'N/A')})"
        ),
        axis=1
    )

    return merged

if __name__ == '__main__':
    # NOTE: In a production environment, store the connection URI and
    # credentials in a more secure way, e.g., environment variables.
    uri = "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261"
    
    client = None
    try:
        # Connect to MongoDB
        client = MongoClient(uri)
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ismaster')
        db = client['mit261']
        
        teacher_name = "Prof. Henry Dologuin"
        subjects_df = get_subjects_by_teacher(db, teacher_name)
        print(subjects_df.columns)
        
        if not subjects_df.empty:
            print(f"Subjects for {teacher_name}:")
            print(subjects_df[["DisplayName", "Grades", "Status"]])
        else:
            print("No data to display.")

    except ConnectionFailure as e:
        print(f"Could not connect to MongoDB: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if client:
            client.close()
            print("MongoDB connection closed.")
