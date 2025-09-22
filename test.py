from pymongo import MongoClient
from config.settings import APP_TITLE, DEFAULT_PAGE_TITLE, MONGODB_URI, DB_NAME
import pandas as pd
import os
import pickle   # ✅ Needed for checkpoint save/load

# Database connection
# client = MongoClient(MONGODB_URI)
client = MongoClient('mongodb://localhost:27017/')
CACHE_DIR = "./cache"
db = client['mit261m']


class report_helper(object):
    def __init__(self, arg):
        super(report_helper, self).__init__()
        self.arg = arg
        self.db = arg["db"]

    def get_students_batch_checkpoint(self, batch_size=1000, course=None, year_level=None):
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
            batch_ids = student_ids[i:i + batch_size]
            print(f"Caching students collection: {i + 1} - {min(i + batch_size, len(student_ids))}")

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


# --- Example usage ---
h = report_helper({"db": db})

a = h.get_retention_rates(course='BSBA', year_level=None)
print(a)
