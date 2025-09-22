import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
from typing import List, Dict

# ---------- Helpers ----------
def get_subjects_by_teacher(db, teacher_name: str) -> pd.DataFrame:
    try:
        grades: List[Dict] = list(db.grades.find({"Teachers": teacher_name}))
    except Exception as e:
        print(f"Error querying grades collection: {e}")
        return pd.DataFrame()

    if not grades:
        return pd.DataFrame()

    # Extract unique subject codes and semester IDs
    all_subject_codes = set()
    all_semester_ids = set()
    for entry in grades:
        if "SubjectCodes" in entry:
            all_subject_codes.update(entry["SubjectCodes"])
        if "SemesterID" in entry:
            all_semester_ids.add(entry["SemesterID"])

    # Fetch related subjects and semesters
    subjects = list(db.subjects.find({"_id": {"$in": list(all_subject_codes)}}))
    semesters = list(db.semesters.find({"_id": {"$in": list(all_semester_ids)}}))

    # Convert to DataFrames
    grades_df = pd.DataFrame(grades)
    subjects_df = pd.DataFrame(subjects).rename(columns={"_id": "SubjectCodes"})
    semesters_df = pd.DataFrame(semesters).rename(columns={"_id": "SemesterID"})

    # Explode grades for multi-subject entries
    if not grades_df.empty:
        grades_df = grades_df.explode(["SubjectCodes", "Grades", "Teachers", "Status"])

    # Merge all
    merged = pd.merge(grades_df, subjects_df, how="left", on="SubjectCodes")
    merged = pd.merge(merged, semesters_df, how="left", on="SemesterID")

    # Build DisplayName
    merged["DisplayName"] = merged.apply(
        lambda row: f"{row.get('SubjectCodes', '')} - {row.get('Description', '')} "
                    f"({row.get('Semester', '')}, {row.get('SchoolYear', '')})",
        axis=1
    )

    return merged


def get_student_grades(db, teacher_name, subject_code):
    students_df = pd.DataFrame(list(db.students.find()))
    grades_df = pd.DataFrame(list(db.grades.find()))

    if students_df.empty or grades_df.empty:
        return pd.DataFrame()

    students_df = students_df.rename(columns={'_id': 'StudentID'})

    # explode
    if isinstance(grades_df.get("SubjectCodes").iloc[0], list):
        grades_exploded = grades_df.explode(['SubjectCodes', 'Grades', 'Teachers'])
    else:
        grades_exploded = grades_df.copy()

    grades_exploded = grades_exploded.rename(columns={'SubjectCodes': 'SubjectCode'})

    # filter by teacher + subject
    filtered = grades_exploded[
        (grades_exploded["SubjectCode"] == subject_code) &
        (grades_exploded["Teachers"] == teacher_name)
    ]

    if filtered.empty:
        return pd.DataFrame()

    merged = pd.merge(filtered, students_df, on="StudentID", how="left")

    return merged[["StudentID", "Name", "Course", "YearLevel", "Grades"]]

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


# ---------- Main Page ----------
def student_grade_analytics_page(db):
    st.markdown("## 📊 Students Grade Analytics")

    user_role = st.session_state.get("user_role", "")
    teacher_list = []

    if user_role == "registrar":
        teacher_list = get_teachers(db)
    elif user_role == "teacher":
        teacher_list = get_teachers(db, st.session_state.get("fullname", ""))
    else:
        st.warning("⚠️ Unknown user role.")
        return

    if not teacher_list:
        st.warning("⚠️ No teachers available for selection.")
        return

    teacher_name = st.selectbox("👩‍🏫 Select Teacher", [""] + teacher_list)
    if not teacher_name:
        st.info("Please select a teacher to continue.")
        return

    # ---------- Load teacher's subjects ----------
    with st.spinner("Loading teacher's subjects..."):
        subjects_df = get_subjects_by_teacher(db, teacher_name)

    if subjects_df.empty:
        st.warning("⚠️ No subjects found for this teacher.")
        return

    subject_options = [""] + subjects_df["DisplayName"].unique().tolist()
    subject_map = dict(zip(subjects_df["DisplayName"], subjects_df["SubjectCodes"]))

    selected_subject_label = st.selectbox("📘 Select Subject", subject_options)
    selected_subject_code = subject_map.get(selected_subject_label, None)
    if not selected_subject_code:
        return

    # ---------- Fetch student grades ----------
    with st.spinner("Fetching grades..."):
        df = get_student_grades(db, teacher_name, selected_subject_code)

    if df.empty:
        st.warning("⚠️ No grades found for this subject.")
        return

    # ---------- Summary Stats ----------
    st.subheader(f"📑 Grades Summary of Faculty: {teacher_name}")
    summary_data = {
        "Mean": round(df["Grades"].mean(), 2),
        "Median": round(df["Grades"].median(), 2),
        "Highest": round(df["Grades"].max(), 2),
        "Lowest": round(df["Grades"].min(), 2),
    }
    st.table(pd.DataFrame([summary_data]))

    # ---------- Histogram (Grade Distribution) ----------
    st.subheader(f"📊 Grade Distribution - {selected_subject_label}")
    hist_data = df["Grades"].value_counts().sort_index()
    hist_options = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": [str(i) for i in hist_data.index.tolist()]},
        "yAxis": {"type": "value"},
        "series": [{"data": [int(v) for v in hist_data.values.tolist()], "type": "bar"}],
    }
    st_echarts(options=hist_options, height="400px")

    # ---------- Pass vs Fail ----------
    st.subheader("✅ Pass vs ❌ Fail")
    pass_fail_counts = {
        "Pass": int((df["Grades"] >= 75).sum()),
        "Fail": int((df["Grades"] < 75).sum()),
    }
    pass_fail_options = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": list(pass_fail_counts.keys())},
        "yAxis": {"type": "value"},
        "series": [{
            "data": [
                {"value": int(pass_fail_counts["Pass"]), "itemStyle": {"color": "green"}},
                {"value": int(pass_fail_counts["Fail"]), "itemStyle": {"color": "red"}},
            ],
            "type": "bar",
        }],
    }
    st_echarts(options=pass_fail_options, height="400px")

    # ---------- Student Grades Table ----------
    st.subheader("📝 Student Grades Table")
    df["GradeDisplay"] = df["Grades"].apply(lambda g: "INC" if g == 0 else str(g))
    df["Status"] = df["Grades"].apply(lambda x: "Pass" if x >= 75 else "Fail")

    def style_pass_fail(val):
        return "color: green; font-weight: bold" if val == "Pass" else "color: red; font-weight: bold"

    st.dataframe(
        df[["StudentID", "Name", "Course", "YearLevel", "GradeDisplay", "Status"]]
        .style.applymap(style_pass_fail, subset=["Status"])
    )
