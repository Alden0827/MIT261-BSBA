import pandas as pd

def curriculum_manager_page(st, db):
    # --- Custom button CSS ---
    st.markdown(
        """
        <style>
        div[data-testid="stButton"] > button.custom-btn {
            background-color: #4CAF50;
            color: white;
            padding: 10px 18px;
            font-size: 15px;
            font-weight: bold;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: 0.3s;
        }
        div[data-testid="stButton"] > button.custom-btn:hover {
            background-color: #45a049;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.subheader("📚 Curriculum Manager")

    # ✅ Dialog for Curriculum
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

    # ✅ Dialog for Add Subject
    @st.dialog("Add Subject")
    def add_subject_dialog(program_doc):
        with st.form("add_subject"):
            subj_code = st.text_input("Subject Code").strip().upper()
            subj_name = st.text_input("Subject Name")
            year = st.number_input("Year Level", min_value=1, max_value=5, value=1)
            semester = st.selectbox("Semester", ["First", "Second", "Summer"])
            lec = st.number_input("Lecture Units", min_value=0, max_value=10)
            lab = st.number_input("Lab Units", min_value=0, max_value=10)
            prereq = st.text_input("Prerequisites (comma-separated)")

            if st.form_submit_button("Save Subject"):
                subj_code_norm = subj_code.strip().upper()

                program = db.curriculum.find_one({"_id": program_doc["_id"]})
                existing_codes = {s["code"].strip().upper() for s in program.get("subjects", [])}

                if not subj_code_norm:
                    st.error("❌ Subject Code is required")
                elif subj_code_norm in existing_codes:
                    st.warning(f"⚠️ Subject `{subj_code}` already exists. Cannot add duplicate.")
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
                    st.rerun()

    # --- Buttons Row (side by side) ---
    colA, colB = st.columns([1, 1])
    with colA:
        new_btn = st.button("➕ New Curriculum", key="new_curriculum_btn")
        if new_btn:
            new_curriculum_dialog()

    with colB:
        st.session_state.add_subject_trigger = False  # default

    # --- Select existing curriculum ---
    programs = list(db.curriculum.find())
    program_options = {f"{p['programCode']} - {p['programName']} ({p['curriculumYear']})": p for p in programs}
    selected_label = st.selectbox(
        "Select Curriculum",
        ["Select Curriculum"] + list(program_options.keys()),
    )

    if selected_label and selected_label != "Select Curriculum":
        program_doc = program_options[selected_label]

        # Show Add Subject button only when curriculum selected
        if colB.button("➕ Add Subject", key="add_subject_btn"):
            add_subject_dialog(program_doc)

        st.markdown(f"### Curriculum: SY {program_doc['curriculumYear']}")

        # --- Subjects Display ---
        if "editing_subject" not in st.session_state:
            st.session_state.editing_subject = None

        df = pd.DataFrame(program_doc["subjects"])
        if df.empty:
            st.info("No subjects yet. Use ➕ Add Subject.")
        else:
            for year in sorted(set([s.get("year", 1) for s in program_doc["subjects"]])):
                for sem in ["First", "Second", "Summer"]:
                    sem_df = df[(df["year"] == year) & (df["semester"] == sem)]
                    if not sem_df.empty:
                        with st.expander(f"Year {year} - {sem} Semester",  expanded=True):
                            for _, subj in sem_df.iterrows():
                                col1, col2, col3, col4, col5, col6 = st.columns([2, 4, 5, 2, 1, 1])

                                # Display subject info
                                col1.write(subj["code"])
                                col2.write(subj["name"])
                                col3.markdown(
                                    f"""
                                    <span>Lec: <b>{subj['lec']}</b></span> &nbsp;
                                    <span>Lab: <b>{subj['lab']}</b></span> &nbsp;
                                    <span>Unit: <b>{subj['unit']}</b></span>
                                    """,
                                    unsafe_allow_html=True
                                )
                                col4.write("Prerequisites:" + ", ".join(map(str, subj["preRequisites"])))

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
                                    st.error(f"Duplicate key detected for subject {subj['code']}.")

                                # Show edit form if selected
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
