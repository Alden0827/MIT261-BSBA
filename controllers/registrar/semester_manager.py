
import pandas as pd
def semester_manager_page(st,db): 
    st.subheader("Semester Control")

    semesters = list(db.semester.find())
    if semesters:
        df = pd.DataFrame(semesters)[["schoolYear", "term", "status"]]
        st.dataframe(df)
    else:
        st.info("No semesters found.")

    # Add Semester
    with st.form("add_semester"):
        sy = st.text_input("School Year")
        term = st.selectbox("Term", ["1st Semester", "2nd Semester", "Summer"])
        status = st.selectbox("Status", ["OPEN", "CLOSED", "ONGOING", "COMPLETED"])
        if st.form_submit_button("Save Semester"):
            db.semester.insert_one({"schoolYear": sy, "term": term, "status": status})
            st.success("Semester added")
            st.rerun()

    # Update Semester Status
    if semesters:
        selected_sem = st.selectbox("Select Semester to Update", [s["_id"] for s in semesters])
        new_status = st.selectbox("New Status", ["OPEN", "CLOSED", "ONGOING", "COMPLETED"])
        if st.button("Update Status"):
            db.semester.update_one({"_id": selected_sem}, {"$set": {"status": new_status}})
            st.success("Semester status updated")
            st.rerun()
