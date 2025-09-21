import streamlit as st
import pandas as pd
import helpers.data_helper as dh

def calculate_difficulty(grades_series):
    """Calculates difficulty level based on grade distribution."""
    average_grade = grades_series.mean()
    if average_grade >= 85:
        return "Low"
    elif average_grade >= 75:
        return "Medium"
    else:
        return "High"

def subject_difficulty_page(db):
    r = dh.data_helper({"db": db})
    st.title("📊 Subject Difficulty Ratings")

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
    st.subheader(f"Student: {student_name} ({StudentID})")

    # --- Get student's taken subjects and grades ---
    student_grades = r.get_student_subjects_grades(StudentID=StudentID)
    if student_grades.empty:
        st.info("You have no grades recorded yet.")
        return

    # Get all subjects for description mapping
    all_subjects_df = r.get_subjects()
    if not all_subjects_df.empty:
        subject_map = all_subjects_df.set_index('Subject Code')['Description'].to_dict()
    else:
        subject_map = {}

    # --- Process each subject ---
    report_data = []

    # Iterate over unique subjects taken by the student
    subjects_taken = student_grades[['Subject Code', 'Grade']].drop_duplicates(subset=['Subject Code'])

    for _, row in subjects_taken.iterrows():
        subject_code = row['Subject Code']
        your_grade = row['Grade']

        # Get all grades for this subject from all students
        all_grades_subject = r.get_all_grades_for_subject(subject_code)

        if all_grades_subject.empty:
            continue

        total_students = len(all_grades_subject)
        grades = all_grades_subject['Grade'].astype(float)

        # Grade distribution calculation
        dist_90_100 = (grades >= 90).sum() / total_students * 100
        dist_80_89 = ((grades >= 80) & (grades < 90)).sum() / total_students * 100
        dist_70_79 = ((grades >= 70) & (grades < 80)).sum() / total_students * 100
        dist_60_69 = ((grades >= 60) & (grades < 70)).sum() / total_students * 100
        dist_lt_60 = (grades < 60).sum() / total_students * 100

        # Difficulty level
        difficulty = calculate_difficulty(grades)

        report_data.append({
            "Subject Code": subject_code,
            "Subject": subject_map.get(subject_code, "N/A"),
            "Total Students": total_students,
            "Your Grade(%)": f"{your_grade:.2f}",
            "90-100% (%)": f"{dist_90_100:.1f}",
            "80-89% (%)": f"{dist_80_89:.1f}",
            "70-79% (%)": f"{dist_70_79:.1f}",
            "60-69% (%)": f"{dist_60_69:.1f}",
            "< 60% (%)": f"{dist_lt_60:.1f}",
            "Difficulty Level": difficulty,
        })

    # --- Display Table ---
    if not report_data:
        st.info("Could not generate difficulty ratings for your subjects.")
        return

    report_df = pd.DataFrame(report_data)
    st.dataframe(report_df)
