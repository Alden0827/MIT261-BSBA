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
    student_options = {0: ""}
    student_options.update(student_names)

    selected_student_id = st.selectbox(
        "Select Student",
        options=list(student_options.keys()),
        format_func=lambda x: student_options[x],
    )

    if selected_student_id:
        st.subheader(f"Editing Grades for: {student_options[selected_student_id]} [{selected_student_id}]")

        # Fetch all grade docs for this student
        grades_docs = list(db.grades.find({"StudentID": selected_student_id}))

        if not grades_docs:
            st.warning("No grades found for this student.")
            return

        semester_order = {"FirstSem": 1, "SecondSem": 2, "Summer": 3}
        semester_grade_data = []

        # Process each grade document
        for grades_doc in grades_docs:
            semester_id = grades_doc.get("SemesterID")
            sem_doc = db.semesters.find_one({"_id": semester_id})

            if sem_doc:
                sem_label = f"{sem_doc['Semester']} {sem_doc['SchoolYear']}"
                sem_year = sem_doc["SchoolYear"]
                sem_rank = semester_order.get(sem_doc["Semester"], 99)
            else:
                sem_label = f"Semester {semester_id}"
                sem_year = 9999
                sem_rank = 99

            grade_data = []
            for i, subject_code in enumerate(grades_doc.get("SubjectCodes", [])):
                current_teacher = grades_doc["Teachers"][i] if i < len(grades_doc["Teachers"]) else "N/A"

                if current_teacher == teacher_name:
                    subject_info = db.subjects.find_one({"_id": subject_code})
                    grade_data.append({
                        "Subject Code": subject_code,
                        "Description": subject_info["Description"] if subject_info else "N/A",
                        "Grade": grades_doc["Grades"][i],
                        "Status": grades_doc["Status"][i]
                    })

            # Skip semesters with no subjects for this teacher
            if not grade_data:
                continue

            semester_grade_data.append({
                "year": sem_year,
                "rank": sem_rank,
                "label": sem_label,
                "grades_doc": grades_doc,
                "grade_data": grade_data
            })

        # Sort semesters chronologically
        semester_grade_data.sort(key=lambda x: (x["year"], x["rank"]))

        # Render each semester
        for sem in semester_grade_data:
            st.markdown(f"### {sem['label']}")

            df = pd.DataFrame(sem["grade_data"])
            grades_doc = sem["grades_doc"]

            # --- Editable Table ---
            for i, row in df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 4, 1, 2, 1])

                with col1:
                    st.text(row["Subject Code"])
                with col2:
                    st.text(row["Description"])
                with col3:
                    new_grade = st.number_input(
                        "Grade",
                        value=row["Grade"],
                        key=f"grade_{grades_doc['_id']}_{i}",
                        label_visibility="collapsed"
                    )
                with col4:
                    new_status = st.selectbox(
                        "Status",
                        options=["", "Final", "INC"],
                        index=["", "Final", "INC"].index(row["Status"]),
                        key=f"status_{grades_doc['_id']}_{i}",
                        label_visibility="collapsed"
                    )
                with col5:
                    if st.button("Delete", key=f"delete_{grades_doc['_id']}_{i}"):
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

                # Update DataFrame with new values
                df.at[i, "Grade"] = new_grade
                df.at[i, "Status"] = new_status

            if st.button("Save Changes", key=f"save_{grades_doc['_id']}"):
                for index, row in df.iterrows():
                    subject_code_to_update = row["Subject Code"]
                    subject_index = grades_doc["SubjectCodes"].index(subject_code_to_update)

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
                with st.form(f"add_grade_form_{grades_doc['_id']}"):
                    all_subjects = db.subjects.find({"Teacher": teacher_name})
                    graded_subjects = grades_doc.get("SubjectCodes", [])
                    available_subjects = {
                        s["_id"]: f"{s['_id']} - {s['Description']}"
                        for s in all_subjects if s["_id"] not in graded_subjects
                    }

                    if not available_subjects:
                        st.warning("No more subjects to add for this student.")
                    else:
                        selected_subject = st.selectbox(
                            "Select Subject",
                            options=list(available_subjects.keys()),
                            format_func=lambda x: available_subjects[x]
                        )
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
