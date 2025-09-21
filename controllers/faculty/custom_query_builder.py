import streamlit as st
import pandas as pd
from itertools import zip_longest

def custom_query_builder_page(db):
    """
    📋 Custom Query Builder
    Allows users to build filtered queries on student grades.
    Example: Show all students with <75 in CS101.
    """

    st.markdown("### 🔎 Custom Query Builder")
    st.markdown("Build a custom query to filter student performance.")

    # --- Load collections ---
    with st.spinner("Loading data..."):
        students_df = pd.DataFrame(list(db.students.find()))
        grades_list = list(db.grades.find())
        subjects_df = pd.DataFrame(list(db.subjects.find()))
        semesters_df = pd.DataFrame(list(db.semesters.find()))

    if students_df.empty or not grades_list or subjects_df.empty or semesters_df.empty:
        st.warning("⚠️ Missing data in one or more collections.")
        return

    # --- Normalize ---
    students_df = students_df.rename(columns={"_id": "StudentID"})
    subjects_df = subjects_df.rename(columns={"_id": "SubjectCode"})
    semesters_df = semesters_df.rename(columns={"_id": "SemesterID"})

    # Build semester labels
    semesters_df["Label"] = semesters_df["Semester"].astype(str) + " " + semesters_df["SchoolYear"].astype(str)
    semester_map = dict(zip(semesters_df["SemesterID"].astype(str), semesters_df["Label"]))

    # --- Filters ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        selected_sem = st.selectbox("📅 Semester", ["All"] + list(semester_map.values()))
    with col2:
        selected_subject = st.selectbox("📘 Subject", ["All"] + subjects_df["SubjectCode"].astype(str).tolist())
    with col3:
        operator = st.selectbox("Operator", ["<", ">", "<=", ">=", "<>"])
    with col4:
        grade_value = st.number_input("Grade", min_value=0, max_value=100, value=75)

    # --- Query Execution ---
    if st.button("Run Query"):
        st.info(f"Current Query: **Show all students with {operator} {grade_value}"
                f"{' in ' + selected_subject if selected_subject != 'All' else ''}"
                f"{' for ' + selected_sem if selected_sem != 'All' else ''}**")

        records = []

        with st.spinner("Fetching information base on query.", show_time = True):
            for gdoc in grades_list:
                sem_id = str(gdoc.get("SemesterID", ""))
                sem_label = semester_map.get(sem_id, "Unknown")

                # filter semester
                if selected_sem != "All" and sem_label != selected_sem:
                    continue

                sid = gdoc.get("StudentID")
                for subj, grd in zip_longest(
                    gdoc.get("SubjectCodes", []),
                    gdoc.get("Grades", []),
                    fillvalue=None
                ):
                    subj = str(subj) if subj else ""
                    grd_val = float(grd) if grd is not None and str(grd).strip() != "" else None

                    # filter subject
                    if selected_subject != "All" and subj != selected_subject:
                        continue

                    # apply operator
                    if grd_val is None:
                        continue
                    match = False
                    if operator == "<": match = grd_val < grade_value
                    elif operator == ">": match = grd_val > grade_value
                    elif operator == "<=": match = grd_val <= grade_value
                    elif operator == ">=": match = grd_val >= grade_value
                    elif operator == "<>": match = grd_val != grade_value

                    if match:
                        student_row = students_df[students_df["StudentID"] == sid]
                        if not student_row.empty:
                            student_name = student_row["Name"].values[0]
                        else:
                            student_name = "Unknown"

                        subj_desc = subjects_df.loc[subjects_df["SubjectCode"] == subj, "Description"]
                        subj_name = subj_desc.values[0] if not subj_desc.empty else "Unknown"

                        records.append({
                            "StudentID": sid,
                            "Name": student_name,
                            "Subject Code": subj,
                            "Subject": subj_name,
                            "Grade": f"{grd_val:.0f}%"
                        })

        if not records:
            st.warning("⚠️ No matching records found.")
            return

        result_df = pd.DataFrame(records)
        st.success(f"✅ Found {len(result_df)} matching records")
        st.dataframe(result_df)

        # --- Export ---
        csv = result_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv,
            file_name=f"custom_query_results.csv",
            mime="text/csv"
        )
