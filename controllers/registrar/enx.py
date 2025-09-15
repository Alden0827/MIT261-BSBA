# import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Helpers
from helpers.data_helper import (
    get_school_years,
    get_semester_names,
    get_courses,
    get_curriculum,
    get_student_subjects_grades,
)
from helpers.registration_helper import find_best_match
    
# ---------------------------
# Main Enrollment Manager Page
# ---------------------------
def enrollment_manager_page(st, db):
    st.title("Enrollment Manager")

    with st.spinner("Loading school years...", show_time=True):
        school_years = get_school_years()
    with st.spinner("Loading semesters...", show_time=True):
        semester_names = get_semester_names()
    with st.spinner("Loading Courses...", show_time=True):
        courses = get_courses()

    # Initialize session state variables
    if "confirm_enrollment" not in st.session_state:
        st.session_state.confirm_enrollment = False
    if "selected_student" not in st.session_state:
        st.session_state.selected_student = None
    if "selected_subjects_to_enroll" not in st.session_state:
        st.session_state.selected_subjects_to_enroll = []
    if "search_results" not in st.session_state:
        st.session_state.search_results = []
    if "selected_student_id" not in st.session_state:
        st.session_state.selected_student_id = None

    # Dropdowns for filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_school_year = st.selectbox("School Year", school_years)
    with col2:
        selected_semester = st.selectbox("Semester", semester_names)
    with col3:
        selected_course = st.selectbox("Course", courses)

    print("Selected Course:", selected_course)

    # Student Search
    st.subheader("🔍 Student Search")
    search_query = st.text_input("Enter student name")

    if st.button("Search"):
        st.session_state.confirm_enrollment = False
        st.session_state.selected_student = None
        st.session_state.selected_student_id = None

        if search_query.strip():

            students_col = db["students"]
            # matches = find_best_match(search_query, students_col)
            matches = find_best_match(search_query, course=selected_course, collection=db.students)

            if matches:
                # ✅ Filter students by selected course
                # matches = [m for m in matches if m.get("Course") == selected_course]

                print('Search result:',matches)
                if matches:
                    st.session_state.search_results = matches
                else:
                    st.session_state.search_results = []
                    st.warning(f"No student found for course {selected_course}.")
            else:
                st.session_state.search_results = []
                st.warning("No student found.")
        else:
            st.warning("Please enter a name to search.")

    # Show search results if available
    if st.session_state.search_results:
        options = {m["_id"]: m["Name"] for m in st.session_state.search_results}
        selected_id = st.selectbox(
            "Select Student",
            list(options.keys()),
            index=list(options.keys()).index(st.session_state.selected_student_id)
            if st.session_state.selected_student_id in options
            else 0,
            format_func=lambda x: options[x],
            key="student_selector",
        )

        if selected_id != st.session_state.selected_student_id:
            st.session_state.selected_student_id = selected_id
            st.session_state.selected_student = db["students"].find_one(
                {"_id": selected_id}
            )

    # Display Student Info
    student = st.session_state.selected_student
    if student:
        st.subheader("👩‍🎓 Student Information")
        st.write(f"**Name:** {student.get('Name', 'N/A')}")
        st.write(f"**Student’s Course (from record):** {student.get('Course', 'N/A')}")
        st.write(f"**Selected Course (filter):** {selected_course}")
        st.write(f"**Year Level:** {student.get('YearLevel', 'N/A')}")

        # ✅ Use curriculum from selected course
        curriculum_df = get_curriculum(selected_course)
        student_grades_df = get_student_subjects_grades(student.get("_id"))
        print('student_id:',student.get("_id"))
        print('student_grades_df:',student_grades_df)
        print('curriculum_df:',curriculum_df.iloc(0))
        if not curriculum_df.empty:
            # ---------------------------
            # Passed subjects (>= 75)
            # ---------------------------


            passed_subjects = []
            if not student_grades_df.empty:
                passed_subjects = student_grades_df[student_grades_df["Grade"] >= 75][
                    "Subject Code"
                ].tolist()

            # Filter curriculum for semester & year level
            potential_subjects = curriculum_df[
                (curriculum_df["semester"] == selected_semester.replace("Sem", ""))
                & (curriculum_df["year"] == student.get("YearLevel"))
                & (
                    ~curriculum_df["Subject Code"].isin(
                        student_grades_df["Subject Code"].tolist()
                    )
                )
            ].copy()

            available_subjects, blocked_subjects = [], []
            for _, row in potential_subjects.iterrows():
                prerequisites = row.get("preRequisites", [])
                if not prerequisites or all(
                    prereq in passed_subjects for prereq in prerequisites
                ):
                    available_subjects.append(row)
                else:
                    blocked_subjects.append(row)

            available_subjects_df = pd.DataFrame(available_subjects)
            blocked_subjects_df = pd.DataFrame(blocked_subjects)

            # ✅ Available Subjects
            st.subheader("✅ Available Subjects")
            if not available_subjects_df.empty:
                st.dataframe(
                    available_subjects_df[["Subject Code", "Description", "unit"]]
                )

                selected_subjects = st.multiselect(
                    "Select subjects to enroll",
                    options=available_subjects_df["Subject Code"].tolist(),
                    format_func=lambda x: f"{x} - {available_subjects_df.loc[available_subjects_df['Subject Code'] == x, 'Description'].iloc[0]}",
                )

                # 🔹 Confirmation Dialog (unchanged) ...
                # Your confirm_enrollment_dialog() remains same here
                # 🔹 Show dialog when Finalize Enrollment is clicked
                if st.button("Finalize Enrollment"):
                    if selected_subjects:
                        st.session_state.confirm_enrollment = True
                        st.session_state.selected_subjects_to_enroll = selected_subjects
                        confirm_enrollment_dialog()
            else:
                st.info("No subjects available for enrollment.")

            # ⛔ Blocked Subjects
            st.subheader("⛔ Blocked Subjects")
            if not blocked_subjects_df.empty:
                st.dataframe(
                    blocked_subjects_df[
                        ["Subject Code", "Description", "Units", "preRequisites"]
                    ]
                )
            else:
                st.info("No blocked subjects.")
        else:
            st.warning(f"No curriculum found for course {selected_course}.")
    else:
        st.info("Search for a student to begin enrollment.")

if __name__ == "__main__":
    from pymongo import MongoClient
    from config.settings import MONGODB_URI, CACHE_MAX_AGE

    client = MongoClient(MONGODB_URI)
    db = client["mit261"]

    enrollment_manager_page(db)
