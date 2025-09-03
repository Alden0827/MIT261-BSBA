import pandas as pd

def curriculum_manager_page(st, db):

    st.markdown(
        """
        <style>
        .small-button > button {
            padding: 2px 6px;
            font-size: 0.8rem;
            height: auto;
            width: auto;
        }

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

    # --- 1️⃣ New Curriculum button ABOVE the selectbox ---
    new_btn = st.button("➕ New Curriculum", key="new_curriculum_btn", use_container_width=False)

    st.markdown(
        """
        <script>
        const btn = window.parent.document.querySelector('button[data-testid="baseButton-new_curriculum_btn"]');
        if (btn) { btn.classList.add('custom-btn'); }
        </script>
        """,
        unsafe_allow_html=True
    )

    if new_btn:
        new_curriculum_dialog()

    # --- Select existing curriculum ---
    programs = list(db.curriculum.find())
    program_options = {f"{p['programCode']} - {p['programName']} ({p['curriculumYear']})": p for p in programs}
    selected_label = st.selectbox("Select Curriculum", [""] + list(program_options.keys()))

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
                                col1, col2, col3, col4, col5, col6 = st.columns([2, 4, 5, 2, 1, 1])

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
                                col4.write(", ".join(map(str, subj["preRequisites"])))  # list → string

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
