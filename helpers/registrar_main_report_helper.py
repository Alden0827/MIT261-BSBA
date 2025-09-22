# helpers/report_helper.py
# optimization:
#    db.students.aggregate(pipeline, maxTimeMS=120000)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

# from pymongo import MongoClient
from functools import wraps
import hashlib
import pickle
import time
# from config.settings import MONGODB_URI
from helpers.cache_helper import cache_meta, load_checkpoint, save_checkpoint

CACHE_DIR = "./cache"


# ------------------------------
# MongoDB Connection
# ------------------------------
# def get_db(uri=MONGODB_URI):
#     client = MongoClient(uri)
#     db = client.get_database()
#     return db

# ------------------------------
# Student collection caching
# ------------------------------



class report_helper(object):
    def __init__(self, arg):
        super(report_helper, self).__init__()
        self.arg = arg
        self.db = arg["db"]
        

    # @cache_meta(ttl=1440)
    def get_students_batch_checkpoint(self,batch_size=1000, course=None, year_level=None):
        
        CACHE_DIR = "./cache"
        CHECKPOINT_FILE = os.path.join(CACHE_DIR, "students_checkpoint.pkl")

        # --- Load checkpoint ---
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, "rb") as f:
                checkpoint = pickle.load(f)
            start_index = checkpoint["last_index"]
            results = checkpoint["results"]
            print(f"Resuming from batch index {start_index}...")
        else:
            start_index, results = 0, []

        query = {}
        if course:
            query["Course"] = course
        if year_level:
            query["YearLevel"] = year_level

        student_ids = self.db.students.distinct("_id", query)

        # --- Process in batches ---
        for i in range(start_index, len(student_ids), batch_size):
            batch_ids = student_ids[i:i+batch_size]
            print(f"Caching students collection: {i+1} - {min(i+batch_size, len(student_ids))}")

            cursor = self.db.students.find(
                {"_id": {"$in": batch_ids}},
                {"_id": 1, "Name": 1, "Course": 1, "YearLevel": 1}
            )

            batch_df = pd.DataFrame(list(cursor))
            if not batch_df.empty:
                results.append(batch_df)

            # --- Save checkpoint ---
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(CHECKPOINT_FILE, "wb") as f:
                pickle.dump({"last_index": i + batch_size, "results": results}, f)

        if not results:
            return pd.DataFrame()

        # --- Merge all batches ---
        final_df = pd.concat(results, ignore_index=True)

        # --- Delete checkpoint after success ---
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        return final_df


    # ------------------------------
    # 1a. Dean's List
    # ------------------------------

    @cache_meta(ttl=1)
    def get_deans_list(self, batch_size=1000, top_n=10, course=None, year_level=None):
        print("Da 1")
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()

        student_ids = students_df["_id"].tolist()
        print("Da 2")

        # 🔹 Load checkpoint
        CHECKPOINT_FILE = os.path.join(CACHE_DIR, "deans_list_checkpoint.pkl")
        checkpoint = load_checkpoint(CHECKPOINT_FILE=CHECKPOINT_FILE)
        start_index = checkpoint.get("last_index", 0)
        results = []

        print(f"Resuming from batch index {start_index}...")

        for i in range(start_index, len(student_ids), batch_size):
            batch_ids = student_ids[i:i+batch_size]
            print(f"Processing {i+1} - {min(i+batch_size, len(student_ids))}")

            # --- Fetch students ---
            students = list(self.db.students.find(
                {"_id": {"$in": batch_ids}},
                {"_id": 1, "Name": 1, "Course": 1, "YearLevel": 1}
            ))

            # --- Fetch grades separately ---
            grades = list(self.db.grades.find(
                {"StudentID": {"$in": batch_ids}},
                {"StudentID": 1, "Grades": 1}
            ))

            # Build a map {StudentID: all_grades}
            grade_map = {}
            for g in grades:
                if "Grades" in g:
                    grade_map.setdefault(g["StudentID"], []).extend(g["Grades"])

            # --- Aggregate GPA per student ---
            for stu in students:
                all_grades = grade_map.get(stu["_id"], [])
                valid_grades = [int(x) for x in all_grades if str(x).strip().isdigit()]
                if not valid_grades:
                    continue

                results.append({
                    "ID": stu["_id"],
                    "Name": stu.get("Name"),
                    "Prog": stu.get("Course"),
                    "Yr": stu.get("YearLevel"),
                    "Units": len(valid_grades),
                    "High": max(valid_grades),
                    "Low": min(valid_grades),
                    "GPA": sum(valid_grades) / len(valid_grades)
                })

            # --- Save checkpoint after each batch ---
            save_checkpoint(
                last_index=i + batch_size,
                results={"last_index": i + batch_size},
                CHECKPOINT_FILE=CHECKPOINT_FILE
            )

        if not results:
            return pd.DataFrame()

        # Merge all results
        final_df = pd.DataFrame(results)

        # --- Dean’s List filter ---
        final_df = final_df[(final_df["Low"] >= 85) & (final_df["GPA"] >= 90)]

        # Sort + Top N
        final_df.sort_values(by="GPA", ascending=False, inplace=True)
        final_df = final_df.head(top_n)

        # Add rank column
        final_df.index = range(1, len(final_df)+1)
        final_df["#"] = final_df.index

        # 🔹 Delete checkpoint after success
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        return final_df




    # ------------------------------
    # 1b. Academic Probation
    # ------------------------------
    @cache_meta(ttl=1440)
    def get_academic_probation_batch_checkpoint(self,batch_size=10000, top_n=10, course=None, year_level=None):
        CHECKPOINT_FILE = os.path.join(CACHE_DIR, "get_academic_probation_batch_checkpoint.pkl")
        

        # 🔹 Load all students (cached)
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()

        student_ids = students_df["_id"].tolist()

        # 🔹 Load checkpoint if exists
        checkpoint = load_checkpoint(CHECKPOINT_FILE=CHECKPOINT_FILE)
        start_index = checkpoint["last_index"]
        results = checkpoint["results"]



        print(f"Resuming Academic Probation from batch index {start_index}...")

        for i in range(start_index, len(student_ids), batch_size):
            batch_ids = student_ids[i:i+batch_size]
            print(f"Processing students {i+1} - {min(i+batch_size, len(student_ids))}")

            # 🔹 Fetch students in this batch
            batch_students = students_df[students_df["_id"].isin(batch_ids)]

            # 🔹 Fetch grades separately (no aggregation)
            raw_grades = list(self.db.grades.find({"StudentID": {"$in": batch_ids}}, {
                "StudentID": 1,
                "Grades": 1
            }))

            # Map grades by StudentID for quick lookup
            grades_map = {}
            for g in raw_grades:
                grades_map.setdefault(g["StudentID"], []).extend(g.get("Grades", []))

            rows = []
            for _, stu in batch_students.iterrows():
                sid = stu["_id"]
                grades = grades_map.get(sid, [])

                # ✅ Clean: keep only digits, drop '' and None
                valid_grades = [int(x) for x in grades if str(x).strip().isdigit()]
                if not valid_grades:
                    continue  # skip students with no valid grades

                # print("DEBUG g:", valid_grades, type(valid_grades))
                print(f"   → Checking {stu.get('Name', 'Unknown')} ({sid})")

                units = len(valid_grades)
                high = max(valid_grades)
                low = min(valid_grades)
                gpa = sum(valid_grades) / units if units else 0

                fail_percent = (len([x for x in valid_grades if x < 75]) / units) * 100 if units else 0

                if low < 75 or fail_percent >= 30:
                    rows.append({
                        "ID": sid,
                        "Name": stu.get("Name"),
                        "Prog": stu.get("Course"),
                        "Yr": stu.get("YearLevel"),
                        "Units": units,
                        "High": high,
                        "Low": low,
                        "GPA": round(gpa, 2),
                        "Fail%": round(fail_percent, 2)
                    })



            if rows:
                batch_df = pd.DataFrame(rows)
                results.append(batch_df)

            # 🔹 Save checkpoint after each batch
            save_checkpoint(last_index=i + batch_size, results=results,CHECKPOINT_FILE=CHECKPOINT_FILE)

        if not results:
            return pd.DataFrame()

        # Merge
        final_df = pd.concat(results, ignore_index=True)

        # Sort by GPA ascending (worst first)
        final_df.sort_values(by="GPA", ascending=True, inplace=True)

        # Take top_n
        final_df = final_df.head(top_n)

        # Add rank
        final_df.index = range(1, len(final_df)+1)
        final_df['#'] = final_df.index

        # Clean up checkpoint
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        return final_df


    # ------------------------------
    # 2. Subject Pass/Fail Distribution
    # ------------------------------
    @cache_meta()
    def get_subject_pass_fail(self, course=None, year_level=None):
        
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()
        student_ids = students_df["_id"].tolist()

        # 🔹 Load required collections
        grades = list(self.db.grades.find({"StudentID": {"$in": student_ids}}, {"SubjectCodes": 1, "Grades": 1, "SemesterID": 1}))
        subjects = pd.DataFrame(list(self.db.subjects.find({}, {"_id": 1, "Description": 1})))
        semesters = pd.DataFrame(list(self.db.semesters.find({}, {"_id": 1, "Semester": 1})))

        if not grades or subjects.empty or semesters.empty:
            return pd.DataFrame()

        # 🔹 Flatten grades
        rows = []
        for g in grades:
            subject_codes = g.get("SubjectCodes", [])
            subject_grades = g.get("Grades", [])
            semester_id = g.get("SemesterID")

            for code, grade in zip(subject_codes, subject_grades):
                rows.append({
                    "Subject Code": code,
                    "Grade": grade,
                    "SemesterID": semester_id
                })

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # 🔹 Merge subject descriptions
        subjects.rename(columns={"_id": "Subject Code", "Description": "Subject Name"}, inplace=True)
        df = df.merge(subjects, on="Subject Code", how="left")

        # 🔹 Merge semester names
        semesters.rename(columns={"_id": "SemesterID"}, inplace=True)
        df = df.merge(semesters, on="SemesterID", how="left")

        # 🔹 Compute pass/fail counts per subject + semester
        summary = (
            df.groupby(["Subject Code", "Subject Name", "Semester"])
              .agg(
                  **{
                      "Pass Count": ("Grade", lambda x: (x >= 75).sum()),
                      "Fail Count": ("Grade", lambda x: (x < 75).sum())
                  }
              )
              .reset_index()
        )

        # 🔹 Compute percentages
        summary["Total"] = summary["Pass Count"] + summary["Fail Count"]
        summary["Pass %"] = ((summary["Pass Count"] / summary["Total"]) * 100).round(2)
        summary["Fail %"] = ((summary["Fail Count"] / summary["Total"]) * 100).round(2)
        summary.drop(columns=["Total"], inplace=True)

        return summary



    # ------------------------------
    # 3. Enrollment trend An analysis
    # ------------------------------

    def get_enrollment_trend(self,batch_size=1000, course=None, year_level=None):
        
        CACHE_DIR = "./cache"
        CHECKPOINT_FILE = os.path.join(CACHE_DIR, "enrollment_trend_checkpoint.pkl")

        # --- Load checkpoint ---
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, "rb") as f:
                checkpoint = pickle.load(f)
            start_index = checkpoint["last_index"]
            results = checkpoint["results"]
            print(f"Resuming enrollment trend from index {start_index}...")
        else:
            start_index, results = 0, []

        # Load all students (with batching)
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()
        student_ids = students_df["_id"].tolist()

        # Load all grades
        grades_cursor = self.db.grades.find(
            {"StudentID": {"$in": student_ids}},
            {"StudentID": 1, "SemesterID": 1}
        )
        grades_df = pd.DataFrame(list(grades_cursor))
        if grades_df.empty:
            return pd.DataFrame()

        # Map SemesterID -> "Semester Year"
        sem_ids = grades_df["SemesterID"].unique().tolist()
        sem_map = {
            s["_id"]: f"{s['Semester']} {s['SchoolYear']}"
            for s in self.db.semesters.find(
                {"_id": {"$in": sem_ids}}, {"Semester": 1, "SchoolYear": 1}
            )
        }
        grades_df["Semester"] = grades_df["SemesterID"].map(sem_map)

        # --- Process by semester ---
        summary = []
        semesters_ordered = sorted(grades_df["Semester"].unique())
        prev_students = set()
        for sem in semesters_ordered:
            sem_students = set(grades_df.loc[grades_df["Semester"] == sem, "StudentID"])
            new_enrollees = sem_students - prev_students
            dropouts = prev_students - sem_students
            total = len(sem_students)
            retained = total - len(new_enrollees)
            retention_rate = (retained / total * 100) if total else 0

            summary.append({
                "Semester": sem,
                "Total Enrollment": total,
                "New Enrollees": len(new_enrollees),
                "Dropouts": len(dropouts),
                "Retention Rate (%)": round(retention_rate, 2)
            })
            prev_students = sem_students

        # --- Delete checkpoint ---
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        return pd.DataFrame(summary)


    # ------------------------------
    # 4. Incomplete Grades Report
    # ------------------------------

    @cache_meta()
    def get_incomplete_grades(self, course=None, year_level=None):
        
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()
        student_ids = students_df["_id"].tolist()

        # 🔹 Load collections
        grades = list(self.db.grades.find({"StudentID": {"$in": student_ids}}, {"StudentID": 1, "SubjectCodes": 1, "Grades": 1, "SemesterID": 1, "Status": 1}))
        subjects = pd.DataFrame(list(self.db.subjects.find({}, {"_id": 1, "Description": 1})))
        semesters = pd.DataFrame(list(self.db.semesters.find({}, {"_id": 1, "Semester": 1})))

        if not grades or subjects.empty or semesters.empty:
            return pd.DataFrame()

        # 🔹 Flatten grades (expand arrays)
        rows = []
        for g in grades:
            student_id = g.get("StudentID")
            semester_id = g.get("SemesterID")
            subject_codes = g.get("SubjectCodes", [])
            subject_grades = g.get("Grades", [])
            subject_status = g.get("Status", [])

            for code, grade, status in zip(subject_codes, subject_grades, subject_status):
                if status in ["INC", "Dropped"]:
                    rows.append({
                        "Student ID": student_id,
                        "Course Code": code,
                        "Grade": grade,
                        "SemesterID": semester_id,
                        "Status": status  # ✅ use the Status field
                    })

        df = pd.DataFrame(rows)
        if df.empty:
            return df

        # 🔹 Merge student info
        students_df.rename(columns={"_id": "Student ID"}, inplace=True)
        df = df.merge(students_df, on="Student ID", how="left")

        # 🔹 Merge subject info
        subjects.rename(columns={"_id": "Course Code", "Description": "Course Title"}, inplace=True)
        df = df.merge(subjects, on="Course Code", how="left")

        # 🔹 Merge semester info
        semesters.rename(columns={"_id": "SemesterID", "Semester": "Term"}, inplace=True)
        df = df.merge(semesters, on="SemesterID", how="left")

        # 🔹 Final cleanup
        df = df[["Student ID", "Name", "Course Code", "Course Title", "Term", "Grade", "Status"]]
        df = df[df["Term"].notna()] #term should not be advanced


        return df

    # ------------------------------
    # 5. Retention and Dropout Rates (continued)
    # ------------------------------

    # @cache_meta()
    # def get_retention_rates(self, batch_size=1000, course=None, year_level=None):
    #     CHECKPOINT_FILE = os.path.join(CACHE_DIR, "retention_checkpoint.pkl")

    #     # --- Load checkpoint ---
    #     if os.path.exists(CHECKPOINT_FILE):
    #         with open(CHECKPOINT_FILE, "rb") as f:
    #             checkpoint = pickle.load(f)
    #         start_index = checkpoint["last_index"]
    #         results = checkpoint["results"]
    #         print(f"Resuming retention from index {start_index}...")
    #     else:
    #         start_index, results = 0, []

    #     students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
    #     if students_df.empty:
    #         return pd.DataFrame()
    #     student_ids = students_df["_id"].tolist()

    #     # --- Process students in batches ---
    #     for i in range(start_index, len(student_ids), batch_size):
    #         batch_ids = student_ids[i:i + batch_size]
    #         print(f"Processing retention for students {i + 1}-{min(i + batch_size, len(student_ids))}")

    #         grades_cursor = self.db.grades.find(
    #             {"StudentID": {"$in": batch_ids}},
    #             {"StudentID": 1, "SemesterID": 1}
    #         )

    #         grades_df = pd.DataFrame(list(grades_cursor))
    #         if grades_df.empty:
    #             continue

    #         # --- Map SemesterID → formatted string
    #         sem_ids = grades_df["SemesterID"].unique().tolist()
    #         sem_map = {
    #             s["_id"]: f"{s['Semester']} {s['SchoolYear']}"
    #             for s in self.db.semesters.find(
    #                 {"_id": {"$in": sem_ids}},
    #                 {"Semester": 1, "SchoolYear": 1}
    #             )
    #         }
    #         grades_df["Semester"] = grades_df["SemesterID"].map(sem_map)
    #         results.append(grades_df)

    #         # --- Save checkpoint ---
    #         os.makedirs(CACHE_DIR, exist_ok=True)
    #         with open(CHECKPOINT_FILE, "wb") as f:
    #             pickle.dump({"last_index": i + batch_size, "results": results}, f)

    #     if not results:
    #         return pd.DataFrame()

    #     df = pd.concat(results, ignore_index=True)

    #     # --- Load all semesters for ordering ---
    #     all_semesters = list(self.db.semesters.find({}, {"_id": 1, "Semester": 1, "SchoolYear": 1}))
    #     sem_df = pd.DataFrame(all_semesters)
    #     sem_df["SemesterLabel"] = sem_df["Semester"] + " " + sem_df["SchoolYear"].astype(str)

    #     # Create ordering index from semesters collection
    #     sem_df = sem_df.sort_values(by="_id")
    #     sem_df["SemesterIndex"] = range(len(sem_df))

    #     sem_map = dict(zip(sem_df["_id"], sem_df["SemesterLabel"]))
    #     idx_map = dict(zip(sem_df["_id"], sem_df["SemesterIndex"]))

    #     # Map Semester and SemesterIndex into df
    #     df["Semester"] = df["SemesterID"].map(sem_map)
    #     df["SemesterIndex"] = df["SemesterID"].map(idx_map)

    #     # --- Sort by student & semester ---
    #     df.sort_values(by=["StudentID", "SemesterIndex"], inplace=True)

    #     # --- Retention logic ---
    #     # Shift still useful to see next enrollment
    #     df["Next_SemIndex"] = df.groupby("StudentID")["SemesterIndex"].shift(-1)

    #     # Retained = has ANY later semester
    #     df["Retained"] = (df["Next_SemIndex"].notnull()).astype(int)
    #     df.loc[
    #         (df["Next_SemIndex"].notnull()) &
    #         (df["Next_SemIndex"] == df["SemesterIndex"] + 1),
    #         "Retained"
    #     ] = 1

    #     # --- Force dropout if student has no next semester but it's not the global last semester ---
    #     max_sem_index = df["SemesterIndex"].max()
    #     df["Dropped"] = 0
    #     df.loc[(df["Next_SemIndex"].isnull()) & (df["SemesterIndex"] < max_sem_index), "Dropped"] = 1

    #     # --- Aggregate by semester ---
    #     summary = df.groupby("Semester").agg(
    #         Retained=("Retained", "sum"),
    #         Dropped_Out=("Dropped", "sum"),
    #         Total=("Retained", "count")
    #     ).reset_index()

    #     summary["Retention Rate (%)"] = (summary["Retained"] / summary["Total"] * 100).round(2)

    #     # --- Ensure correct semester ordering based on _id ---
    #     sem_order = sem_df["SemesterLabel"].tolist()
    #     summary["Semester"] = pd.Categorical(summary["Semester"], categories=sem_order, ordered=True)
    #     summary.sort_values(by="Semester", inplace=True)

    #     # --- Delete checkpoint ---
    #     if os.path.exists(CHECKPOINT_FILE):
    #         os.remove(CHECKPOINT_FILE)

    #     return summary[["Semester", "Retained", "Dropped_Out", "Retention Rate (%)"]].reset_index(drop=True)


    # ------------------------------
    # 6. Top Performers per Program
    # ------------------------------

    @cache_meta()
    def get_top_performers(self, course=None, year_level=None):
        
        # 1. Load students using batch checkpoint loader
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()

        student_ids = students_df["_id"].tolist()
        # 2. Load grades (StudentID + Grades + SemesterID)
        grades = list(self.db.grades.find({"StudentID": {"$in": student_ids}}, {"StudentID": 1, "Grades": 1, "SemesterID": 1}))
        if not grades:
            return pd.DataFrame()

        grades_df = pd.DataFrame(grades)

        # 3. Compute GPA per student/semester
        def safe_avg(grades):
            if isinstance(grades, list) and grades:
                valid = [g for g in grades if g is not None]
                return sum(valid) / len(valid) if valid else None
            return None

        grades_df["GPA"] = grades_df["Grades"].apply(safe_avg)
        grades_df = grades_df.dropna(subset=["GPA"])

        # Keep the *latest* semester per student (if multiple exist)
        grades_df = grades_df.sort_values("SemesterID").drop_duplicates("StudentID", keep="last")

        # 4. Join with students
        merged = students_df.merge(
            grades_df[["StudentID", "GPA", "SemesterID"]],
            left_on="_id", right_on="StudentID", how="inner"
        )

        # 5. Attach semester info (SchoolYear + Semester)
        sem_ids = merged["SemesterID"].unique().tolist()
        sem_map = {
            s["_id"]: f"{s.get('SchoolYear', '')} - {s['Semester']}"
            for s in self.db.semesters.find({"_id": {"$in": sem_ids}}, {"SchoolYear": 1, "Semester": 1})
        }
        merged["Semester"] = merged["SemesterID"].map(sem_map)

        # 6. Rank within each Course
        merged["Rank"] = merged.groupby("Course")["GPA"].rank("dense", ascending=False)

        # 7. Sort results
        merged.sort_values(["Course", "Rank"], inplace=True)

        # 8. Final clean DataFrame
        result = merged.rename(columns={
            "_id": "Student ID",
            "Name": "Student Name",
            "Course": "Program",
            "YearLevel": "Year Level"
        })[["Program", "Year Level", "Semester", "Student ID", "Student Name", "GPA", "Rank"]]

        result["GPA"] = result["GPA"].round(2)

        return result

    # @cache_meta()
    def get_retention_rates(self, batch_size=1000, course=None, year_level=None):
        import os, pickle
        import pandas as pd

        CHECKPOINT_FILE = os.path.join(CACHE_DIR, "retention_checkpoint.pkl")

        # --- Load checkpoint ---
        if os.path.exists(CHECKPOINT_FILE):
            with open(CHECKPOINT_FILE, "rb") as f:
                checkpoint = pickle.load(f)
            start_index = checkpoint["last_index"]
            results = checkpoint["results"]
            print(f"Resuming retention from index {start_index}...")
        else:
            start_index, results = 0, []

        # --- Load students ---
        students_df = self.get_students_batch_checkpoint(course=course, year_level=year_level)
        if students_df.empty:
            return pd.DataFrame()
        student_ids = students_df["_id"].tolist()

        # --- Process students in batches ---
        for i in range(start_index, len(student_ids), batch_size):
            batch_ids = student_ids[i:i + batch_size]
            print(f"Processing retention for students {i+1}-{min(i+batch_size, len(student_ids))}")

            grades_cursor = self.db.grades.find(
                {"StudentID": {"$in": batch_ids}},
                {"StudentID": 1, "SemesterID": 1}
            )
            grades_df = pd.DataFrame(list(grades_cursor))
            if grades_df.empty:
                continue

            # Map SemesterID → formatted string
            sem_ids = grades_df["SemesterID"].unique().tolist()
            sem_map = {
                s["_id"]: f"{s['Semester']} {s['SchoolYear']}"
                for s in self.db.semesters.find(
                    {"_id": {"$in": sem_ids}},
                    {"Semester": 1, "SchoolYear": 1}
                )
            }
            grades_df["Semester"] = grades_df["SemesterID"].map(sem_map)
            results.append(grades_df)

            # --- Save checkpoint ---
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(CHECKPOINT_FILE, "wb") as f:
                pickle.dump({"last_index": i + batch_size, "results": results}, f)

        if not results:
            return pd.DataFrame()

        df = pd.concat(results, ignore_index=True)

        # --- Sort semesters properly ---
        def sem_sort_key(val):
            if not isinstance(val, str):
                return (9999, 99)
            sem, year = val.split()
            order_map = {"FirstSem": 1, "SecondSem": 2, "Summer": 3}
            return (int(year), order_map.get(sem, 99))

        df["SemSort"] = df["Semester"].map(sem_sort_key)
        df = df.sort_values(by=["StudentID", "SemSort"])

        # --- Retention logic ---
        df["Next_Semester"] = df.groupby("StudentID")["Semester"].shift(-1)
        df["Retained"] = df["Next_Semester"].notnull().astype(int)

        # --- Exclude the global latest semester (since no one can be retained past it) ---
        latest_semester = max(df["Semester"], key=sem_sort_key)
        retention_df = df[df["Semester"] != latest_semester].copy()

        # --- Aggregate retention per semester ---
        summary = retention_df.groupby("Semester").agg(
            Retained=("Retained", "sum"),
            Total=("StudentID", "count")
        ).reset_index()

        summary["Dropped Out"] = summary["Total"] - summary["Retained"]
        summary["Retention Rate (%)"] = (summary["Retained"] / summary["Total"] * 100).round(2)

        # --- Sort semesters in correct academic order ---
        summary["SemSort"] = summary["Semester"].map(sem_sort_key)
        summary = summary.sort_values(by="SemSort").drop(columns=["SemSort"])

        # --- Delete checkpoint ---
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)

        return summary[["Semester", "Retained", "Dropped Out", "Retention Rate (%)"]].reset_index(drop=True)



    # ------------------------------
    # 7. Curriculum Progress Viewer
    # ------------------------------

    @cache_meta()
    def get_curriculum_progress(self,program=None):
        """
        Fetch curriculum subjects from the database.
        If 'program' is given, only return subjects for that program.
        Includes semester information.
        """
        

        # Build the query
        query = {}
        if program:
            query["programCode"] = program

        # Fetch all curriculums matching the query
        curriculums = list(self.db.curriculum.find(
            query,
            {"programName": 1, "curriculumYear": 1, "subjects": 1}
        ))

        rows = []
        for cur in curriculums:
            prog = cur.get("programName", "")
            year = cur.get("curriculumYear", "")
            subjects = cur.get("subjects", [])

            for subj in subjects:
                prereqs = subj.get("preRequisites", [])
                prereq_str = ", ".join(prereqs) if prereqs else ""

                rows.append({
                    "Program": prog,
                    "Curriculum Year": year,
                    "Semester": subj.get("semester", ""),  # Added semester
                    "Year": subj.get("year", ""),  
                    "Subject Code": subj.get("code", ""),
                    "Subject Description": subj.get("name", ""),
                    "Lec Hours": subj.get("lec", 0),
                    "Lab Hours": subj.get("lab", 0),
                    "Units": subj.get("unit", 0),
                    "Prerequisites": prereq_str
                })

        df = pd.DataFrame(rows)
        return df

    def get_predicted_subjects(self, student_id, semester_string):
        """
        Predicts recommended and blocked subjects for a student for a given semester.
        """
        from helpers.data_helper import data_helper
        dh = data_helper({"db": self.db})

        # 1. Get student's course
        student_data = self.db.students.find_one({"_id": student_id})
        if not student_data:
            return pd.DataFrame(), pd.DataFrame()
        student_course = student_data.get("Course")

        # 2. Get student's passed subjects
        grades_df = dh.get_grades(student_id=student_id)

        passed_subjects = set()
        if not grades_df.empty:
            # Explode the DataFrame to have one row per subject grade
            grades_flat = grades_df.explode(['SubjectCodes', 'Grades'])
            # Filter for passed grades
            passed_df = grades_flat[grades_flat['Grades'] >= 75]
            passed_subjects.update(passed_df['SubjectCodes'].unique())

        # 3. Get curriculum for the student's course
        curriculum_df = dh.get_curriculum(student_course)
        if curriculum_df.empty:
            return pd.DataFrame(), pd.DataFrame()

        # 4. Parse semester string
        # Assuming semester_string format is "FirstSem 2025", "SecondSem 2025", etc.
        semester_map = {"FirstSem": "First", "SecondSem": "Second", "Summer": "Summer"}
        parts = semester_string.split()
        semester_name_short = parts[0]
        semester_name_full = semester_map.get(semester_name_short)

        if not semester_name_full:
            return pd.DataFrame(), pd.DataFrame()

        # 5. Filter curriculum for the target semester
        target_subjects_df = curriculum_df[curriculum_df['semester'] == semester_name_full]

        recommended_list = []
        blocked_list = []

        # 6. Check prerequisites
        for _, subject in target_subjects_df.iterrows():
            prereqs = subject.get('preRequisites', [])
            subject_code = subject.get('code') # Corrected from 'Subject Code'

            # Skip subjects already passed
            if subject_code in passed_subjects:
                continue

            missing_prereqs = [p for p in prereqs if p not in passed_subjects]

            if not missing_prereqs:
                recommended_list.append({
                    "Subject Code": subject_code,
                    "Description": subject.get('name'), # Corrected from 'Description'
                    "Grade": "",  # No grade yet
                    "Year Level": subject.get('year'),
                    "Semester": subject.get('semester')
                })
            else:
                blocked_list.append({
                    "Subject Code": subject_code,
                    "Subject": subject.get('name'), # Corrected from 'Description'
                    "Prerequisites": ", ".join(missing_prereqs),
                    "Year Level": subject.get('year'),
                    "Semester": subject.get('semester')
                })

        recommended_df = pd.DataFrame(recommended_list)
        blocked_df = pd.DataFrame(blocked_list)

        return recommended_df, blocked_df


# ------------------------------
# Test all functions in __main__
# ------------------------------
if __name__ == "__main__":
    
    # deans_list = get_deans_list(batch_size=10000) # 1. Dean's List
    # probation = get_academic_probation_batch_checkpoint(top_n=10) #2. Academic Probation
    # pass_fail = get_subject_pass_fail() # 3. Subject Pass/Fail Distribution
    # incomplete = get_incomplete_grades() #4. Incomplete Grades Report
    # retention = get_retention_rates(batch_size=1000, course=None, year_level=None) #5. Retention and Dropout Rates
    # top_performers = get_top_performers() #6. Top Performers per Program
    # curriculum = get_curriculum_progress() #7. Curriculum Progress Viewer
    # print(curriculum.iloc[0])
    
    pass
