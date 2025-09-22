import streamlit as st
import pandas as pd
from itertools import zip_longest


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


def grade_submission_status_page(db):
    st.markdown("### 📊 Grade Submission Status")
    st.markdown("Tracks whether faculty have completely submitted grades for their classes.")

    # --- Determine teacher list based on user role ---
    user_role = st.session_state.get("user_role", "")
    if user_role == "registrar":
        # Registrar sees all teachers
        teacher_list = get_teachers(db)
    elif user_role == "teacher":
        # Teacher sees only themselves
        teacher_list = [st.session_state.get("fullname", "")]
    else:
        teacher_list = []

    if not teacher_list:
        st.warning("Faculty name is required.")
        return

    # --- Teacher selectbox ---
    teacher_name = st.selectbox("Select Teacher", teacher_list)

    if st.button("Search", key="search_btn"):
        # --- Load collections ---
        with st.spinner("Loading data..."):
            students_df = pd.DataFrame(list(db.students.find()))
            grades_list = list(db.grades.find())
            semesters_df = pd.DataFrame(list(db.semesters.find()))
            subjects_df = pd.DataFrame(list(db.subjects.find({"Teacher": teacher_name})))

        if students_df.empty or not grades_list or semesters_df.empty or subjects_df.empty:
            st.warning("⚠️ Missing data in one or more collections.")
            return

        # --- Semester Filter ---
        semesters_df = semesters_df.rename(columns={"_id": "SemesterID"})
        semesters_df["SemesterID"] = semesters_df["SemesterID"].astype(str)
        semesters_df["Label"] = semesters_df["Semester"].astype(str) + " " + semesters_df["SchoolYear"].astype(str)

        semester_map = dict(zip(semesters_df["SemesterID"], semesters_df["Label"]))
        semester_options = ["All Semesters"] + list(semester_map.values())
        selected_sem = st.selectbox("📅 Select Semester", semester_options)

        if selected_sem == "All Semesters":
            selected_ids = set(semesters_df["SemesterID"])
        else:
            selected_ids = {k for k, v in semester_map.items() if v == selected_sem}

        # --- Normalize subjects ---
        subjects_df = subjects_df.rename(columns={"_id": "SubjectCode"})
        subjects_df["SubjectCode"] = subjects_df["SubjectCode"].astype(str)

        # --- Build submission rows ---
        submission_rows = []
        for gdoc in grades_list:
            sem = str(gdoc.get("SemesterID", ""))
            if sem not in selected_ids:
                continue
            sid = str(gdoc.get("StudentID", ""))

            for subj, grd, tchr in zip_longest(
                gdoc.get("SubjectCodes", []),
                gdoc.get("Grades", []),
                gdoc.get("Teachers", []),
                fillvalue=None
            ):
                if tchr != teacher_name:
                    continue
                submission_rows.append({
                    "SemesterID": sem,
                    "StudentID": sid,
                    "SubjectCode": str(subj) if subj else "",
                    "Grade": grd
                })

        if not submission_rows:
            st.info("✅ No grade records found for the selected semester(s).")
            return

        grades_df = pd.DataFrame(submission_rows)

        # --- Count submissions ---
        def grade_is_submitted(val):
            return val not in [None, "", "0"]

        grouped = grades_df.groupby("SubjectCode").agg(
            SubmittedGrades=("Grade", lambda x: sum(grade_is_submitted(g) for g in x)),
            TotalStudents=("StudentID", "nunique")
        ).reset_index()

        grouped["SubmissionRate"] = (grouped["SubmittedGrades"] / grouped["TotalStudents"] * 100).round(1).astype(str) + "%"

        # --- Merge with subject info ---
        subj_map = dict(zip(subjects_df["SubjectCode"], subjects_df["Description"]))
        grouped["Subject"] = grouped["SubjectCode"].map(subj_map)

        display_df = grouped[["SubjectCode", "Subject", "SubmittedGrades", "TotalStudents", "SubmissionRate"]]

        # --- Show table ---
        st.dataframe(display_df)

        # --- Export CSV ---
        csv = display_df.to_csv(index=False).encode("utf-8")
        sem_label = selected_sem.replace(" ", "_")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"grade_submission_status_{teacher_name}_{sem_label}.csv",
            mime="text/csv"
        )
