import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import helpers.data_helper as dh


def get_student_subjects_grades(db, StudentID=None, limit=1000):
    """
    Returns all subjects and grades for a specific student with:
    ["Subject Code", "Description", "Grade", "Semester", "SchoolYear"]
    """

    def query():
        if StudentID is None:
            return pd.DataFrame()

        student_id = int(StudentID)
        grade_docs = db.grades.find({"StudentID": student_id})  # ✅ Multiple documents

        rows = []
        for grade_doc in grade_docs:
            subject_codes = grade_doc.get("SubjectCodes", [])
            grades = grade_doc.get("Grades", [])
            semester_id = grade_doc.get("SemesterID")

            # Fetch semester info
            sem = db.semesters.find_one({"_id": semester_id})
            semester = sem["Semester"] if sem else None
            school_year = sem["SchoolYear"] if sem else None

            # Process each subject
            for code, grade in zip(subject_codes, grades):
                subj = db.subjects.find_one({"_id": code})
                desc = subj["Description"] if subj else None

                rows.append({
                    "Subject Code": code,
                    "Description": desc,
                    "Grade": grade,
                    "Semester": semester,
                    "SchoolYear": school_year
                })

        # Apply limit
        if limit:
            rows = rows[:limit]

        return pd.DataFrame(rows)

    return query()  # no caching


def passed_failed_summary_page(db):
    r = dh.data_helper({"db": db})
    st.title("📊 Passed vs Failed Summary")

    # --- Role & UID ---
    role = st.session_state.get("user_role", "student")
    StudentID = st.session_state.get("uid", None)

    if role == "registrar":
        students = r.get_students()
        if students.empty:
            st.warning("No students found.")
            return

        selected_student = st.selectbox(
            "Select Student",
            students["Name"].tolist()
        )
        student_row = students[students["Name"] == selected_student].iloc[0]
        StudentID = student_row["_id"]
        student_name = student_row["Name"]
        program_code = student_row["Course"]

    elif role == "student":
        if not StudentID:
            st.warning("Student not logged in.")
            return

        student_info = r.get_students(StudentID=StudentID)
        if student_info.empty:
            st.warning("Student not found.")
            return
        student_name = student_info.iloc[0]["Name"]
        program_code = student_info.iloc[0]["Course"]

    else:
        st.error("Unauthorized role.")
        return

    st.subheader(f"Student: {student_name} ({StudentID})")

    # --- Get Curriculum and Grades ---
    curriculum_df = r.get_curriculum(program_code)
    if curriculum_df.empty:
        st.warning(f"No curriculum found for course: {program_code}")
        return
    total_required_subjects = len(curriculum_df)

    stud_grades = get_student_subjects_grades(db,StudentID=StudentID)

    # --- Calculations ---
    if not stud_grades.empty:
        merged_df = pd.merge(
            curriculum_df,
            stud_grades[['Subject Code', 'Grade']],
            on="Subject Code",
            how="left"
        )
        # print('curriculum_df:',curriculum_df)
        print('stud_grades:',stud_grades)
        # print('merged_df:',merged_df)
        merged_df['Grade'] = pd.to_numeric(merged_df['Grade'], errors='coerce')

        passed_subjects = merged_df[merged_df['Grade'] >= 75].shape[0]
        failed_subjects = merged_df[(merged_df['Grade'] < 75) & (merged_df['Grade'].notna())].shape[0]
        taken_subjects = passed_subjects + failed_subjects
        not_yet_taken = total_required_subjects - taken_subjects
    else:
        passed_subjects = 0
        failed_subjects = 0
        not_yet_taken = total_required_subjects

    # --- Prepare Data for Display ---
    summary_data = {
        "Category": ["Passed Subjects", "Failed Subjects", "Not Yet Taken", "Total Required Subjects"],
        "Count": [passed_subjects, failed_subjects, not_yet_taken, total_required_subjects],
        "Percentage (%)": [
            (passed_subjects / total_required_subjects) * 100 if total_required_subjects > 0 else 0,
            (failed_subjects / total_required_subjects) * 100 if total_required_subjects > 0 else 0,
            (not_yet_taken / total_required_subjects) * 100 if total_required_subjects > 0 else 0,
            100
        ],
        "Description": [
            f"Courses where {student_name} achieved passing grades.",
            f"Courses where {student_name} earned failing grades.",
            "Remaining required courses yet to be taken.",
            "Total courses in the curriculum."
        ]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df["Percentage (%)"] = summary_df["Percentage (%)"].map("{:.1f}%".format)

    st.subheader(f"Subject Completion Overview (out of {total_required_subjects} required subjects)")
    st.dataframe(summary_df)

    # --- Display Bar Chart ---
    st.subheader("Visual Summary")
    chart_data = {
        "Passed": passed_subjects,
        "Failed": failed_subjects,
        "Not Yet Taken": not_yet_taken,
    }

    fig, ax = plt.subplots()
    ax.bar(chart_data.keys(), chart_data.values(), color=['green', 'red', 'grey'])
    ax.set_ylabel("Number of Subjects")
    ax.set_title("Subject Completion Status")

    for i, v in enumerate(chart_data.values()):
        ax.text(i, v + 0.1, str(v), ha='center', fontweight='bold')

    st.pyplot(fig)
