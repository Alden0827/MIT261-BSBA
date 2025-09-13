import pandas as pd
import streamlit as st

# ----------------- Dialogs -----------------
@st.dialog("Add Semester")
def add_semester_dialog(db):
    st.write("### New Semester")
    sy = st.number_input("School Year", step=1, format="%d")
    sem = st.selectbox("Semester", ["FirstSem", "SecondSem", "Summer"])

    if st.button("Save Semester"):
        # Check duplicate (SchoolYear + Semester)
        existing = db.semesters.find_one({
            "SchoolYear": int(sy),
            "Semester": sem
        })

        if existing:
            st.error(f"Semester {sy} - {sem} already exists.")
        else:
            # Compute next _id
            last = db.semesters.find_one(sort=[("_id", -1)])
            next_id = (last["_id"] + 1) if last else 1

            db.semesters.insert_one({
                "_id": next_id,
                "SchoolYear": int(sy),
                "Semester": sem
            })
            st.success("Semester added")
            st.rerun()

@st.dialog("Edit Semester")
def edit_semester_dialog(db, sem):
    st.write("### Edit Semester")
    new_sy = st.number_input("School Year", value=sem["SchoolYear"], step=1, format="%d")
    new_sem = st.selectbox(
        "Semester", ["FirstSem", "SecondSem", "Summer"],
        index=["FirstSem", "SecondSem", "Summer"].index(sem["Semester"])
    )
    if st.button("Update"):
        db.semesters.update_one(
            {"_id": sem["_id"]},
            {"$set": {"SchoolYear": int(new_sy), "Semester": new_sem}}
        )
        st.success("Semester updated")
        st.rerun()

@st.dialog("Delete Semester")
def delete_semester_dialog(db, sem):
    st.write(f"⚠️ Are you sure you want to delete **{sem['SchoolYear']} - {sem['Semester']}**?")
    if st.button("Yes, Delete"):
        db.semesters.delete_one({"_id": sem["_id"]})
        st.success("Semester deleted")
        st.rerun()

# ----------------- Main Page -----------------
def semester_manager_page(st, db):
    st.subheader("Semester Control")

    if st.button("➕ Add Semester"):
        add_semester_dialog(db)


    semesters = list(db.semesters.find())
    if semesters:
        # Only keep the fields in your schema
        df = pd.DataFrame(semesters)[["_id", "SchoolYear", "Semester"]]
        
        st.write("### Semester List")

        for i, row in df.iterrows():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            col1.write(row["SchoolYear"])
            col2.write(row["Semester"])

            if col3.button("✏️ Edit", key=f"edit_{row['_id']}"):
                sem = db.semesters.find_one({"_id": row["_id"]})
                edit_semester_dialog(db, sem)

            if col4.button("🗑️ Delete", key=f"delete_{row['_id']}"):
                sem = db.semesters.find_one({"_id": row["_id"]})
                delete_semester_dialog(db, sem)
    else:
        st.info("No semesters found.")



# sample semesters collection
# {
#   "_id": 16,
#   "Semester": "FirstSem",
#   "SchoolYear": 2025
# },

# {
#   "_id": 17,
#   "Semester": "SecondSem",
#   "SchoolYear": 2025
# },
# {
#   "_id": 18,
#   "Semester": "Summer",
#   "SchoolYear": 2025
# }