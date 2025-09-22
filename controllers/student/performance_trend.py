import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import helpers.data_helper as dh

def performance_trend_page(db):
    r = dh.data_helper({"db": db})
    st.title("📈 Performance Trend Over Time")

    user_role = st.session_state.get("user_role", "")
    StudentID = st.session_state.get("uid", None)

    # --- Student Selection ---
    if user_role == "registrar":
        students = r.get_students()  # all students
        if students.empty:
            st.warning("No students found.")
            return

        student_display = students["Name"] + " (" + students["_id"].astype(str) + ")"
        selected_student = st.selectbox("Select Student", student_display.tolist())
        selected_id = students.iloc[student_display[student_display == selected_student].index[0]]["_id"]

        student_info = students[students["_id"] == selected_id]
    else:
        # Student user
        if not StudentID:
            st.warning("Student not logged in.")
            return
        student_info = r.get_students(StudentID=StudentID)

    if student_info.empty:
        st.warning("Student not found.")
        return

    student_name = student_info.iloc[0]["Name"]
    sid = student_info.iloc[0]["_id"]

    st.subheader(f"Student: {student_name} ({sid})")

    # --- Get Grades ---
    stud_grades = r.get_student_subjects_grades(StudentID=sid)

    if stud_grades.empty or 'Grade' not in stud_grades.columns or stud_grades['Grade'].isnull().all():
        st.info("No grades available to show performance trend.")
        return

    # --- Calculate GPA Trend ---
    stud_grades['Grade'] = pd.to_numeric(stud_grades['Grade'], errors='coerce')

    gpa_trend = (
        stud_grades.dropna(subset=['Grade'])
        .groupby(["SchoolYear", "Semester"])["Grade"]
        .mean()
        .reset_index()
    )

    if gpa_trend.empty:
        st.info("No semester data available to show trend.")
        return

    gpa_trend["Period"] = gpa_trend["SchoolYear"].astype(str) + " / " + gpa_trend["Semester"].astype(str)
    gpa_trend.sort_values(["SchoolYear", "Semester"], inplace=True)
    gpa_trend.rename(columns={"Grade": "Semester GPA"}, inplace=True)

    # --- Display Chart ---
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(gpa_trend["Period"], gpa_trend["Semester GPA"], marker='o', linestyle='-', color='b')
    ax.set_ylim(50, 100)
    ax.set_xlabel("Semester")
    ax.set_ylabel("Semester GPA")
    ax.set_title("GPA Trend per Semester")
    ax.grid(True, linestyle='--', alpha=0.6)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    # --- Display Table ---
    st.subheader("Data")
    display_df = gpa_trend[["Period", "Semester GPA"]].copy()
    display_df["Semester GPA"] = display_df["Semester GPA"].map("{:.2f}".format)
    st.dataframe(display_df.rename(columns={"Period": "Semester"}).reset_index(drop=True))
