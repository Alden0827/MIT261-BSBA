import streamlit as st
import pandas as pd
from itertools import zip_longest

def get_subjects_by_teacher(db, teacher_name):
    """Get subjects handled by the faculty."""
    cursor = db.subjects.find(
        {"Teacher": teacher_name},
        {"_id": 1, "Description": 1, "Teacher": 1}
    )
    df = pd.DataFrame(list(cursor))
    if not df.empty:
        df = df.rename(columns={"_id": "SubjectCode"})
        df["SubjectCode"] = df["SubjectCode"].astype(str)
    return df

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

def intervention_candidates_page(db):
    """📋 Lists students at academic risk (low or missing grades)."""
    st.markdown("### 🚨 Intervention Candidates List")
    st.markdown("Students flagged due to **low grades (<60)** or **missing grades (INC)**.")

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

    # --- Load collections ---
    with st.spinner("Loading data..."):
        students_df = pd.DataFrame(list(db.students.find()))
        grades_list = list(db.grades.find())
        semesters_df = pd.DataFrame(list(db.semesters.find()))
        subjects_df = get_subjects_by_teacher(db, teacher_name)

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

    # --- Normalize ---
    students_df = students_df.rename(columns={"_id": "StudentID"})
    students_df["StudentID"] = students_df["StudentID"].astype(str)
    subj_map = dict(zip(subjects_df["SubjectCode"], subjects_df["Description"]))

    # --- Flatten grades ---
    flat_rows = []
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
            subj_s = str(subj) if subj else ""
            grade_val = None
            risk_flag = ""

            # Treat 0 or empty as INC
            if grd is None or str(grd).strip() == "" or float(grd) == 0:
                grade_val, risk_flag = "INC", "Missing Grades"
            else:
                try:
                    grade_val = float(grd)
                    if grade_val < 60:
                        risk_flag = "At Risk (<60)"
                except:
                    grade_val, risk_flag = "INC", "Missing Grades"

            if risk_flag:
                flat_rows.append({
                    "StudentID": sid,
                    "SubjectCode": subj_s,
                    "Grade": grade_val,
                    "RiskFlag": risk_flag
                })

    if not flat_rows:
        st.info("✅ No at-risk students found for the selected semester(s).")
        return

    flat_df = pd.DataFrame(flat_rows)

    # --- Merge with student + subject info ---
    final_df = pd.merge(flat_df, students_df[["StudentID", "Name"]], on="StudentID", how="left")
    final_df["SubjectName"] = final_df["SubjectCode"].map(subj_map)

    display_df = final_df[["StudentID", "Name", "SubjectCode", "SubjectName", "Grade", "RiskFlag"]]

    # --- Show table ---
    st.dataframe(display_df)

    # --- Export CSV ---
    csv = display_df.to_csv(index=False).encode("utf-8")
    sem_label = selected_sem.replace(" ", "_")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"intervention_candidates_{teacher_name}_{sem_label}.csv",
        mime="text/csv"
    )
