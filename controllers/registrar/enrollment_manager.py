import streamlit as st
import pandas as pd
from helpers.data_helper import get_school_years, get_semesters, get_courses, get_curriculum, get_student_subjects_grades
from rapidfuzz import process, fuzz
from bson.objectid import ObjectId

def find_best_match(query, collection):
    """
    Find the best match for a query in a MongoDB collection.
    """
    names = [doc["Name"] for doc in collection.find({}, {"Name": 1})]
    best_match = process.extractOne(query, names, scorer=fuzz.token_set_ratio)
    return best_match

def enrollment_manager_page(st, db):
    st.title("Enrollment Manager")

    if 'confirm_enrollment' not in st.session_state:
        st.session_state.confirm_enrollment = False

    # Get dropdown options
    school_years = get_school_years()
    semesters = get_semesters()
    courses = get_courses()

    # Create columns for the dropdowns and search bar
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_school_year = st.selectbox("School Year", school_years)
    with col2:
        selected_semester = st.selectbox("Semester", semesters)
    with col3:
        selected_course = st.selectbox("Course", courses)

    # Student search
    st.subheader("Student Search")
    search_query = st.text_input("Search for a student by name")
    if st.button("Search"):
        st.session_state.confirm_enrollment = False  # Reset confirmation on new search
        if search_query:
            students_col = db["students"]
            match = find_best_match(search_query, students_col)
            if match:
                best_name, score, _ = match
                if score > 80:  # Set a threshold for matching
                    st.session_state['selected_student'] = students_col.find_one({"Name": best_name})
                else:
                    st.warning("No student found with that name.")
            else:
                st.warning("No student found with that name.")

    # Display student information and subject tables
    if 'selected_student' in st.session_state and st.session_state['selected_student']:
        student = st.session_state['selected_student']
        st.subheader("Student Information")
        st.write(f"**Name:** {student['Name']}")
        st.write(f"**Course:** {student['Course']}")
        st.write(f"**Year Level:** {student['YearLevel']}")

        # Get curriculum and student grades
        curriculum_df = get_curriculum(student['Course'])
        student_grades_df = get_student_subjects_grades(student['_id'])

        if not curriculum_df.empty:
            # Filter curriculum for the student's year level and selected semester
            subjects_to_enroll_df = curriculum_df[
                (curriculum_df['year'] == student['YearLevel']) &
                (curriculum_df['semester'] == selected_semester)
            ]

            passed_subjects = []
            if not student_grades_df.empty:
                passed_subjects = student_grades_df[student_grades_df['Grade'] <= 3.0]['Subject Code'].tolist()

            available_subjects = []
            blocked_subjects = []

            for _, subject in subjects_to_enroll_df.iterrows():
                prerequisites = subject.get('preRequisites', [])
                if not prerequisites or all(prereq in passed_subjects for prereq in prerequisites):
                    available_subjects.append(subject)
                else:
                    blocked_subjects.append(subject)

            st.subheader("Available Subjects for Enrollment")
            if available_subjects:
                available_subjects_df = pd.DataFrame(available_subjects)
                selected_subjects = st.multiselect(
                    "Select subjects to enroll",
                    options=available_subjects_df['code'].tolist(),
                    format_func=lambda x: f"{x} - {available_subjects_df.loc[available_subjects_df['code'] == x, 'name'].iloc[0]}"
                )

                if st.button("Finalize Enrollment"):
                    if selected_subjects:
                        st.session_state.confirm_enrollment = True
                        st.session_state.selected_subjects_to_enroll = selected_subjects

                if st.session_state.confirm_enrollment:
                    st.warning("Are you sure you want to finalize the enrollment for the selected subjects?")
                    if st.button("Yes, Finalize Enrollment"):
                        # Get semester ID
                        semester_doc = db.semesters.find_one({"SchoolYear": selected_school_year, "Semester": selected_semester})
                        if semester_doc:
                            semester_id = semester_doc['_id']
                            # Create a new entry in the grades collection
                            new_grades_entry = {
                                "StudentID": student['_id'],
                                "SemesterID": semester_id,
                                "SubjectCodes": st.session_state.selected_subjects_to_enroll,
                                "Grades": [-1] * len(st.session_state.selected_subjects_to_enroll),  # -1 for not yet graded
                                "Teachers": ["Not Set"] * len(st.session_state.selected_subjects_to_enroll)
                            }
                            db.grades.insert_one(new_grades_entry)
                            st.success("Enrollment finalized successfully!")
                            # Clear selected student and confirmation state to start a new enrollment
                            st.session_state['selected_student'] = None
                            st.session_state.confirm_enrollment = False
                            st.session_state.selected_subjects_to_enroll = []
                            st.rerun()
                        else:
                            st.error("Could not find the semester. Please check the school year and semester.")
            else:
                st.info("No subjects available for enrollment.")

            st.subheader("Blocked Subjects (Unmet Prerequisites)")
            if blocked_subjects:
                st.dataframe(pd.DataFrame(blocked_subjects))
            else:
                st.info("No blocked subjects.")
        else:
            st.warning("No curriculum found for this course.")
    else:
        st.info("Search for a student to begin the enrollment process.")
