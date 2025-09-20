import streamlit as st
import pandas as pd

def teacher_subjects_page(db, teacher_name: str):
    """
    Displays list of handled subjects for a given teacher.
    """
    st.subheader(f"📘 Subjects handled by {teacher_name}")

    # Get subjects assigned to this teacher
    subjects = list(db.subjects.find({"Teacher": teacher_name}))

    if not subjects:
        st.info("No subjects assigned yet.")
        return

    rows = []
    for subj in subjects:
        subj_code = subj["_id"]
        subj_name = subj.get("Description", "")
        units = subj.get("Units", 0)

        # If Lec/Lab is not explicitly stored, split Units or default to Lec only
        lec = subj.get("Lec", units)   # assume all units as Lec if not provided
        lab = subj.get("Lab", 0)

        # Count number of students taking this subject
        student_count = db.grades.count_documents({"SubjectCodes": subj_code})

        rows.append({
            "Subject Code": subj_code,
            "Subject": subj_name,
            "Lec": lec,
            "Lab": lab,
            "Unit": units,
            "Number of Students": student_count
        })

    # Convert to DataFrame for nicer display
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True)

def class_scheduler_manager_page(db):
    st.subheader("Class Scheduling")

    # Load metadata
    with st.spinner(f"Loading metadata...", show_time=True):
        unassigned_subjects = list(db.subjects.find({}))  # only those without teacher
        teachers = list(db.userAccounts.find({"role": "teacher"}))
        semesters = list(db.semester.find())

    # Assign Teacher to Subject
    st.markdown("### Assign Teacher to Subject")
    if not unassigned_subjects:
        st.info("✅ All subjects already have teachers assigned.")
    else:
        with st.form("assign_teacher_form"):
            subject_sel = st.selectbox(
                "Unassigned Subject",
                [f"{s['_id']} - {s['Description']}" for s in unassigned_subjects]
            )
            teacher_sel = st.selectbox(
                "Teacher",
                [t["fullName"] for t in teachers]
            )

            if st.form_submit_button("Assign Teacher"):
                subj_id = subject_sel.split(" - ")[0]
                teacher = next(t for t in teachers if t["fullName"] == teacher_sel)
                # semester = next(s for s in semesters if f"{s['term']} {s['schoolYear']}" == semester_sel)

                # Update subject with teacher name
                db.subjects.update_one(
                    {"_id": subj_id},
                    {"$set": {"Teacher": teacher["fullName"]}}
                )
                st.success(f"✅ {teacher['fullName']} assigned to {subj_id}")
                st.rerun()

    st.subheader("Assignments")
    st.dataframe(unassigned_subjects)
    # st.rerun()
