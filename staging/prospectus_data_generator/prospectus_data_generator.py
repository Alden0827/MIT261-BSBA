from pymongo import MongoClient
import json
import os, pickle
from pathlib import Path

# MongoDB connection
URI = "mongodb+srv://aldenroxy:N53wxkFIvbAJjZjc@cluster0.l7fdbmf.mongodb.net/mit261"
DB_NAME = "mit261"

# Cache directory
CACHE_DIR = Path("./cache")
CACHE_DIR.mkdir(exist_ok=True)


def _load_or_query(cache_file, query_fn, description: str, force_reload=False):
    """Helper to load from pickle or query MongoDB."""
    if cache_file.exists() and not force_reload:
        print(f"[CACHE] Using cached {description} from {cache_file}")
        with open(cache_file, "rb") as f:
            return pickle.load(f)

    print(f"[QUERY] Fetching {description} from MongoDB...")
    data = query_fn()
    with open(cache_file, "wb") as f:
        pickle.dump(data, f)
    print(f"[CACHE] Saved {description} to {cache_file}")
    return data


def list_courses(uri: str = URI, db_name: str = DB_NAME, force_reload: bool = False) -> list:
    """List all unique courses from the students collection."""
    client = MongoClient(uri)
    db = client[db_name]

    courses_cache = CACHE_DIR / "courses.pkl"

    courses = _load_or_query(
        courses_cache,
        lambda: sorted(db["students"].distinct("Course")),
        "course list",
        force_reload,
    )

    print(f"[INFO] Found {len(courses)} courses")
    for idx, c in enumerate(courses, 1):
        print(f"  {idx}. {c}")

    return courses


def generate_prospectus(course: str, uri: str = URI, db_name: str = DB_NAME, force_reload: bool = False) -> dict:
    """Generate a prospectus JSON for a given course (always rebuilt fresh)."""
    client = MongoClient(uri)
    db = client[db_name]

    # --- Cacheable resources ---
    students_cache = CACHE_DIR / f"students_{course.replace(' ', '_').lower()}.pkl"
    subjects_cache = CACHE_DIR / "subjects.pkl"
    semesters_cache = CACHE_DIR / "semesters.pkl"
    grades_cache = CACHE_DIR / f"grades_{course.replace(' ', '_').lower()}.pkl"

    # Students
    students = _load_or_query(
        students_cache,
        lambda: list(db["students"].find({"Course": {"$regex": f"^{course}$", "$options": "i"}})),
        f"students for course={course}",
        force_reload,
    )

    if not students:
        print(f"[ERROR] No students found for course '{course}'")
        return {"error": f"No students found for course '{course}'"}

    student_ids = [s["_id"] for s in students]
    program_name = students[0]["Course"]
    program_code = "".join([w[0].upper() for w in program_name.split()])
    print(f"[OK] Found {len(students)} students for {program_name} → code={program_code}")

    # Subjects
    subjects = _load_or_query(
        subjects_cache,
        lambda: {s["_id"]: s for s in db["subjects"].find()},
        "all subjects",
        force_reload,
    )

    # Semesters
    semesters = _load_or_query(
        semesters_cache,
        lambda: {s["_id"]: s for s in db["semesters"].find()},
        "all semesters",
        force_reload,
    )

    # Grades
    grades = _load_or_query(
        grades_cache,
        lambda: list(db["grades"].find({"StudentID": {"$in": student_ids}})),
        "grades for students",
        force_reload,
    )

    # --- Build prospectus fresh every run ---
    print("[INFO] Rebuilding prospectus JSON...")
    subjects_list = []

    school_year = "N/A"
    for g in grades:
        semester_doc = semesters.get(g["SemesterID"])
        if not semester_doc:
            print(f"  [WARN] Semester {g['SemesterID']} not found")
            continue

        semester_name = semester_doc.get("Semester", "Unknown")
        school_year = semester_doc.get("SchoolYear", "N/A")

        for code in g["SubjectCodes"]:
            subj = subjects.get(code)
            if subj:
                subj_entry = {
                    "year": students[0].get("YearLevel", "N/A"),
                    "semester": semester_name,
                    "code": subj["_id"],
                    "name": subj["Description"],
                    "lec": subj.get("Lec", subj.get("lec", 3)),
                    "lab": subj.get("Lab", subj.get("lab", 0)),
                    "unit": subj.get("Units", subj.get("unit", 3)),
                    "preRequisites": [],
                }
                subjects_list.append(subj_entry)
            else:
                print(f"  [WARN] Subject {code} not found in subjects collection")

    # Deduplicate
    seen = set()
    unique_subjects = []
    for subj in subjects_list:
        if subj["code"] not in seen:
            seen.add(subj["code"])
            unique_subjects.append(subj)

    output = {
        "programCode": program_code,
        "programName": program_name.upper(),
        "curriculumYear": f"{school_year}-{school_year+1}" if isinstance(school_year, int) else "N/A",
        "subjects": unique_subjects,
    }

    print("[DONE] Prospectus built successfully")
    print(json.dumps(output, indent=2))
    return output


def save_prospectus_to_db(prospectus: dict, uri: str = URI, db_name: str = DB_NAME):
    """Insert or update the prospectus into the curriculum collection."""
    client = MongoClient(uri)
    db = client[db_name]
    curriculum_col = db["curriculum"]

    filter_query = {
        "programCode": prospectus["programCode"],
        "curriculumYear": prospectus["curriculumYear"],
    }

    print(f"[DB] Checking if curriculum exists for {filter_query}...")
    existing = curriculum_col.find_one(filter_query)

    if existing:
        print("[DB] Curriculum exists → updating record...")
        curriculum_col.update_one(filter_query, {"$set": prospectus})
        print("[OK] Curriculum updated successfully.")
    else:
        print("[DB] Curriculum does not exist → inserting new record...")
        curriculum_col.insert_one(prospectus)
        print("[OK] Curriculum inserted successfully.")


if __name__ == "__main__":
    print("\n=== Available Courses ===")
    courses = list_courses(force_reload=False)

    print("\n=== Generate Prospectus ===")
    course_name = "Information Technology"
    prospectus = generate_prospectus(course_name, force_reload=False)

    print("\n=== Save Prospectus to Curriculum Collection ===")
    save_prospectus_to_db(prospectus)
