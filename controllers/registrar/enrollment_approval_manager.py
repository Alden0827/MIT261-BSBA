import streamlit as st
def enrollment_approval_manager_page(db):
    st.subheader("Enrollment Approvals")
    with st.spinner(f"Loading metadata...", show_time=True):
        pending = list(db.enrollments.find({"status": "Pending"}))
    if not pending:
        st.info("No pending enrollments")
    for e in pending:
        student = db.students.find_one({"_id": e["studentId"]})
        class_off = db.classSchedule.find_one({"_id": e["classOfferingId"]})
        st.write(f"{student['studentName']} → {class_off['section']}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Approve", key=f"approve_{e['_id']}"):
                db.enrollments.update_one({"_id": e["_id"]}, {"$set": {"status": "Enrolled"}})
                st.success("Enrollment approved")
                st.rerun()
        with col2:
            if st.button("❌ Deny", key=f"deny_{e['_id']}"):
                db.enrollments.update_one({"_id": e["_id"]}, {"$set": {"status": "Denied"}})
                st.warning("Enrollment denied")
                st.rerun()