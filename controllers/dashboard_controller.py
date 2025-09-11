import pandas as pd
import streamlit as st
from streamlit_echarts import st_echarts #pip install streamlit-echarts
import os, pickle, time
from helpers.data_helper import get_students, get_grades, get_semesters, get_subjects

CACHE_FILE = "./cache/dashboard_cache.pkl"
CACHE_TTL = 3600  # 1 hour in seconds

def dasboard_view(st):

    print('Loading grades...')
    grades = get_grades()
    print('Loading students...')
    students = get_students()
    print('Loading semesters...')
    semesters = get_semesters()
    print('Loading subjects...')
    subjects = get_subjects()

    st.title("🎓 University Dashboard")

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", len(students))
    col2.metric("Faculty", subjects["Teacher"].nunique())
    col3.metric("Courses", subjects["Description"].nunique())
    col4.metric("Enrollments", len(grades))

    st.markdown("---")

    # ---------------- Charts Row 1 ----------------
    row1_col1, row1_col2 = st.columns(2)

    # Students per Course
    with row1_col1:
        st.subheader("📊 Students per Course")
        students_per_course = students.groupby("Course")["_id"].count().reset_index()
        students_per_course.rename(columns={"_id": "Count"}, inplace=True)

        option1 = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": students_per_course["Course"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{
                "data": students_per_course["Count"].tolist(),
                "type": "bar",
                "itemStyle": {"color": "#5DADE2"},
                "label": {"show": True, "position": "top"}
            }]
        }
        st_echarts(options=option1, height="400px")

    # Grade Distribution
    with row1_col2:
        st.subheader("📊 Grade Distribution")
        all_grades_list = [g for row in grades["Grades"] for g in row]

        option2 = {
            "tooltip": {},
            "xAxis": {"type": "category", "data": list(range(50, 101, 5))},
            "yAxis": {"type": "value"},
            "series": [{
                "type": "histogram",
                "data": all_grades_list,
                "itemStyle": {"color": "#E74C3C"}
            }]
        }
        # ECharts has no direct "histogram", we simulate with bar count
        import numpy as np
        hist, bins = np.histogram(all_grades_list, bins=10)
        option2["xAxis"]["data"] = [f"{int(bins[i])}-{int(bins[i+1])}" for i in range(len(bins)-1)]
        option2["series"] = [{
            "data": hist.tolist(),
            "type": "bar",
            "itemStyle": {"color": "#E74C3C"},
            "label": {"show": True, "position": "top"}
        }]
        st_echarts(options=option2, height="400px")

    st.markdown("---")

    # ---------------- Charts Row 2 ----------------
    st.subheader("📈 Average GPA per Semester")

    all_grades = []
    for idx, row in grades.iterrows():
        for g, sem_id in zip(
            row["Grades"],
            row["SemesterID"] if isinstance(row["SemesterID"], list) else [row["SemesterID"]] * len(row["Grades"])
        ):
            all_grades.append({"Grade": g, "SemesterID": sem_id})
    df_grades = pd.DataFrame(all_grades)

    df_grades = df_grades.merge(semesters, left_on="SemesterID", right_on="_id", how="left")
    df_grades["SemesterLabel"] = df_grades["Semester"].astype(str) + " " + df_grades["SchoolYear"].astype(str)

    gpa_per_semester = df_grades.groupby("SemesterLabel")["Grade"].mean().reset_index()

    option3 = {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": gpa_per_semester["SemesterLabel"].tolist()},
        "yAxis": {"type": "value", "min": 50, "max": 100},
        "series": [{
            "data": gpa_per_semester["Grade"].round(2).tolist(),
            "type": "line",
            "smooth": True,
            "symbol": "circle",
            "symbolSize": 10,
            "itemStyle": {"color": "#F39C12"},
            "label": {"show": True, "position": "top"}
        }]
    }
    st_echarts(options=option3, height="400px")
