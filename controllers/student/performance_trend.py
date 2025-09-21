import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import helpers.data_helper as dh

def performance_trend_page(db):
    r = dh.data_helper({"db": db})
    st.title("📈 Performance Trend Over Time")

    StudentID = st.session_state.get('uid', None)
    if not StudentID:
        st.warning("Student not logged in.")
        return

    # --- Student Info ---
    student_info = r.get_students(StudentID=StudentID)
    if student_info.empty:
        st.warning("Student not found.")
        return

    student_name = student_info.iloc[0]["Name"]
    st.subheader(f"Student: {student_name}")

    # --- Get Grades ---
    stud_grades = r.get_student_subjects_grades(StudentID=StudentID)

    if stud_grades.empty or 'Grade' not in stud_grades.columns or stud_grades['Grade'].isnull().all():
        st.info("No grades available to show performance trend.")
        return

    # --- Calculate GPA Trend ---
    # Ensure 'Grade' is numeric
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
    gpa_trend.sort_values("Period", inplace=True)
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
