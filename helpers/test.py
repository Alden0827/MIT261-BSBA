import sys
import pandas as pd
from pymongo import MongoClient

# -------------------------------------------------------------------
# MongoDB Connection
# -------------------------------------------------------------------
try:
    client = MongoClient("mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net")
    db = client['mit261']
    print("✅ Successfully connected to MongoDB!")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    sys.exit()

def get_academic_risks(semester_id, top_n=10):
    """
    Fetch BSBA students who are academically at risk based on semester grades.
    At risk = GPA < 60 OR no grades (INC).
    """

    # 🔹 Get all grades for this semester
    raw_grades = list(db.grades.find(
        {"SemesterID": semester_id},
        {"StudentID": 1, "Grades": 1}
    ))

    if not raw_grades:
        return pd.DataFrame()

    student_ids = [g["StudentID"] for g in raw_grades]

    # 🔹 Load corresponding students (filter to BSBA only)
    students = list(db.students.find(
        {"_id": {"$in": student_ids}, "Course": "BSBA"},
        {"_id": 1, "Name": 1, "Course": 1, "YearLevel": 1}
    ))


    if not students:
        return pd.DataFrame()

    students_df = pd.DataFrame(students)
    grades_map = {g["StudentID"]: g.get("Grades", []) for g in raw_grades}

    rows = []
    for _, stu in students_df.iterrows():
        sid = stu["_id"]
        grades = grades_map.get(sid, [])

        # Remove None values
        valid_grades = [g for g in grades if g is not None]

        # 🔹 INC (no grades at all)
        if not valid_grades:
            rows.append({
                "ID": sid,
                "Name": stu.get("Name"),
                "Prog": stu.get("Course"),
                "Yr": stu.get("YearLevel"),
                "Units": 0,
                "High": None,
                "Low": None,
                "GPA": None,
                "Risk": "INC"
            })
            continue

        units = len(valid_grades)
        cleaned_grades = [int(g) for g in valid_grades if str(g).isdigit()]

        high = max(cleaned_grades) if cleaned_grades else None
        low = min(cleaned_grades) if cleaned_grades else None
        gpa = sum(cleaned_grades) / len(cleaned_grades) if cleaned_grades else 0

        # 🔹 At risk if GPA < 60
        risk = "at risk (<60)" if (gpa < 60 and gpa > 0) else "INC"

        rows.append({
            "ID": sid,
            "Name": stu.get("Name"),
            "Prog": stu.get("Course"),
            "Yr": stu.get("YearLevel"),
            "Units": units,
            "High": high,
            "Low": low,
            "GPA": round(gpa, 2),
            "Remarks": risk
        })

    final_df = pd.DataFrame(rows)

    if final_df.empty:
        return pd.DataFrame()
    # 🔹 Keep only INC or GPA < 60
    final_df = final_df[(final_df["GPA"] < 60) | (final_df["GPA"] == 0 ) | (final_df["GPA"] == None)]

    # 🔹 Add rank
    final_df.index = range(1, len(final_df) + 1)
    final_df['#'] = final_df.index

    return final_df


# Example usage
a = get_academic_risks(semester_id=14)
print(a)
