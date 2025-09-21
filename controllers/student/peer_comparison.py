import streamlit as st
import pandas as pd
import helpers.data_helper as dh

def get_remarks(your_grade, class_average):
    """Generates remarks based on grade vs. class average."""
    diff = your_grade - class_average
    if diff > 10:
        return "Above class average - excellent standing"
    elif diff > 0:
        return "Slightly above average - solid performance"
    elif diff == 0:
        return "At class average"
    elif diff > -10:
        return "Slightly below average - room for improvement"
    else:
        return "Below class average - needs additional support"

def peer_comparison_page(db):
    r = dh.data_helper({"db": db})
    st.title("🧑‍🤝‍🧑 Subject Peer Comparison")

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
    subject_map = all_subjects_df.set_index('Subject Code')['Description'].to_dict() if not all_subjects_df.empty else {}

    # --- Process each subject ---
    report_data = []
    subjects_taken = student_grades[['Subject Code', 'Grade']].drop_duplicates(subset=['Subject Code'])

    for _, row in subjects_taken.iterrows():
        subject_code = row['Subject Code']
        your_grade = float(row['Grade'])

        all_grades_subject = r.get_all_grades_for_subject(subject_code)
        if all_grades_subject.empty or len(all_grades_subject) < 2:
            continue # Not enough data for comparison

        grades = all_grades_subject['Grade'].astype(float)
        total_students = len(grades)
        class_average = grades.mean()

        # Calculate rank
        # Sort grades descending, duplicates get same rank
        sorted_grades = grades.sort_values(ascending=False).unique()
        # Find the rank of the student's grade
        rank = pd.Series(sorted_grades).searchsorted(your_grade, side='right')
        your_rank = len(sorted_grades) - rank +1

        remarks = get_remarks(your_grade, class_average)

        report_data.append({
            "Subject Code": subject_code,
            "Subject": subject_map.get(subject_code, "N/A"),
            "Total Students": total_students,
            "Your Grade(%)": f"{your_grade:.2f}%",
            "Class Average(%)": f"{class_average:.2f}%",
            "Your Rank": f"{your_rank} of {total_students}",
            "Remarks": remarks,
        })

    # --- Display Table ---
    if not report_data:
        st.info("Could not generate peer comparison for your subjects.")
        return

    report_df = pd.DataFrame(report_data)
    st.dataframe(report_df)
