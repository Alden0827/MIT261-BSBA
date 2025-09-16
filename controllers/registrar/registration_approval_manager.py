import streamlit as st

def registration_approval_manager_page(db):
    st.title("Registration Approvals")

    with st.spinner("Loading pending registrations..."):
        pending_registrations = list(db.registration.find({"status": "Pending"}))

    if not pending_registrations:
        st.info("No pending registrations found.")
        return

    for registration in pending_registrations:
        student_id = registration.get("studentId")
        if not student_id:
            st.warning(f"Skipping registration {registration['_id']} due to missing 'studentId'.")
            continue

        student = db.students.find_one({"_id": student_id})
        if not student:
            st.warning(f"Could not find student with ID: {student_id}")
            continue

        st.subheader(f"Student: {student.get('Name', 'N/A')}")
        st.write(f"Course: {student.get('Course', 'N/A')}")
        st.write(f"Year Level: {student.get('YearLevel', 'N/A')}")

        # Displaying registration details, if any
        st.write("Registration Details:")
        st.write(registration)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{registration['_id']}"):
                db.registration.update_one({"_id": registration["_id"]}, {"$set": {"status": "Approved"}})
                st.success(f"Registration for {student.get('Name', 'N/A')} approved.")
                st.rerun()
        with col2:
            if st.button("❌ Deny", key=f"deny_{registration['_id']}"):
                db.registration.update_one({"_id": registration["_id"]}, {"$set": {"status": "Denied"}})
                st.warning(f"Registration for {student.get('Name', 'N/A')} denied.")
                st.rerun()
