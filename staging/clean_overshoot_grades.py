from pymongo import MongoClient

# Connect
uri = "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261"
client = MongoClient(uri)
db = client['mit261']

# Step 1: Find SemesterIDs for Second Semester 2025+
semester_ids = db.semesters.find({
    "Semester": {"$regex": "Second", "$options": "i"},
    "SchoolYear": {"$gte": 2025}
}, {"_id": 1})

semester_ids = [s["_id"] for s in semester_ids]

# Step 2: Clear grades, teachers, and subjects for those semesters
result = db.grades.update_many(
    {"SemesterID": {"$in": semester_ids}},
    {"$set": {
        "Grades": [],
        "Teachers": [],
        "SubjectCodes": []
    }}
)

print(f"Updated {result.modified_count} grade records.")
