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


def intervention_candidates_page(db):
    """📋 Lists students at academic risk (low or missing grades)."""
    st.markdown("### 🚨 Intervention Candidates List")
    st.markdown("Students flagged due to **low grades (<60)** or **missing grades (INC)**.")

    # Faculty name
    teacher_name = st.session_state.get("fullname", "")
    if not teacher_name:
        teacher_name = st.text_input("Faculty Name", value="")
        if not teacher_name:
            st.warning("Faculty name is required.")
            return

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
            subj_s = str(subj) if subj else ""
            tchr_s = str(tchr) if tchr else ""
            if tchr_s != teacher_name:
                continue

            grade_val = None
            risk_flag = ""

            # --- FIX: treat 0 as INC ---
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

    # --- Export ---
    csv = display_df.to_csv(index=False).encode("utf-8")
    sem_label = selected_sem.replace(" ", "_")
    st.download_button(
        label="⬇️ Download CSV",
        data=csv,
        file_name=f"intervention_candidates_{teacher_name}_{sem_label}.csv",
        mime="text/csv"
    )
