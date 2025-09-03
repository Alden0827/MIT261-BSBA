import pandas as pd
import streamlit as st
from bson.objectid import ObjectId

# ----------------- Dialogs -----------------
@st.dialog("Add Semester")
def add_semester_dialog(db):
    st.write("### New Semester")
    sy = st.text_input("School Year")
    term = st.selectbox("Term", ["1st Semester", "2nd Semester", "Summer"])
    status = st.selectbox("Status", ["OPEN", "CLOSED", "ONGOING", "COMPLETED"])
    if st.button("Save Semester"):
        db.semester.insert_one({"schoolYear": sy, "term": term, "status": status})
        st.success("Semester added")
        st.rerun()

@st.dialog("Edit Semester")
def edit_semester_dialog(db, sem):
    st.write("### Edit Semester")
    new_sy = st.text_input("School Year", sem["schoolYear"])
    new_term = st.selectbox(
        "Term", ["1st Semester", "2nd Semester", "Summer"],
        index=["1st Semester", "2nd Semester", "Summer"].index(sem["term"])
    )
    new_status = st.selectbox(
        "Status", ["OPEN", "CLOSED", "ONGOING", "COMPLETED"],
        index=["OPEN", "CLOSED", "ONGOING", "COMPLETED"].index(sem["status"])
    )
    if st.button("Update"):
        db.semester.update_one(
            {"_id": sem["_id"]},
            {"$set": {"schoolYear": new_sy, "term": new_term, "status": new_status}}
        )
        st.success("Semester updated")
        st.rerun()

@st.dialog("Change Status")
def change_status_dialog(db, sem):
    st.write(f"### Change Status for {sem['schoolYear']} - {sem['term']}")
    new_status = st.selectbox(
        "New Status", ["OPEN", "CLOSED", "ONGOING", "COMPLETED"],
        index=["OPEN", "CLOSED", "ONGOING", "COMPLETED"].index(sem["status"])
    )
    if st.button("Confirm Update"):
        db.semester.update_one({"_id": sem["_id"]}, {"$set": {"status": new_status}})
        st.success("Semester status changed")
        st.rerun()

@st.dialog("Delete Semester")
def delete_semester_dialog(db, sem):
    st.write(f"⚠️ Are you sure you want to delete **{sem['schoolYear']} - {sem['term']}**?")
    if st.button("Yes, Delete"):
        db.semester.delete_one({"_id": sem["_id"]})
        st.success("Semester deleted")
        st.rerun()

# ----------------- Main Page -----------------
def semester_manager_page(st, db):
    st.subheader("Semester Control")

    semesters = list(db.semester.find())
    if semesters:
        df = pd.DataFrame(semesters)[["_id", "schoolYear", "term", "status"]]
        
        st.write("### Semester List")

        for i, row in df.iterrows():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 2, 4])
            col1.write(row["schoolYear"])
            col2.write(row["term"])
            col3.write(row["status"])

            if col4.button("✏️ Edit", key=f"edit_{row['_id']}"):
                sem = db.semester.find_one({"_id": ObjectId(row["_id"])})
                edit_semester_dialog(db, sem)

            if col5.button("🗑️ Delete", key=f"delete_{row['_id']}"):
                sem = db.semester.find_one({"_id": ObjectId(row["_id"])})
                delete_semester_dialog(db, sem)

            if col6.button("🔄 Change Status", key=f"status_{row['_id']}"):
                sem = db.semester.find_one({"_id": ObjectId(row["_id"])})
                change_status_dialog(db, sem)
    else:
        st.info("No semesters found.")

    if st.button("➕ Add Semester"):
        add_semester_dialog(db)
