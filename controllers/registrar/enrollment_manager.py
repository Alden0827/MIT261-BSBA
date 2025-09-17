import streamlit as st
import pandas as pd
import sys
import os
from bson import ObjectId
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# Helpers
import helpers.data_helper as dh
import helpers.registration_helper as rh

def normalize_enrollees(docs):
    rows = []
    for d in docs:
        row = {}
        for k, v in d.items():
            # Convert ObjectId → str
            if isinstance(v, ObjectId):
                row[k] = str(v)
            # Convert numpy scalars → Python native
            elif isinstance(v, (np.generic,)):
                row[k] = v.item()
            # Convert list of dicts (like subjects) → comma separated string
            elif isinstance(v, list):
                row[k] = ", ".join([str(x) for x in v])
            # Convert dict (like registeredBy, discardedBy) → JSON string
            elif isinstance(v, dict):
                row[k] = ", ".join(f"{kk}: {vv}" for kk, vv in v.items())
            else:
                row[k] = v
        rows.append(row)
    return pd.DataFrame(rows)
def enrollment_manager_page(db):
    st.title("Enrollment Manager")

    # --- Pre-load data ---
    r = dh.data_helper({"db": db})
    with st.spinner("Loading school years...", show_time=True):
        school_years = r.get_school_years()
    with st.spinner("Loading semesters...", show_time=True):
        semester_names = r.get_semester_names()
    with st.spinner("Loading Courses...", show_time=True):
        courses = r.get_courses()

    # --- Initialize session state variables ---
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

    tab1, tab2, tab3, tab4 = st.tabs([
        "Student Search & Enroll",
        "Pending Approval",
        "Enrolled Students",
        "Discarded Enrollments"
    ])

    with tab1:
        st.header("Student Search & Enroll")

        # Dropdowns for filters
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_school_year = st.selectbox("School Year", school_years, key="tab1_sy")
        with col2:
            selected_semester = st.selectbox("Semester", semester_names, key="tab1_sem")
        with col3:
            selected_course = st.selectbox("Course", courses, key="tab1_course")

        # Student Search
        st.subheader("🔍 Student Search")
        search_query = st.text_input("Enter student name", key="tab1_search")

        if st.button("Search", key="tab1_search_btn"):
            st.session_state.confirm_enrollment = False
            st.session_state.selected_student = None
            st.session_state.selected_student_id = None

            if search_query.strip():
                students_col = db["students"]
                matches = rh.find_best_match(query=search_query, course=selected_course, collection=students_col)
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

            if not curriculum_df.empty:
                passed_subjects = []
                if not student_grades_df.empty:
                    passed_subjects = student_grades_df[student_grades_df["Grade"] >= 75]["Subject Code"].tolist()

                curriculum_df.columns = curriculum_df.columns.str.strip()

                taken_subjects = []
                if not student_grades_df.empty and "Subject Code" in student_grades_df.columns:
                    taken_subjects = student_grades_df["Subject Code"].tolist()

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

                st.subheader("✅ Available Subjects")
                if not available_subjects_df.empty:
                    st.dataframe(available_subjects_df[["Subject Code", "Description", "unit"]])
                    selected_subjects = st.multiselect(
                        "Select subjects to enroll",
                        options=available_subjects_df["Subject Code"].tolist(),
                        format_func=lambda x: f"{x} - {available_subjects_df.loc[available_subjects_df['Subject Code'] == x, 'Description'].iloc[0]}",
                    )

                    if st.button("Submit for Approval"):
                        if selected_subjects:
                            semester_doc = db.semesters.find_one({
                                "SchoolYear": selected_school_year,
                                "Semester": selected_semester
                            })
                            if semester_doc:
                                semester_id = semester_doc["_id"]
                                student_id = student["_id"]
                                registrar_user = {"_id": "registrar1", "fullName": "Registrar User"} # Dummy user

                                # Check if already enrolled
                                if rh.is_already_enrolled(student_id, semester_id):
                                    st.warning(f"Student is already enrolled or has a pending enrollment for this semester.")
                                else:
                                    pending_id = rh.add_pending_enrollee(
                                        student_id=student_id,
                                        semester_id=semester_id,
                                        subject_codes=selected_subjects,
                                        registered_by_user=registrar_user
                                    )
                                    if pending_id:
                                        st.success(f"Enrollment submitted for approval with ID: {pending_id}")
                                        # Clear fields after submission
                                        st.session_state.selected_student = None
                                        st.session_state.selected_student_id = None
                                        st.session_state.search_results = []
                                        st.rerun()
                                    else:
                                        st.error("Failed to submit enrollment.")
                            else:
                                st.error("Could not find the selected semester.")
                        else:
                            st.warning("Please select subjects to enroll.")
                else:
                    st.info("No subjects available for enrollment.")

                st.subheader("⛔ Blocked Subjects")
                if not blocked_subjects_df.empty:
                    st.dataframe(blocked_subjects_df[["Subject Code", "Description", "unit", "preRequisites"]])
                else:
                    st.info("No blocked subjects.")
            else:
                st.warning("No curriculum found for this course.")
        else:
            st.info("Search for a student to begin enrollment.")

    with tab2:
        st.header("Pending Enrollments for Approval")

        # Filters
        col1, col2 = st.columns(2)
        with col1:
            sy_pending = st.selectbox("School Year", school_years, key="pending_sy")
        with col2:
            sem_pending = st.selectbox("Semester", semester_names, key="pending_sem")

        semester_doc = db.semesters.find_one({"SchoolYear": sy_pending, "Semester": sem_pending})
        if semester_doc:
            semester_id = semester_doc["_id"]

            pending_df = rh.get_pending_enrollees(semester_id=semester_id)

            if not pending_df.empty:
                st.write("Select a student to approve or discard their enrollment.")
                selected_pending = st.dataframe(pending_df, on_select="rerun", selection_mode="single-row")

                if selected_pending.selection['rows']:
                    selected_row_index = selected_pending.selection['rows'][0]
                    selected_student_id = pending_df.iloc[selected_row_index]['StudentID']

                    st.subheader(f"Action for Student ID: {selected_student_id}")

                    # Approve Button
                    if st.button("Approve Enrollment", key=f"approve_{selected_student_id}"):
                        approver_user = {"_id": "approver1", "fullName": "Approver User"} # Dummy user

                        # We need all subject codes for the approval
                        enrollment_doc = db.enrollments.find_one({"studentId": int(selected_student_id), "semesterId": int(semester_id), "status": "Pending"})
                        if enrollment_doc:
                            subject_codes = [s['subjectCode'] for s in enrollment_doc.get('subjects', [])]
                            approved_id = rh.approve_enrollee(
                                student_id=selected_student_id,
                                semester_id=semester_id,
                                subject_codes=subject_codes,
                                approved_by_user=approver_user
                            )
                            if approved_id:
                                st.success(f"Enrollment approved for student {selected_student_id}")
                                st.rerun()
                            else:
                                st.error("Failed to approve enrollment.")
                        else:
                            st.error("Could not find the pending enrollment details.")

                    # Discard Button
                    reason = st.text_input("Reason for Discarding", key=f"discard_reason_{selected_student_id}")
                    if st.button("Discard Enrollment", key=f"discard_{selected_student_id}"):
                        if reason.strip():
                            discarded_by_user = {"_id": "registrar1", "fullName": "Registrar User"} # Dummy user
                            success = rh.discard_pending_enrollee(
                                student_id=selected_student_id,
                                semester_id=semester_id,
                                discarded_by_user=discarded_by_user,
                                reason=reason
                            )
                            if success:
                                st.success(f"Enrollment for student {selected_student_id} has been discarded.")
                                st.rerun()
                            else:
                                st.error("Failed to discard enrollment.")
                        else:
                            st.warning("Please provide a reason for discarding.")
            else:
                st.info("No pending enrollments for the selected semester.")
        else:
            st.warning("Please select a valid school year and semester.")

    with tab3:
        st.header("Manage Enrolled Students")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            sy_enrolled = st.selectbox("School Year", school_years, key="enrolled_sy")
        with col2:
            sem_enrolled = st.selectbox("Semester", semester_names, key="enrolled_sem")
        with col3:
            course_enrolled = st.selectbox("Course", ["All"] + courses, key="enrolled_course")

        semester_doc = db.semesters.find_one({"SchoolYear": sy_enrolled, "Semester": sem_enrolled})
        if semester_doc:
            semester_id = semester_doc["_id"]

            course_filter = course_enrolled if course_enrolled != "All" else None
            enrolled_df = rh.get_enrolled_students(course=course_filter, semester_id=semester_id)

            if not enrolled_df.empty:
                st.write("Select a student to update their enrollment.")
                selected_enrolled = st.dataframe(enrolled_df, on_select="rerun", selection_mode="single-row")

                if selected_enrolled.selection['rows']:
                    selected_row_index = selected_enrolled.selection['rows'][0]
                    student_id = enrolled_df.iloc[selected_row_index]['StudentID']

                    st.subheader(f"Update Enrollment for Student ID: {student_id}")

                    enrollment_doc = db.enrollments.find_one({"studentId": student_id, "semesterId": semester_id, "status": "Enrolled"})
                    if enrollment_doc:
                        current_subjects = [s['subjectCode'] for s in enrollment_doc.get('subjects', [])]

                        # UI to add/drop subjects
                        st.write("**Current Subjects:**", ", ".join(current_subjects))

                        # Get available subjects for adding
                        student_doc = db.students.find_one({"_id": student_id})
                        curriculum_df = r.get_curriculum(student_doc.get("Course"))
                        if not curriculum_df.empty:
                            # This logic is simplified, in a real scenario it would be more complex
                            all_subjects = curriculum_df["Subject Code"].tolist()
                            available_to_add = [s for s in all_subjects if s not in current_subjects]

                            add_subjects = st.multiselect("Subjects to Add", available_to_add)
                            drop_subjects = st.multiselect("Subjects to Drop", current_subjects)

                            if st.button("Update Enrollment"):
                                if add_subjects or drop_subjects:
                                    updater_user = {"_id": "updater1", "fullName": "Registrar Updater"}
                                    success = rh.update_enrollment(
                                        student_id=student_id,
                                        semester_id=semester_id,
                                        add_subjects=add_subjects,
                                        drop_subjects=drop_subjects,
                                        updated_by_user=updater_user
                                    )
                                    if success:
                                        st.success("Enrollment updated successfully.")
                                        st.rerun()
                                    else:
                                        st.error("Failed to update enrollment.")
                                else:
                                    st.warning("No changes selected.")
                        else:
                            st.warning("Could not load curriculum to find available subjects.")
            else:
                st.info("No enrolled students found for the selected criteria.")
        else:
            st.warning("Please select a valid school year and semester.")

    with tab4:
        st.header("Discarded Enrollment Requests")

        # Filters
        col1, col2 = st.columns(2)
        with col1:
            sy_discarded = st.selectbox("School Year", school_years, key="discarded_sy")
        with col2:
            sem_discarded = st.selectbox("Semester", semester_names, key="discarded_sem")

        semester_doc = db.semesters.find_one({"SchoolYear": sy_discarded, "Semester": sem_discarded})
        if semester_doc:
            semester_id = semester_doc["_id"]
            discarded_docs = list(db.enrollments.find({"semesterId": semester_id, "status": "Discarded"}))
            discarded_df = normalize_enrollees(discarded_docs)

            if not discarded_df.empty:
                st.dataframe(discarded_df)
            else:
                st.info("No discarded enrollments found for the selected semester.")
        else:
            st.warning("Please select a valid school year and semester.")