import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from helpers.data_helper import data_helper


def get_teachers(db, teacher=None):
    """Return list of teacher names from subjects collection."""
    query = {}
    if teacher:
        query['Teacher'] = teacher
    return db.subjects.distinct("Teacher", filter=query)


def get_semesters(db, teacher=None):
    """
    Returns semesters available in the database.
    Optionally filters to only semesters where the specified teacher has subjects.

    :param db: MongoDB database object
    :param teacher: Optional teacher name to filter semesters
    :return: Dict with {_id: "Semester SchoolYear"}

    Sample: {13: 'FirstSem 2024', 14: 'SecondSem 2024'}
    """
    if not teacher:
        semesters = db.semesters.find()
    else:
        teacher_subjects = db.subjects.find({"Teacher": teacher})
        teacher_subject_codes = [s["_id"] for s in teacher_subjects]

        grades_cursor = db.grades.find({"SubjectCodes": {"$in": teacher_subject_codes}})
        semester_ids = {g["SemesterID"] for g in grades_cursor if "SemesterID" in g}
        semesters = db.semesters.find({"_id": {"$in": list(semester_ids)}})

    semester_dict = {s["_id"]: f"{s['Semester']} {s['SchoolYear']}" for s in semesters}
    semester_dict = dict(sorted(semester_dict.items(), key=lambda x: str(x[1])))  # sorted nicely

    return semester_dict


def class_grade_distribution(db):
    """
    Generates Class Grade Distribution report.
    Merges semester and school year into a single dropdown and
    displays teacher + semester filters inline.
    """
    user_role = st.session_state.get("user_role", "")
    if user_role == "teacher":
        teacher_name = st.session_state.get("fullname", "")
        teacher_names = [teacher_name]
    else:
        teacher_names = get_teachers(db)
        teacher_name = None

    # --- Teacher + Semester inline ---
    # col1, col2 = st.columns(2)

    # with col1:
    if user_role != "teacher":
        teacher_name = st.selectbox("Select Faculty", [""] + list(teacher_names))
    else:
        st.markdown(f"👩‍🏫 Faculty: **{teacher_name}**")

    # with col2:
    semester_dict = get_semesters(db, teacher=teacher_name)
    semester_options = [""] + list(semester_dict.values())
    selected_sem_year = st.selectbox("Select Semester & Year", semester_options)

    # --- Generate report button ---
    if st.button("Generate Report"):
        if not teacher_name:
            st.warning("Please select a faculty member to view the report.")
            return
        if not selected_sem_year:
            st.warning("Please select a semester & year.")
            return

        # Reverse lookup semester ID
        semester_id = next((k for k, v in semester_dict.items() if v == selected_sem_year), None)
        if not semester_id:
            st.warning("Selected semester and school year combination not found.")
            return

        st.markdown("### 📊 Class Grade Distribution")
        st.markdown(f"**Faculty Name:** `{teacher_name}`")
        st.markdown(f"**Semester and School Year:** `{selected_sem_year}`")

        # Subjects taught by teacher
        teacher_subjects_cursor = db.subjects.find({"Teacher": teacher_name})
        teacher_subject_codes = [s["_id"] for s in teacher_subjects_cursor]
        if not teacher_subject_codes:
            st.warning(f"No subjects found for teacher: {teacher_name}")
            return

        grades_cursor = db.grades.find({
            "Grades": {"$ne": []},
            "SemesterID": semester_id
        })

        report_data = []
        subject_details = {
            s["_id"]: s["Description"]
            for s in db.subjects.find({"_id": {"$in": teacher_subject_codes}})
        }
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
            for i, subject_code in enumerate(grade_entry.get("SubjectCodes", [])):
                if subject_code in teacher_subject_codes:
                    report_row = next(
                        (item for item in report_data if item["Course Code"] == subject_code), None
                    )
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

        # Build DataFrame
        df = pd.DataFrame(report_data)
        df = df[df['student_count'] > 0].copy()
        grade_cols = ["95-100(%)", "90-94 (%)", "85-89 (%)", "80-84(%)", "75-79%", "Below 75(%)"]

        for col in grade_cols:
            df[col] = (df[col] / df['student_count'] * 100).round(2).astype(str) + '%'

        st.dataframe(df[["Course Code", "Course Name"] + grade_cols])

        # Histogram
        st.markdown("---")
        st.markdown("### Grade Distribution Histograms")

        for _, row in df.iterrows():
            st.markdown(f"#### {row['Course Name']} ({row['Course Code']})")
            plot_values = [float(str(row[col]).replace('%', '')) for col in grade_cols]
            plot_labels = [col.replace('(%)', '').replace('%', '').strip() for col in grade_cols]

            fig, ax = plt.subplots()
            ax.bar(plot_labels, plot_values)
            ax.set_ylabel("Percentage of Students (%)")
            ax.set_title(f"Grade Distribution for {row['Course Code']}")
            plt.xticks(rotation=45, ha="right")
            st.pyplot(fig)
