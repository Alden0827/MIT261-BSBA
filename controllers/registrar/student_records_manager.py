import streamlit as st
from bson.objectid import ObjectId
from helpers.data_helper import get_students

def student_records_manager_page(st, db):
    st.subheader("🧑‍🎓 Student Records Manager")

    # --- Dialog for adding/editing a student ---
    def student_dialog(student=None):
        dialog_title = "Edit Student" if student else "Add New Student"
        with st.form("student_form", clear_on_submit=not student):
            st.subheader(dialog_title)

            name = st.text_input("Full Name", value=student.get("Name", "") if student else "")
            course = st.text_input("Course", value=student.get("Course", "") if student else "")
            year_level = st.number_input("Year Level", min_value=1, max_value=5,
                                         value=student.get("YearLevel", 1) if student else 1)

            if st.form_submit_button("Save"):
                student_data = {
                    "Name": name.strip(),
                    "Course": course.strip(),
                    "YearLevel": year_level
                }

                if student:
                    db.students.update_one({"_id": student["_id"]}, {"$set": student_data})
                    st.success("✅ Student updated successfully.")
                else:
                    last = db.students.find_one(sort=[("_id", -1)])
                    new_id = (last["_id"] + 1) if last else 1
                    student_data["_id"] = new_id
                    db.students.insert_one(student_data)
                    st.success("✅ Student added successfully.")

                st.rerun()

    if st.button("➕ Add New Student"):
        student_dialog()

    # --- Search bar ---
    search_query = st.text_input("🔍 Search students", placeholder="Enter keywords (e.g. 'Niel IT 1')")

    # --- Fetch all students ---
    # students = list(db.students.find())
    students = get_students().to_dict("records")

    if not students:
        st.info("No students found. Add a new student to get started.")
        return

    # --- Apply multi-keyword search filter ---
    if search_query.strip():
        keywords = search_query.lower().split()
        filtered = []
        for s in students:
            record_text = f"{s.get('_id', '')} {s.get('Name', '')} {s.get('Course', '')} {s.get('YearLevel', '')}".lower()
            if all(kw in record_text for kw in keywords):
                filtered.append(s)
        students = filtered

    # --- Pagination ---
    page_size = 10
    total_students = len(students)
    total_pages = (total_students - 1) // page_size + 1 if total_students > 0 else 1
    if "student_page" not in st.session_state:
        st.session_state.student_page = 1
    # Reset to page 1 if search changes
    if search_query and st.session_state.student_page != 1:
        st.session_state.student_page = 1

    col_prev, col_page, col_next = st.columns([1, 2, 1])
    with col_prev:
        if st.button("⬅️ Prev", disabled=st.session_state.student_page <= 1):
            st.session_state.student_page -= 1
            st.rerun()
    with col_page:
        st.markdown(f"**Page {st.session_state.student_page} of {total_pages}**")
    with col_next:
        if st.button("Next ➡️", disabled=st.session_state.student_page >= total_pages):
            st.session_state.student_page += 1
            st.rerun()

    # --- Slice students for current page ---
    start_idx = (st.session_state.student_page - 1) * page_size
    end_idx = start_idx + page_size
    students_page = students[start_idx:end_idx]

    # --- Table Header ---
    header_cols = st.columns([1, 4, 4, 2, 2])
    header_cols[0].markdown("**ID**")
    header_cols[1].markdown("**Name**")
    header_cols[2].markdown("**Course**")
    header_cols[3].markdown("**Year Level**")
    header_cols[4].markdown("**Actions**")
    st.markdown("---")

    # --- Table Rows ---
    if not students_page:
        st.warning("No student records match your search.")
    else:
        for student in students_page:
            row = st.columns([1, 4, 4, 2, 2])
            row[0].write(student.get("_id", "N/A"))
            row[1].write(student.get("Name", "N/A"))
            row[2].write(student.get("Course", "N/A"))
            row[3].write(student.get("YearLevel", "N/A"))

            edit_col, delete_col = row[4].columns(2)
            if edit_col.button("✏️", key=f"edit_{student['_id']}"):
                student_dialog(student)
            if delete_col.button("🗑️", key=f"delete_{student['_id']}"):
                db.students.delete_one({"_id": student["_id"]})
                st.warning(f"Deleted student {student.get('Name', 'Unknown')}")
                st.rerun()
