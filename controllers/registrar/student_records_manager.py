import streamlit as st
import pandas as pd
from bson.objectid import ObjectId

def student_records_manager_page(st, db):
    st.subheader("🧑‍🎓 Student Records Manager")

    # --- Fetch Curricula ---
    curricula = list(db.curriculum.find())
    curriculum_options = {f"{c['programCode']} ({c['curriculumYear']})": c['_id'] for c in curricula}
    curriculum_id_to_name = {v: k for k, v in curriculum_options.items()}

    # --- Dialog for adding/editing a student ---
    def student_dialog(student=None):
        dialog_title = "Edit Student" if student else "Add New Student"
        with st.form("student_form"):
            st.subheader(dialog_title)
            student_id = st.text_input("Student ID", value=student['student_id'] if student else "")
            first_name = st.text_input("First Name", value=student['first_name'] if student else "")
            last_name = st.text_input("Last Name", value=student['last_name'] if student else "")

            default_curricula = []
            if student and 'curricula' in student:
                default_curricula = [curriculum_id_to_name.get(c_id) for c_id in student['curricula'] if curriculum_id_to_name.get(c_id)]

            selected_curricula_names = st.multiselect(
                "Assign Curricula",
                list(curriculum_options.keys()),
                default=default_curricula
            )

            if st.form_submit_button("Save"):
                student_curricula_ids = [curriculum_options[name] for name in selected_curricula_names]

                student_data = {
                    "student_id": student_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "curricula": student_curricula_ids
                }

                if student:
                    db.students.update_one({"_id": student['_id']}, {"$set": student_data})
                    st.success("Student updated successfully.")
                else:
                    db.students.insert_one(student_data)
                    st.success("Student added successfully.")

                st.rerun()

    if st.button("➕ Add New Student"):
        student_dialog()

    # --- Display existing students ---
    students = list(db.students.find())

    if not students:
        st.info("No students found. Add a new student to get started.")
        return

    for student in students:
        col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 3, 4, 1, 1])

        with col1:
            st.write(student.get("student_id", "N/A"))
        with col2:
            st.write(student.get("first_name", "N/A"))
        with col3:
            st.write(student.get("last_name", "N/A"))
        with col4:
            assigned_curricula = [curriculum_id_to_name.get(c_id, "Unknown") for c_id in student.get("curricula", [])]
            st.write(", ".join(assigned_curricula))
        with col5:
            if st.button("✏️", key=f"edit_{student['_id']}"):
                student_dialog(student)
        with col6:
            if st.button("🗑️", key=f"delete_{student['_id']}"):
                db.students.delete_one({"_id": student['_id']})
                st.rerun()
        st.markdown("---")
