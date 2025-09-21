import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
from helpers.data_helper import data_helper

def get_subjects_by_teacher(db,teacher_name, batch_size=1000):
    """
    Returns a DataFrame of subjects handled by a specific teacher.
    Ensures consistent columns: [Subject Code, Description, Units, Teacher].
    """
    cursor = db.subjects.find(
        {"Teacher": teacher_name},   # filter by teacher
        {"_id": 1, "Description": 1, "Units": 1, "Teacher": 1}  # projection
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

    if not df.empty:
        if "_id" in df.columns:
            df.rename(columns={"_id": "Subject Code"}, inplace=True)
            df["Subject Code"] = df["Subject Code"].astype(str)

        # Guarantee schema
        for col in ["Description", "Units", "Teacher"]:
            if col not in df.columns:
                df[col] = ""

    return df

def student_progress_tracker_page(db):
    """
    Displays the Student Progress Tracker report page.
    """
    st.markdown("### 📈 Student Progress Tracker")
    st.markdown("Shows longitudinal performance for individual students.")

    # --- Data Helper ---
    dh = data_helper(db)

    # --- Filters (Sidebar) ---
    teacher_name = st.session_state.get("fullname", "")

    # st.sidebar.header("Filters")
    with st.spinner("Loading teacher's handled Subjects...", show_time=True):
        year_levels = [""] + dh.get_year_levels()
        courses = [""] + dh.get_courses()
        subjects_df = get_subjects_by_teacher(db, teacher_name)

    if "Subject Code" in subjects_df.columns:
        subject_list = [""] + subjects_df["Subject Code"].tolist()
    elif "Code" in subjects_df.columns:  # fallback
        subject_list = [""] + subjects_df["Code"].tolist()
    else:
        subject_list = []
        st.warning("⚠️ No subject code column found in subjects_df.")

    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)
        with col3:
            selected_subject = st.selectbox("Filter by Subject", subject_list)


    # --- Main Page Button ---
    if st.button("Generate Report"):   # <── now in main page
        with st.spinner("Fetching student progress data...", show_time = True):

            progress_data = get_student_progress_data(
                db, selected_course, selected_year_level, selected_subject
            )

        if progress_data.empty:
            st.warning("No data found for the selected filters.")
            return

        # --- Display DataFrame with Styling ---
        st.markdown("### Student GPA Progress")

        def style_trend(val):
            color_map = {
                "Improving": "color: green",
                "Need Attention": "color: red",
                "Stable High": "color: blue",
                "Consistently Low": "color: orange",
                "Stable": "color: black",
                "N/A": "color: grey"
            }
            return color_map.get(val, "")

        display_df = progress_data.fillna('-')
        st.dataframe(display_df.style.applymap(style_trend, subset=['Overall Trend']))

        # --- ECharts Visualizations ---
        st.markdown("---")
        st.markdown("### Visualizations")

        # --- Line Chart ---
        st.markdown("#### GPA Trend - Line Chart")
        gpa_cols = [col for col in progress_data.columns if ' ' in col]
        line_options = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": progress_data['Name'].tolist()},
            "xAxis": {"type": "category", "data": gpa_cols},
            "yAxis": {"type": "value", "name": "GPA"},
            "series": [],
        }
        for _, row in progress_data.iterrows():
            line_options["series"].append({
                "name": row['Name'],
                "type": "line",
                "data": [row.get(c, None) for c in gpa_cols],
            })
        st_echarts(options=line_options, height="500px")

        # --- Scatter Chart ---
        st.markdown("#### GPA Progress - Scatter Chart")
        if len(gpa_cols) >= 2:
            first_sem, last_sem = gpa_cols[0], gpa_cols[-1]
            scatter_data = progress_data[[first_sem, last_sem, 'Name']].dropna()

            scatter_options = {
                "xAxis": {"type": "value", "name": f"GPA ({first_sem})"},
                "yAxis": {"type": "value", "name": f"GPA ({last_sem})"},
                "tooltip": {"trigger": 'item', "formatter": "{b}: ({c})"},
                "series": [{
                    "name": 'Student Progress',
                    "type": 'scatter',
                    "data": [
                        {"value": [row[first_sem], row[last_sem]], "name": row['Name']}
                        for _, row in scatter_data.iterrows()
                    ],
                    "symbolSize": 15,
                }]
            }
            st_echarts(options=scatter_options, height="500px")
        else:
            st.info("Scatter plot requires at least two semesters of data.")



def get_student_progress_data(db, course, year_level, subject_code):
    """
    Fetches and processes data to generate the student progress report.
    """
    students_df = pd.DataFrame(list(db.students.find()))
    grades_df = pd.DataFrame(list(db.grades.find()))
    subjects_df = pd.DataFrame(list(db.subjects.find()))
    semesters_df = pd.DataFrame(list(db.semesters.find()))

    if grades_df.empty or subjects_df.empty or students_df.empty or semesters_df.empty:
        print("⚠️ One of the collections is empty.")
        return pd.DataFrame()

    students_df = students_df.rename(columns={'_id': 'StudentID'})
    subjects_df = subjects_df.rename(columns={'_id': 'SubjectCode'})
    semesters_df = semesters_df.rename(columns={'_id': 'SemesterID'})

    # filter students
    if course:
        students_df = students_df[students_df['Course'] == course]
    if year_level:
        students_df = students_df[students_df['YearLevel'] == year_level]

    # explode grades
    if isinstance(grades_df.get("SubjectCodes").iloc[0], list):
        grades_exploded = grades_df.explode(['SubjectCodes', 'Grades', 'Teachers'])
    else:
        grades_exploded = grades_df.copy()
    grades_exploded = grades_exploded.rename(columns={'SubjectCodes': 'SubjectCode'})

    # filter subject
    if subject_code:
        students_who_took_subject = grades_exploded[grades_exploded['SubjectCode'] == subject_code]['StudentID'].unique()
        students_df = students_df[students_df['StudentID'].isin(students_who_took_subject)]

    # merge grades with subjects
    grades_with_units = pd.merge(grades_exploded, subjects_df[['SubjectCode', 'Units']], on='SubjectCode', how="left")
    grades_with_units['GradePoints'] = grades_with_units['Grades'] * grades_with_units['Units']

    gpa_df = grades_with_units.groupby(['StudentID', 'SemesterID']).apply(
        lambda x: pd.Series({'GPA': x['GradePoints'].sum() / x['Units'].sum() if x['Units'].sum() else None})
    ).reset_index()

    # pivot
    gpa_pivot = gpa_df.pivot(index='StudentID', columns='SemesterID', values='GPA').reset_index()
    semester_map = semesters_df.set_index('SemesterID')[['Semester', 'SchoolYear']].to_dict('index')
    new_columns = {sem_id: f"{sem_info['Semester']} {sem_info['SchoolYear']}" for sem_id, sem_info in semester_map.items()}
    gpa_pivot = gpa_pivot.rename(columns=new_columns)

    # order columns
    student_id_col = ['StudentID']
    gpa_cols = sorted([c for c in gpa_pivot.columns if c not in student_id_col])
    gpa_pivot = gpa_pivot[student_id_col + gpa_cols]

    # merge student info
    final_df = pd.merge(students_df[['StudentID', 'Name']], gpa_pivot, on='StudentID', how='inner')

    # calculate trend
    def calculate_trend(row):
        gpas = row[gpa_cols].dropna().values
        if len(gpas) < 2:
            return "N/A"
        avg_gpa = sum(gpas) / len(gpas)
        if all(gpa > 3.5 for gpa in gpas):
            return "Stable High"
        if all(gpa < 2.5 for gpa in gpas):
            return "Consistently Low"
        if gpas[-1] > gpas[0] and gpas[-1] > avg_gpa:
            return "Improving"
        if gpas[-1] < gpas[0] and gpas[-1] < avg_gpa:
            return "Need Attention"
        return "Stable"

    final_df['Overall Trend'] = final_df.apply(calculate_trend, axis=1)

    return final_df



if __name__ == "__main__":
    pass