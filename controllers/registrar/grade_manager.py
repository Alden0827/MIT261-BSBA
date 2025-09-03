def grade_manager_page(st,db):
    '''
    Receiving and officially recording grades submitted by faculty.
    Maintaining the official academic records (transcripts, report cards, etc.).
    Implementing institutional policies on grade submission deadlines, changes, and disputes.
    Securing and archiving grade data for compliance and accreditation.
    '''
    st.subheader("Grade Management")
    enrollments = list(db.enrollments.find({"status": "Enrolled"}))
    if not enrollments:
        st.info("No grades to manage")
    for e in enrollments:
        student = db.students.find_one({"_id": e["studentId"]})
        class_off = db.classSchedule.find_one({"_id": e["classOfferingId"]})
        st.write(f"{student['studentName']} → {class_off['section']}")
        grade = st.number_input("Grade", min_value=1.0, max_value=5.0, value=e.get("grade") or 1.0, step=0.25, key=f"grade_{e['_id']}")
        status = st.selectbox("Status", ["PASSED", "FAILED", "INC"], index=["PASSED", "FAILED", "INC"].index(e.get("status") or "PASSED"), key=f"status_{e['_id']}")
        if st.button("Save Grade", key=f"save_{e['_id']}"):
            db.enrollments.update_one({"_id": e["_id"]}, {"$set": {"grade": grade, "status": status}})
            st.success("Grade saved")
            st.rerun()