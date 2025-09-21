import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from pymongo import MongoClient

def class_grade_distribution(db, teacher_name, semester, school_year):
    """
    Generates and displays the Class Grade Distribution report.
    This report shows the percentage of students falling into different grade brackets
    for each subject taught by a specific teacher in a given semester and school year.
    """
    st.markdown("### 📊 Class Grade Distribution")
    st.markdown(f"**Faculty Name:** `{teacher_name}`")
    st.markdown(f"**Semester and School Year:** `{semester}, {school_year}`")

    # Find the semester ID from the semester name and school year
    semester_doc = db.semesters.find_one({"Semester": semester, "SchoolYear": school_year})
    if not semester_doc:
        st.warning("Selected semester and school year combination not found.")
        return
    semester_id = semester_doc["_id"]

    # Find all subjects taught by the given teacher
    teacher_subjects_cursor = db.subjects.find({"Teacher": teacher_name})
    teacher_subject_codes = [s["_id"] for s in teacher_subjects_cursor]

    if not teacher_subject_codes:
        st.warning(f"No subjects found for teacher: {teacher_name}")
        return

    # Find all grade entries for the specific semester
    grades_cursor = db.grades.find({"SemesterID": semester_id})

    report_data = []

    # Create a mapping of subject codes to their names for easy lookup
    subject_details = {s["_id"]: s["Description"] for s in db.subjects.find({"_id": {"$in": teacher_subject_codes}})}

    # Initialize report structure for all subjects taught by the teacher
    for code, name in subject_details.items():
        report_data.append({
            "Course Code": code,
            "Course Name": name,
            "95-100(%)": 0,
            "90-94 (%)": 0,
            "85-89 (%)": 0,
            "80-84(%)": 0,
            "75-79%": 0,
            "Below 75(%)": 0,
            "student_count": 0,
        })

    # Process grades
    for grade_entry in grades_cursor:
        student_id = grade_entry.get("StudentID")
        for i, subject_code in enumerate(grade_entry.get("SubjectCodes", [])):
            if subject_code in teacher_subject_codes:
                # Find the corresponding report row
                report_row = next((item for item in report_data if item["Course Code"] == subject_code), None)
                if report_row:
                    grade = grade_entry.get("Grades", [])[i]
                    report_row["student_count"] += 1
                    if grade >= 95:
                        report_row["95-100(%)"] += 1
                    elif 90 <= grade <= 94:
                        report_row["90-94 (%)"] += 1
                    elif 85 <= grade <= 89:
                        report_row["85-89 (%)"] += 1
                    elif 80 <= grade <= 84:
                        report_row["80-84(%)"] += 1
                    elif 75 <= grade <= 79:
                        report_row["75-79%"] += 1
                    else:
                        report_row["Below 75(%)"] += 1

    if not any(row['student_count'] > 0 for row in report_data):
        st.info("No student grade data found for the selected faculty and term.")
        return

    # Create DataFrame and calculate percentages
    df = pd.DataFrame(report_data)

    # Filter out courses with no students
    df = df[df['student_count'] > 0].copy()

    grade_cols = ["95-100(%)", "90-94 (%)", "85-89 (%)", "80-84(%)", "75-79%", "Below 75(%)"]

    for col in grade_cols:
        df[col] = (df[col] / df['student_count'] * 100).round(2)

    df["Total"] = df[grade_cols].sum(axis=1).round(0).astype(str) + '%'

    # Format percentage columns
    for col in grade_cols:
        df[col] = df[col].astype(str) + '%'

    st.dataframe(df[["Course Code", "Course Name"] + grade_cols + ["Total"]])

    # --- Display Histogram ---
    st.markdown("---")
    st.markdown("### Grade Distribution Histograms")

    for index, row in df.iterrows():
        st.markdown(f"#### {row['Course Name']} ({row['Course Code']})")

        # Extract numerical values for plotting
        plot_values = [float(str(row[col]).replace('%','')) for col in grade_cols]
        plot_labels = [col.replace('(%)','').replace('%','').strip() for col in grade_cols]

        fig, ax = plt.subplots()
        ax.bar(plot_labels, plot_values)
        ax.set_ylabel("Percentage of Students (%)")
        ax.set_title(f"Grade Distribution for {row['Course Code']}")
        plt.xticks(rotation=45, ha="right")
        st.pyplot(fig)
