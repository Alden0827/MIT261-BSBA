import streamlit as st
import pandas as pd
from helpers.data_helper import data_helper
from st_echarts import st_echarts

def student_progress_tracker_page(db):
    """
    Displays the Student Progress Tracker report page.
    """
    st.markdown("### 📈 Student Progress Tracker")
    st.markdown("Shows longitudinal performance for individual students.")

    dh = data_helper(db)

    # --- Filters ---
    st.sidebar.header("Filters")
    courses = [""] + dh.get_courses()
    year_levels = [""] + dh.get_year_levels()
    subjects_df = dh.get_subjects()
    subject_list = [""] + subjects_df['Subject Code'].tolist()

    selected_course = st.sidebar.selectbox("Filter by Course", courses)
    selected_year_level = st.sidebar.selectbox("Filter by Year Level", year_levels)
    selected_subject = st.sidebar.selectbox("Filter by Subject", subject_list)

    # --- Report Data ---
    if st.sidebar.button("Generate Report"):
        progress_data = get_student_progress_data(db, selected_course, selected_year_level, selected_subject)

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

        # Fill NaN with '-' for display
        display_df = progress_data.fillna('-')
        st.dataframe(display_df.style.applymap(style_trend, subset=['Overall Trend']))

        # --- ECharts Visualizations ---
        st.markdown("---")
        st.markdown("### Visualizations")

        # --- Line Chart ---
        st.markdown("#### GPA Trend - Line Chart")

        # Prepare data for ECharts
        gpa_cols = [col for col in progress_data.columns if ' ' in col] # Heuristic for semester columns
        line_options = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": progress_data['Name'].tolist()},
            "xAxis": {"type": "category", "data": gpa_cols},
            "yAxis": {"type": "value", "name": "GPA"},
            "series": [],
        }
        for index, row in progress_data.iterrows():
            line_options["series"].append({
                "name": row['Name'],
                "type": "line",
                "data": row[gpa_cols].tolist(),
            })
        st_echarts(options=line_options, height="500px")

        # --- Scatter Chart ---
        st.markdown("#### GPA Progress - Scatter Chart")
        if len(gpa_cols) >= 2:
            first_sem = gpa_cols[0]
            last_sem = gpa_cols[-1]

            scatter_data = progress_data[[first_sem, last_sem, 'Overall Trend', 'Name']].dropna()

            scatter_options = {
                "xAxis": {"type": "value", "name": f"GPA ({first_sem})"},
                "yAxis": {"type": "value", "name": f"GPA ({last_sem})"},
                "tooltip": {
                    "trigger": 'item',
                    "formatter": '{b}<br/>{a} : ( {c} )'
                },
                "series": [{
                    "name": 'Student Progress',
                    "type": 'scatter',
                    "data": [
                        [row[first_sem], row[last_sem], row['Name']] for _, row in scatter_data.iterrows()
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
    # 1. Fetch all necessary data
    students_df = pd.DataFrame(list(db.students.find()))
    grades_df = pd.DataFrame(list(db.grades.find()))
    subjects_df = pd.DataFrame(list(db.subjects.find()))
    semesters_df = pd.DataFrame(list(db.semesters.find()))

    if grades_df.empty or subjects_df.empty or students_df.empty or semesters_df.empty:
        return pd.DataFrame()

    # Rename columns for consistency
    students_df = students_df.rename(columns={'_id': 'StudentID'})
    subjects_df = subjects_df.rename(columns={'_id': 'SubjectCode'})
    semesters_df = semesters_df.rename(columns={'_id': 'SemesterID'})

    # 2. Filter students based on course and year level
    if course:
        students_df = students_df[students_df['Course'] == course]
    if year_level:
        students_df = students_df[students_df['YearLevel'] == year_level]

    # Explode grades dataframe
    grades_exploded = grades_df.explode(['SubjectCodes', 'Grades', 'Teachers']).rename(columns={'SubjectCodes': 'SubjectCode'})

    # 3. Filter by subject if selected
    if subject_code:
        students_who_took_subject = grades_exploded[grades_exploded['SubjectCode'] == subject_code]['StudentID'].unique()
        students_df = students_df[students_df['StudentID'].isin(students_who_took_subject)]

    # Merge grades with subjects to get units
    grades_with_units = pd.merge(grades_exploded, subjects_df[['SubjectCode', 'Units']], on='SubjectCode')

    # Calculate grade points
    grades_with_units['GradePoints'] = grades_with_units['Grades'] * grades_with_units['Units']

    # Group by student and semester to calculate GPA
    gpa_df = grades_with_units.groupby(['StudentID', 'SemesterID']).apply(
        lambda x: pd.Series({
            'GPA': x['GradePoints'].sum() / x['Units'].sum()
        })
    ).reset_index()

    # Pivot the table to have semesters as columns
    gpa_pivot = gpa_df.pivot(index='StudentID', columns='SemesterID', values='GPA').reset_index()

    # Merge with semester names for readable columns
    semester_map = semesters_df.set_index('SemesterID')[['Semester', 'SchoolYear']].to_dict('index')

    # Create readable column names and sort them
    new_columns = {sem_id: f"{sem_info['Semester']} {sem_info['SchoolYear']}" for sem_id, sem_info in semester_map.items()}
    gpa_pivot = gpa_pivot.rename(columns=new_columns)

    # Sort columns chronologically (basic sorting by name)
    student_id_col = ['StudentID']
    gpa_cols = sorted([col for col in gpa_pivot.columns if col not in student_id_col])
    gpa_pivot = gpa_pivot[student_id_col + gpa_cols]

    # Merge with student info
    final_df = pd.merge(students_df[['StudentID', 'Name']], gpa_pivot, on='StudentID', how='inner')

    # Calculate trend
    def calculate_trend(row):
        gpas = row[gpa_cols].dropna().values
        if len(gpas) < 2:
            return "N/A"

        # Simple trend logic (can be improved with regression)
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
