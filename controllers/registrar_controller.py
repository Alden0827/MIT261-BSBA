import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

def registrar_view(st, db):
    st.title("🎓 Registrar Dashboard")

    # Sidebar Menu
    menu = st.sidebar.radio(
        "Registrar Menu",
        [
            "📚 Curriculum Manager",
            "🗓 Semester Control",
            "📑 Class Scheduling",
            "🧑‍🎓 Enrollment Approvals",
            "📝 Grade Management",
            "📈 Reports"
        ]
    )

    # ---------------------------
    # 1️⃣ Curriculum Manager
    # ---------------------------
    if menu == "📚 Curriculum Manager":
        st.subheader("Curriculum Manager")


        st.markdown(
            """
            <style>
            .small-button > button {
                padding: 2px 6px;
                font-size: 0.8rem;
                height: auto;
                width: auto;
            }
            </style>
            """,
            unsafe_allow_html=True
        )


        st.subheader("📚 Curriculum Manager")

        # --- 1️⃣ Select existing curriculum OR create new ---
        col1, col2 = st.columns([3, 1])
        with col1:
            programs = list(db.curriculum.find())
            program_options = {f"{p['programCode']} - {p['programName']} ({p['curriculumYear']})": p for p in programs}
            selected_label = st.selectbox("Select Curriculum", [""] + list(program_options.keys()))

        # ✅ Modal using st.dialog
        @st.dialog("Create New Curriculum")
        def new_curriculum_dialog():
            with st.form("add_program"):
                code = st.text_input("Program Code")
                name = st.text_input("Program Name")
                year = st.text_input("Curriculum Year")
                if st.form_submit_button("Save Program"):
                    db.curriculum.insert_one({
                        "programCode": code,
                        "programName": name,
                        "curriculumYear": year,
                        "subjects": []
                    })
                    st.success("Program created successfully")
                    st.rerun()

        with col2:
            if st.button("➕ New Curriculum"):
                new_curriculum_dialog()

        # --- 2️⃣ Load selected program ---
        if selected_label:
            program_doc = program_options[selected_label]
            st.markdown(f"### Curriculum: SY {program_doc['curriculumYear']}")

            # Track which subject is being edited
            if "editing_subject" not in st.session_state:
                st.session_state.editing_subject = None

            # Group subjects by year/semester
            df = pd.DataFrame(program_doc["subjects"])
            if df.empty:
                st.info("No subjects yet. Add subjects below.")
            else:
                for year in sorted(set([s.get("year", 1) for s in program_doc["subjects"]])):
                    for sem in ["First", "Second", "Summer"]:
                        sem_df = df[(df["year"] == year) & (df["semester"] == sem)]
                        if not sem_df.empty:
                            with st.expander(f"Year {year} - {sem} Semester"):
                                for _, subj in sem_df.iterrows():
                                    col1, col2, col3, col4, col5, col6 = st.columns([2, 4,5,2, 1, 1])

                                    # Display subject info
                                    col1.write(subj["code"])
                                    col2.write(subj["name"])
                                    col3.markdown(
                                        f"""
                                        <span>Le: <b>{subj['lec']}</b></span> &nbsp;
                                        <span>Lab: <b>{subj['lab']}</b></span> &nbsp;
                                        <span>Unit: <b>{subj['unit']}</b></span>
                                        """,
                                        unsafe_allow_html=True
                                    )
                                    col4.write(", ".join(map(str, subj["preRequisites"])))  # ensures list → string

                                    try:
                                        if col5.button("✏️", key=f"edit_{subj['code']}"):
                                            st.session_state.editing_subject = subj["code"]

                                        if col6.button("🗑️", key=f"delete_{subj['code']}"):
                                            db.curriculum.update_one(
                                                {"_id": program_doc["_id"]},
                                                {"$pull": {"subjects": {"code": subj["code"]}}}
                                            )
                                            st.warning(f"Deleted {subj['code']}")
                                            st.rerun()

                                    except st.errors.StreamlitDuplicateElementKey:
                                        st.error(f"Duplicate key detected for subject {subj['code']}. Please ensure subject codes are unique.")

                                    # Show edit form if this subject is selected
                                    if st.session_state.editing_subject == subj["code"]:
                                        with st.form(f"edit_form_{subj['code']}"):
                                            new_name = st.text_input("Subject Name", subj["name"])
                                            new_lec = st.number_input("Lecture Units", min_value=0, max_value=10, value=int(subj["lec"]))
                                            new_lab = st.number_input("Lab Units", min_value=0, max_value=10, value=int(subj["lab"]))
                                            new_unit = new_lec + new_lab
                                            new_prereq = st.text_input("Prerequisites (comma-separated)", ",".join(subj["preRequisites"]))

                                            colE, colC = st.columns(2)
                                            with colE:
                                                if st.form_submit_button("💾 Save Changes"):
                                                    db.curriculum.update_one(
                                                        {"_id": program_doc["_id"], "subjects.code": subj["code"]},
                                                        {"$set": {
                                                            "subjects.$.name": new_name,
                                                            "subjects.$.lec": new_lec,
                                                            "subjects.$.lab": new_lab,
                                                            "subjects.$.unit": new_unit,
                                                            "subjects.$.preRequisites": [s.strip() for s in new_prereq.split(",") if s.strip()]
                                                        }}
                                                    )
                                                    st.success("Subject updated")
                                                    st.session_state.editing_subject = None
                                                    st.rerun()
                                            with colC:
                                                if st.form_submit_button("❌ Cancel"):
                                                    st.session_state.editing_subject = None
                                                    # st.rerun()
            # --- 4️⃣ Add Subject ---
            # --- 4️⃣ Add Subject ---
            with st.expander("➕ Add Subject", expanded=st.session_state.get("add_subject_open", True)):
                with st.form("add_subject"):
                    subj_code = st.text_input("Subject Code", key="subj_code").strip().upper()
                    subj_name = st.text_input("Subject Name", key="subj_name")
                    year = st.number_input("Year Level", min_value=1, max_value=5, value=1, key="subj_year")
                    semester = st.selectbox("Semester", ["First", "Second", "Summer"], key="subj_semester")
                    lec = st.number_input("Lecture Units", min_value=0, max_value=10, key="subj_lec")
                    lab = st.number_input("Lab Units", min_value=0, max_value=10, key="subj_lab")
                    prereq = st.text_input("Prerequisites (comma-separated)", key="subj_prereq")

                    if st.form_submit_button("Save Subject"):
                        subj_code_norm = subj_code.strip().upper()

                        program = db.curriculum.find_one({"_id": program_doc["_id"]})
                        existing_codes = {s["code"].strip().upper() for s in program.get("subjects", [])}

                        if not subj_code_norm:
                            st.error("❌ Subject Code is required")
                            st.session_state.add_subject_open = True
                        elif subj_code_norm in existing_codes:
                            st.warning(f"⚠️ Subject `{subj_code}` already exists. Cannot add duplicate.")
                            st.session_state.add_subject_open = True
                        else:
                            db.curriculum.update_one(
                                {"_id": program_doc["_id"]},
                                {"$push": {"subjects": {
                                    "year": year,
                                    "semester": semester,
                                    "code": subj_code_norm,
                                    "name": subj_name,
                                    "lec": lec,
                                    "lab": lab,
                                    "unit": lec + lab,
                                    "preRequisites": [s.strip().upper() for s in prereq.split(",") if s.strip()]
                                }}}
                            )
                            st.success(f"✅ Subject `{subj_code_norm}` added successfully")

                            st.session_state.add_subject_open = False

                            st.rerun()




    # ---------------------------
    # 2️⃣ Semester Control
    # ---------------------------
    elif menu == "🗓 Semester Control":
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
                st.experimental_rerun()

        # Update Semester Status
        if semesters:
            selected_sem = st.selectbox("Select Semester to Update", [s["_id"] for s in semesters])
            new_status = st.selectbox("New Status", ["OPEN", "CLOSED", "ONGOING", "COMPLETED"])
            if st.button("Update Status"):
                db.semester.update_one({"_id": selected_sem}, {"$set": {"status": new_status}})
                st.success("Semester status updated")
                st.experimental_rerun()

    # ---------------------------
    # 3️⃣ Class Scheduling
    # ---------------------------
    elif menu == "📑 Class Scheduling":
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
                st.experimental_rerun()

    # ---------------------------
    # 4️⃣ Enrollment Approvals
    # ---------------------------
    elif menu == "🧑‍🎓 Enrollment Approvals":
        st.subheader("Enrollment Approvals")
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
                    st.experimental_rerun()
            with col2:
                if st.button("❌ Deny", key=f"deny_{e['_id']}"):
                    db.enrollments.update_one({"_id": e["_id"]}, {"$set": {"status": "Denied"}})
                    st.warning("Enrollment denied")
                    st.experimental_rerun()

    # ---------------------------
    # 5️⃣ Grade Management
    # ---------------------------
    elif menu == "📝 Grade Management":
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
                st.experimental_rerun()

    # ---------------------------
    # 6️⃣ Reports
    # ---------------------------
    elif menu == "📈 Reports":
        st.subheader("Reports & Analytics")
        enrollments = list(db.enrollments.find({"status": "Enrolled"}))
        data = []
        for e in enrollments:
            student = db.students.find_one({"_id": e["studentId"]})
            data.append({"student": student["studentName"], "grade": e.get("grade", 0)})
        df = pd.DataFrame(data)
        if not df.empty:
            st.write("GPA per Student")
            fig, ax = plt.subplots()
            ax.bar(df["student"], df["grade"])
            ax.set_ylabel("Grade")
            ax.set_xlabel("Student")
            plt.xticks(rotation=45)
            st.pyplot(fig)

        # Enrollment Stats
        st.metric("Total Students", db.students.count_documents({}))
        st.metric("Currently Enrolled", db.enrollments.count_documents({"status": "Enrolled"}))
        st.metric("Total Classes", db.classSchedule.count_documents({}))