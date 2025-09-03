
def class_scheduler_manager_page(st,db):

    st.subheader("Class Scheduling")
    programs = list(db.curriculum.find())
    faculty_list = list(db.faculty.find())
    semesters = list(db.semester.find())

    with st.form("add_class_schedule"):
        subject_codes = [s["code"] for p in programs for s in p.get("subjects", [])]
        subj_code = st.selectbox("Subject", subject_codes)
        faculty_names = [f["facultyName"] for f in faculty_list]
        faculty_name = st.selectbox("Faculty", faculty_names)
        semester_terms = [f"{s['term']} {s['schoolYear']}" for s in semesters]
        semester_sel = st.selectbox("Semester", semester_terms)
        section = st.text_input("Section")
        if st.form_submit_button("Save Class Schedule"):
            subj = next((s for p in programs for s in p.get("subjects", []) if s["code"]==subj_code), None)
            fac = next(f for f in faculty_list if f["facultyName"]==faculty_name)
            sem = next(s for s in semesters if f"{s['term']} {s['schoolYear']}"==semester_sel)
            db.classSchedule.insert_one({
                "subjectId": subj.get("_id", None),
                "facultyId": fac["_id"],
                "semesterId": sem["_id"],
                "section": section,
                "schedule": []
            })
            st.success("Class schedule added")
            st.rerun()
