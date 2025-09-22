import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
# from helpers.data_helper import data_helper

def get_year_levels(db):
    return db.students.distinct("YearLevel")

def get_courses(db):
    # Get distinct course values
    data = db.students.distinct("Course")

    # Print debug info
    print("Database Name:", db.name)
    print("Connection String:", db.client.address)  # tuple (host, port)
    print("Courses:", data)

    return data

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

def get_teachers(db, teacher=None):
    """
    Returns a list of teacher names from the subjects collection.
    
    :param teacher: Optional string to filter by a specific teacher
    :return: List of teacher names
    """
    query = {}
    if teacher:
        query['Teacher'] = teacher
    
    # Use distinct to get unique teacher names
    teacher_names = db.subjects.distinct("Teacher", filter=query)
    return teacher_names

def student_progress_tracker_page(db):
    """
    Displays the Student Progress Tracker report page.
    """
    st.markdown("### 📈 Student Progress Tracker")
    st.markdown("Shows longitudinal performance for individual students.")

    # --- Determine teacher list based on user role ---
    user_role = st.session_state.get("user_role", "")
    if user_role == "registrar":
        teacher_list = get_teachers(db)
    elif user_role == "teacher":
        teacher_list = [st.session_state.get("fullname", "")]
    else:
        teacher_list = []

    if not teacher_list:
        st.warning("Faculty name is required.")
        return

    # --- Teacher selectbox ---
    teacher_name = st.selectbox("Select Teacher", teacher_list)

    # --- Load data ---
    with st.spinner("Loading teacher's handled Subjects...", show_time=True):
        year_levels = get_year_levels(db)
        courses = get_courses(db)
        subjects_df = get_subjects_by_teacher(db, teacher_name)

    if not courses or not year_levels or subjects_df.empty:
        st.warning("⚠️ Missing data in one or more collections.")
        return

    # --- Prepare subject list ---
    if "Subject Code" in subjects_df.columns:
        subject_list = [""] + subjects_df["Subject Code"].tolist()
    elif "Code" in subjects_df.columns:  # fallback
        subject_list = [""] + subjects_df["Code"].tolist()
    else:
        subject_list = []
        st.warning("⚠️ No subject code column found in subjects_df.")

    # --- Filters ---
    with st.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)
        with col3:
            selected_subject = st.selectbox("Filter by Subject", subject_list)

    # --- Generate report ---
    if st.button("Generate Report"):
        with st.spinner("Fetching student progress data...", show_time=True):
            progress_data = get_student_progress_data(
                db, selected_course, selected_year_level, selected_subject
            )

        if progress_data.empty:
            st.warning("No data found for the selected filters.")
            return

        # --- Display DataFrame ---
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

        # --- Visualizations ---
        progress_data = progress_data.drop(columns=['StudentID']).fillna(0)
        gpa_cols = progress_data.select_dtypes(include='number').columns.tolist()
        avg_per_semester = progress_data[gpa_cols].mean().tolist()

        st.markdown("#### Average GPA Trend per Semester")
        line_options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": gpa_cols, "name": "Semester"},
            "yAxis": {"type": "value", "name": "Average GPA"},
            "series": [{
                "name": "Average GPA",
                "type": "line",
                "data": avg_per_semester,
                "smooth": True,
            }],
        }
        st_echarts(options=line_options, height="400px")

        # Scatter chart
        st.markdown("#### GPA Progress - Scatter Chart")
        progress_data["GeneralAverage"] = progress_data[gpa_cols].mean(axis=1)
        all_values = progress_data[gpa_cols + ["GeneralAverage"]].values.flatten()
        min_val, max_val = 50, float(pd.Series(all_values).max())
        scatter_options = {
            "tooltip": {"trigger": "item", "formatter": "{b}: {c}"},
            "legend": {"data": gpa_cols},
            "xAxis": {"type": "value", "name": "General Average GPA", "min": min_val, "max": max_val},
            "yAxis": {"type": "value", "name": "Semester GPA", "min": min_val, "max": max_val},
            "series": []
        }
        for col in gpa_cols:
            scatter_options["series"].append({
                "name": col,
                "type": "scatter",
                "data": [
                    {"value": [row["GeneralAverage"], row[col]], "name": row["Name"]}
                    for _, row in progress_data.iterrows() if pd.notnull(row[col])
                ],
                "symbolSize": 12,
            })
        st_echarts(options=scatter_options, height="500px")


def get_student_progress_data(db, course, year_level, subject_code):
    """
    Fetches and processes data to generate the student progress report.
    """
    import pandas as pd

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

    # order columns by SchoolYear and Semester
    semester_rank = {'Spring': 1, 'Summer': 2, 'Fall': 3}  # adjust if you have other semesters
    semester_order = semesters_df.copy()
    semester_order['semester_num'] = semester_order['Semester'].map(semester_rank)
    semester_order = semester_order.sort_values(['SchoolYear', 'semester_num'])
    gpa_cols_ordered = [new_columns[sem_id] for sem_id in semester_order['SemesterID'] if new_columns[sem_id] in gpa_pivot.columns]

    # keep only semester columns where average GPA > 0
    non_zero_semesters = [c for c in gpa_cols_ordered if gpa_pivot[c].dropna().mean() > 0]

    # final pivot columns
    gpa_pivot = gpa_pivot[['StudentID'] + non_zero_semesters]

    # merge student info
    final_df = pd.merge(students_df[['StudentID', 'Name']], gpa_pivot, on='StudentID', how='inner')

    # redefine gpa_cols for trend calculation
    gpa_cols = non_zero_semesters

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