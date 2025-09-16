import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Helpers
# from helpers.data_helper import (
#     get_school_years,
#     get_semester_names,
#     get_courses,
#     get_curriculum,
#     get_student_subjects_grades,
# )

import helpers.data_helper as dh


from helpers.registration_helper import find_best_match
    
# ---------------------------
# Main Enrollment Manager Page
# ---------------------------
def enrollment_manager_page(db):
    r = dh.data_helper({"db": db})
    st.title("Enrollment Manager")

    with st.spinner("Loading school years...", show_time=True):
        school_years = r.get_school_years()
    with st.spinner("Loading semesters...", show_time=True):
        semester_names = r.get_semester_names()
    with st.spinner("Loading Courses...", show_time=True):
        courses = r.get_courses()

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
            # matches = find_best_match(search_query, course=selected_course, collection=students_col)
            matches = find_best_match(query=search_query, course=selected_course, collection=students_col)


            if matches:
                st.session_state.search_results = matches
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
            key="student_selector"
        )

        if selected_id != st.session_state.selected_student_id:
            st.session_state.selected_student_id = selected_id
            st.session_state.selected_student = db["students"].find_one({"_id": selected_id})

    # Display Student Info
    student = st.session_state.selected_student
    if student:
        st.subheader("👩‍🎓 Student Information")
        st.write(f"**Name:** {student.get('Name', 'N/A')}")
        st.write(f"**Course:** {student.get('Course', 'N/A')}")
        st.write(f"**Year Level:** {student.get('YearLevel', 'N/A')}")

        # Get Curriculum & Grades
        curriculum_df = r.get_curriculum(student.get("Course"))
        student_grades_df = r.get_student_subjects_grades(student.get("_id"))
        print('selected_semester:',selected_semester)
        print("Curriculum columns:", curriculum_df.columns.tolist())
        print("Student grades columns:", student_grades_df.columns.tolist())
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
            # print('curriculum_df:',curriculum_df.head(1))
            # potential_subjects = curriculum_df[
            #     (curriculum_df["semester"] == selected_semester.replace('Sem',''))
            #     & (curriculum_df["year"] == student.get("YearLevel"))
            #     & (~curriculum_df["Subject Code"].isin(student_grades_df["Subject Code"].tolist()))
            # ].copy()

            # normalize col names (good practice)
            curriculum_df.columns = curriculum_df.columns.str.strip()

            # handle if student_grades_df is empty
            if not student_grades_df.empty and "Subject Code" in student_grades_df.columns:
                taken_subjects = student_grades_df["Subject Code"].tolist()
            else:
                taken_subjects = []

            potential_subjects = curriculum_df[
                (curriculum_df["semester"].str.lower() == selected_semester.replace("Sem", "").lower())
                & (curriculum_df["year"] == student.get("YearLevel"))
                & (~curriculum_df["Subject Code"].isin(taken_subjects))
            ].copy()

            available_subjects, blocked_subjects = [], []
            for _, row in potential_subjects.iterrows():
                prerequisites = row.get("preRequisites", [])
                if not prerequisites or all(prereq in passed_subjects for prereq in prerequisites):
                    available_subjects.append(row)
                else:
                    blocked_subjects.append(row)

            available_subjects_df = pd.DataFrame(available_subjects)
            blocked_subjects_df = pd.DataFrame(blocked_subjects)

            # ✅ Available Subjects
            st.subheader("✅ Available Subjects")
            if not available_subjects_df.empty:
                st.dataframe(available_subjects_df[["Subject Code", "Description", "unit"]])

                selected_subjects = st.multiselect(
                    "Select subjects to enroll",
                    options=available_subjects_df["Subject Code"].tolist(),
                    format_func=lambda x: f"{x} - {available_subjects_df.loc[available_subjects_df['Subject Code'] == x, 'Description'].iloc[0]}",
                )

                # 🔹 Define the confirmation dialog
                @st.dialog("Confirm Enrollment")
                def confirm_enrollment_dialog():
                    st.write("⚠️ Please review your enrollment before confirming:")

                    # --- Available Subjects Table ---
                    if selected_subjects:
                        available_confirmation_df = pd.DataFrame({
                            "Subject Code": selected_subjects,
                            "Description": [
                                available_subjects_df.loc[
                                    available_subjects_df["Subject Code"] == s, "Description"
                                ].iloc[0] for s in selected_subjects
                            ],
                            "Units": [
                                available_subjects_df.loc[
                                    available_subjects_df["Subject Code"] == s, "unit"
                                ].iloc[0] for s in selected_subjects
                            ],
                            "Prerequisites": [
                                available_subjects_df.loc[
                                    available_subjects_df["Subject Code"] == s, "preRequisites"
                                ].iloc[0] for s in selected_subjects
                            ]
                        })

                        # Apply styling for prerequisites
                        def style_prerequisites(prereq_list):
                            if not prereq_list:
                                return ""
                            styled = []
                            for prereq in prereq_list:
                                if prereq in passed_subjects:
                                    styled.append(f"✅ {prereq}")
                                else:
                                    styled.append(f"❌ {prereq}")
                            return ", ".join(styled)

                        available_confirmation_df["Prerequisites"] = available_confirmation_df["Prerequisites"].apply(style_prerequisites)
                        st.subheader("✅ Selected Subjects")
                        st.dataframe(available_confirmation_df.style.set_properties(**{'text-align': 'left'}))

                        # Total units
                        total_units = available_confirmation_df["Units"].sum()
                        st.write(f"**Total Units:** {total_units}")

                    # --- Blocked Subjects Table ---
                    if not blocked_subjects_df.empty:
                        blocked_confirmation_df = pd.DataFrame({
                            "Subject Code": blocked_subjects_df["Subject Code"],
                            "Description": blocked_subjects_df["Description"],
                            "Units": blocked_subjects_df["unit"],
                            "Prerequisites": blocked_subjects_df["preRequisites"]
                        })
                        blocked_confirmation_df["Prerequisites"] = blocked_confirmation_df["Prerequisites"].apply(style_prerequisites)
                        st.subheader("⛔ Blocked Subjects")
                        st.dataframe(blocked_confirmation_df.style.set_properties(**{'text-align': 'left'}))

                    # --- Confirm / Cancel Buttons ---
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Yes, Confirm"):
                            semester_doc = db.semesters.find_one(
                                {"SchoolYear": selected_school_year, "Semester": selected_semester}
                            )
                            if semester_doc:
                                semester_id = semester_doc["_id"]
                                new_grades_entry = {
                                    "StudentID": student["_id"],
                                    "SemesterID": semester_id,
                                    "SubjectCodes": selected_subjects,
                                    "Grades": [-1] * len(selected_subjects),
                                    "Teachers": ["Not Set"] * len(selected_subjects),
                                }
                                db.grades.insert_one(new_grades_entry)
                                st.success("🎉 Enrollment finalized successfully!")
                                # Reset session state
                                st.session_state.selected_student = None
                                st.session_state.selected_student_id = None
                                st.session_state.confirm_enrollment = False
                                st.session_state.selected_subjects_to_enroll = []
                                st.session_state.search_results = []
                                st.rerun()
                            else:
                                st.error("Semester not found. Please check school year/semester.")
                    with col2:
                        if st.button("❌ Cancel"):
                            st.session_state.confirm_enrollment = False
                            st.info("Enrollment cancelled.")

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
                print('blocked_subjects_df:',blocked_subjects_df)
                st.dataframe(blocked_subjects_df[["Subject Code", "Description", "unit", "preRequisites"]])
            else:
                st.info("No blocked subjects.")
        else:
            st.warning("No curriculum found for this course.")
    else:
        st.info("Search for a student to begin enrollment.")


if __name__ == "__main__":

    pass