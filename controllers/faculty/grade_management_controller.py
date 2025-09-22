import streamlit as st
import pandas as pd
from helpers.faculty_helper import get_students_for_teacher

def grade_management_page(db):
    st.title("Student Grade Management")

    teacher_name = st.session_state.get("fullname", "")
    if not teacher_name:
        st.warning("Could not determine teacher's name from session.")
        return

    st.markdown(f"👩‍🏫 Faculty: **{teacher_name}**")

    students = get_students_for_teacher(db, teacher_name)
    if not students:
        st.info("No students found for this teacher.")
        return

    student_names = {s["_id"]: s["Name"] for s in students}

    # Prepend a blank option to the dictionary of student names
    student_options = {0: ""}
    student_options.update(student_names)

    selected_student_id = st.selectbox("Select Student", options=list(student_options.keys()), format_func=lambda x: student_options[x])

    if selected_student_id:
        st.subheader(f"Editing Grades for: {student_options[selected_student_id]}")

        grades_doc = db.grades.find_one({"StudentID": selected_student_id})

        if grades_doc:
            # Create a list of dictionaries for the data editor
            grade_data = []
            for i, subject_code in enumerate(grades_doc["SubjectCodes"]):
                # Find the teacher for the current subject
                current_teacher = grades_doc["Teachers"][i] if i < len(grades_doc["Teachers"]) else "N/A"

                # Only allow editing if the logged-in teacher is the teacher for the subject
                if current_teacher == teacher_name:
                    subject_info = db.subjects.find_one({"_id": subject_code})
                    grade_data.append({
                        "Subject Code": subject_code,
                        "Description": subject_info["Description"] if subject_info else "N/A",
                        "Grade": grades_doc["Grades"][i],
                        "Status": grades_doc["Status"][i]
                    })

            if not grade_data:
                st.info("This student has no subjects assigned to you.")
                return

            # --- Grade Table ---
            df = pd.DataFrame(grade_data)

            for i, row in df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 4, 1, 2, 1])

                with col1:
                    st.text(row["Subject Code"])
                with col2:
                    st.text(row["Description"])
                with col3:
                    new_grade = st.number_input("Grade", value=row["Grade"], key=f"grade_{i}", label_visibility="collapsed")
                with col4:
                    new_status = st.selectbox("Status", options=["", "Final", "INC"], index=["", "Final", "INC"].index(row["Status"]), key=f"status_{i}", label_visibility="collapsed")
                with col5:
                    if st.button("Delete", key=f"delete_{i}"):
                        # Pull the element from the arrays
                        db.grades.update_one(
                            {"_id": grades_doc["_id"]},
                            {
                                "$pull": {
                                    "SubjectCodes": row["Subject Code"],
                                    "Grades": row["Grade"],
                                    "Teachers": teacher_name,
                                    "Status": row["Status"]
                                }
                            }
                        )
                        st.success(f"Grade for {row['Subject Code']} deleted successfully!")
                        st.rerun()

                # Update the DataFrame with the new values
                df.at[i, "Grade"] = new_grade
                df.at[i, "Status"] = new_status


            if st.button("Save Changes"):
                # Update the grades in the database
                for index, row in df.iterrows():
                    subject_code_to_update = row["Subject Code"]

                    # Find the index of the subject in the original grades document
                    subject_index = grades_doc["SubjectCodes"].index(subject_code_to_update)

                    # Update the grade and status
                    db.grades.update_one(
                        {"_id": grades_doc["_id"]},
                        {
                            "$set": {
                                f"Grades.{subject_index}": row["Grade"],
                                f"Status.{subject_index}": row["Status"]
                            }
                        }
                    )
                st.success("Grades updated successfully!")
                st.rerun()

            # --- Add Grade Form ---
            with st.expander("➕ Add New Grade"):
                with st.form("add_grade_form"):
                    # Get subjects not yet graded for the student
                    all_subjects = db.subjects.find({"Teacher": teacher_name})
                    graded_subjects = grades_doc.get("SubjectCodes", [])
                    available_subjects = {
                        s["_id"]: f"{s['_id']} - {s['Description']}"
                        for s in all_subjects if s["_id"] not in graded_subjects
                    }

                    if not available_subjects:
                        st.warning("No more subjects to add for this student.")
                    else:
                        selected_subject = st.selectbox("Select Subject", options=list(available_subjects.keys()), format_func=lambda x: available_subjects[x])
                        new_grade = st.number_input("Enter Grade", min_value=0, max_value=100, step=1)

                        submitted = st.form_submit_button("Add Grade")
                        if submitted:
                            db.grades.update_one(
                                {"_id": grades_doc["_id"]},
                                {
                                    "$push": {
                                        "SubjectCodes": selected_subject,
                                        "Grades": new_grade,
                                        "Teachers": teacher_name,
                                        "Status": ""
                                    }
                                }
                            )
                            st.success(f"Grade for {selected_subject} added successfully!")
                            st.rerun()

        else:
            st.warning("No grades found for this student.")
