import streamlit as st
import pandas as pd
from itertools import zip_longest
from streamlit_echarts import st_echarts

def get_subjects_by_teacher(db, teacher_name, batch_size=1000):
    """
    Returns a DataFrame of subjects handled by a specific teacher.
    Ensures consistent columns: [Subject Code, Description, Units, Teacher, CourseCode(optional)].
    """
    cursor = db.subjects.find(
        {"Teacher": teacher_name},
        {"_id": 1, "Description": 1, "Units": 1, "Teacher": 1, "CourseCode": 1}
    )

    docs, chunks = [], []
    for i, doc in enumerate(cursor, 1):
        docs.append(doc)
        if i % batch_size == 0:
            chunks.append(pd.DataFrame(docs))
            docs = []

    if docs:
        chunks.append(pd.DataFrame(docs))

    df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    expected_cols = ["Subject Code", "Description", "Units", "Teacher", "CourseCode"]
    if not df.empty:
        if "_id" in df.columns:
            df = df.rename(columns={"_id": "Subject Code"})
        df["Subject Code"] = df["Subject Code"].astype(str)

    for col in expected_cols:
        if col not in df.columns:
            df[col] = ""

    # Return columns in stable order
    return df[expected_cols] if not df.empty else pd.DataFrame(columns=expected_cols)


def subject_difficulty_page(db):
    """
    Full, robust Subject Difficulty page:
    - filters by semester (or All)
    - counts only the teacher's subjects/rows
    - zips SubjectCodes/Grades/Teachers/Status to keep them aligned
    - computes Fail Rate (%) and Dropout Rate (%) per subject
    - shows table + heatmap + CSV download
    """
    st.markdown("### 📊 Subject Difficulty Report")
    st.markdown("Visualizes subjects with high failure or dropout rates handled by the faculty.")

    # teacher from session (or allow manual input for testing)
    teacher_name = st.session_state.get("fullname", "")
    if not teacher_name:
        teacher_name = st.text_input("Teacher full name (for testing)", value="")
        if not teacher_name:
            st.warning("Please set `st.session_state['fullname']` or enter a name for testing.")
            return

    # load collections
    with st.spinner("Loading data...", show_time=True):
        semesters_list = list(db.semesters.find())
        subjects_df = get_subjects_by_teacher(db, teacher_name)
        grades_list = list(db.grades.find())
        # student info map (for possible future drilldowns)
        students_list = list(db.students.find())

    # semesters -> DataFrame + map
    if not semesters_list:
        st.warning("No semester data found.")
        return

    semesters_df = pd.DataFrame(semesters_list)
    if "_id" in semesters_df.columns:
        semesters_df = semesters_df.rename(columns={"_id": "SemesterID"})
    for c in ["SemesterID", "Semester", "SchoolYear"]:
        if c not in semesters_df.columns:
            semesters_df[c] = ""

    # normalize strings
    semesters_df["SemesterID"] = semesters_df["SemesterID"].astype(str)
    semesters_df["Semester"] = semesters_df["Semester"].astype(str)
    semesters_df["SchoolYear"] = semesters_df["SchoolYear"].astype(str)

    semester_labels = (semesters_df["Semester"] + " " + semesters_df["SchoolYear"]).tolist()
    # map label -> list of semester ids (some systems may have duplicates)
    semester_map = {}
    for sid, label in zip(semesters_df["SemesterID"].tolist(), semester_labels):
        semester_map.setdefault(label, []).append(str(sid))

    semester_options = ["All Semesters"] + list(semester_map.keys())
    selected_semester_label = st.selectbox("📅 Select Semester", semester_options)

    # build set of semester ids to include
    if selected_semester_label == "All Semesters":
        selected_semester_ids = set(semesters_df["SemesterID"].astype(str).tolist())
    else:
        selected_semester_ids = set(semester_map.get(selected_semester_label, []))

    if not selected_semester_ids:
        st.info("No semester IDs resolved for selection.")
        return

    # ensure we have the teacher's subject codes list
    if subjects_df.empty:
        st.info("You have no subjects assigned.")
        return

    subj_codes_handled = set(subjects_df["Subject Code"].astype(str).tolist())
    subj_desc_map = dict(zip(subjects_df["Subject Code"].astype(str), subjects_df["Description"].astype(str)))

    # build students map for possible lookup
    students_map = {str(s.get("_id")): s for s in students_list}

    # Flatten grades list by zipping parallel arrays — robust and lossless
    flat_rows = []
    for gdoc in grades_list:
        sid = gdoc.get("StudentID")
        sid_s = str(sid) if sid is not None else ""
        sem_raw = gdoc.get("SemesterID", "")
        sem_s = str(sem_raw)

        # if this grade doc's semester is not in the selected set -> skip early
        if sem_s not in selected_semester_ids:
            continue

        subject_codes = gdoc.get("SubjectCodes", []) or []
        grades = gdoc.get("Grades", []) or []
        teachers = gdoc.get("Teachers", []) or []
        status = gdoc.get("Status", []) or []

        # iterate indices, use zip_longest so we won't lose mis-sized arrays (use None for missing)
        for subj, grd, tchr, stat in zip_longest(subject_codes, grades, teachers, status, fillvalue=None):
            subj_s = str(subj).strip() if subj is not None else ""
            tchr_s = str(tchr).strip() if tchr is not None else ""
            # only include entries for this teacher (ensures teacher filter works)
            if tchr_s != teacher_name:
                continue
            # only consider subjects that the teacher handles (extra guard)
            if subj_s not in subj_codes_handled:
                continue

            # coerce grade to numeric if possible, else None
            try:
                grd_num = float(grd) if grd is not None and str(grd).strip() != "" else None
            except Exception:
                grd_num = None

            flat_rows.append({
                "StudentID": sid_s,
                "SemesterID": sem_s,
                "SubjectCode": subj_s,
                "Grade": grd_num,
                "Status": str(stat) if stat is not None else "",
                "Teacher": tchr_s
            })

    # if no rows found after applying teacher+semester filters
    if not flat_rows:
        st.info("No grade rows found for this teacher in the selected semester(s).")
        return

    flat_df = pd.DataFrame(flat_rows)

    # helper counters
    def count_fails(df_slice, passing_threshold=75):
        if df_slice.empty:
            return 0
        # prefer explicit Status column if it uses e.g. 'Failed'
        if df_slice["Status"].astype(str).str.contains("fail", case=False, na=False).any():
            return df_slice[df_slice["Status"].astype(str).str.contains("fail", case=False, na=False)]["StudentID"].nunique()
        # else use numeric Grades (< passing threshold)
        if "Grade" in df_slice.columns:
            mask = pd.to_numeric(df_slice["Grade"], errors="coerce") < passing_threshold
            return df_slice[mask]["StudentID"].nunique()
        return 0

    def count_dropouts(df_slice):
        if df_slice.empty:
            return 0
        if df_slice["Status"].astype(str).str.contains("drop", case=False, na=False).any():
            return df_slice[df_slice["Status"].astype(str).str.contains("drop", case=False, na=False)]["StudentID"].nunique()
        # fallback: missing grade might indicate dropout (best-effort)
        if "Grade" in df_slice.columns:
            return df_slice[df_slice["Grade"].isna()]["StudentID"].nunique()
        return 0

    # Build summary per subject the teacher handles (even if no rows for some subjects)
    rows = []
    for subj_code in sorted(subj_codes_handled):
        subj_rows = flat_df[flat_df["SubjectCode"].astype(str) == subj_code]
        total_students = subj_rows["StudentID"].nunique() if not subj_rows.empty else 0
        fails = count_fails(subj_rows)
        dropouts = count_dropouts(subj_rows)

        fail_rate = round((fails / total_students) * 100, 2) if total_students else 0.0
        dropout_rate = round((dropouts / total_students) * 100, 2) if total_students else 0.0

        if fail_rate >= 20 or dropout_rate >= 10:
            difficulty = "High"
        elif fail_rate >= 10 or dropout_rate >= 5:
            difficulty = "Medium"
        else:
            difficulty = "Low"

        rows.append({
            "Course Code": subj_code,
            "Course Name": subj_desc_map.get(subj_code, ""),
            "Fail Rate (%)": fail_rate,
            "Dropout Rate (%)": dropout_rate,
            "Difficulty Level": difficulty,
            "Total": total_students
        })

    summary_df = pd.DataFrame(rows)

    # show table
    display_cols = ["Course Code", "Course Name", "Fail Rate (%)", "Dropout Rate (%)", "Difficulty Level", "Total"]
    st.markdown("### 📋 Subject Difficulty Table")
    st.dataframe(summary_df[display_cols].sort_values(by=["Fail Rate (%)", "Dropout Rate (%)"], ascending=False).reset_index(drop=True))

    # build heatmap data in the shape [xName, yName, value] (ECharts accepts category names)
    subject_codes = summary_df["Course Code"].tolist()
    y_categories = ["Fail Rate (%)", "Dropout Rate (%)"]
    heatmap_data = []
    for _, r in summary_df.iterrows():
        heatmap_data.append([r["Course Code"], "Fail Rate (%)", float(r["Fail Rate (%)"])])
        heatmap_data.append([r["Course Code"], "Dropout Rate (%)", float(r["Dropout Rate (%)"])])

    heatmap_options = {
        "tooltip": {
            # no python % formatting here, plain JS string
            "formatter": """function (params) {
                // params.value = [xName, yName, value] when using category names
                var subj = params.value[0] || params.name || '';
                var metric = params.value[1] || '';
                var value = params.value[2] || 0;
                return params.marker + subj + '<br/>' + metric + ': ' + value + '%';
            }"""
        },
        "grid": {"height": "60%", "top": "10%"},
        "xAxis": {"type": "category", "data": subject_codes, "axisLabel": {"rotate": 45, "interval": 0}},
        "yAxis": {"type": "category", "data": y_categories},
        "visualMap": {"min": 0, "max": 100, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "0"},
        "series": [{
            "name": "Subject Difficulty",
            "type": "heatmap",
            "data": heatmap_data,
            "label": {"show": True},
            "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)"}}
        }]
    }

    st.markdown("### 🔥 Subject Difficulty Heatmap")
    st_echarts(options=heatmap_options, height="480px")

    # CSV download
    csv = summary_df[display_cols].to_csv(index=False).encode("utf-8")
    safe_label = selected_semester_label.replace(" ", "_")
    st.download_button("Download CSV", data=csv, file_name=f"subject_difficulty_{teacher_name}_{safe_label}.csv", mime="text/csv")


if __name__ == "__main__":
    pass