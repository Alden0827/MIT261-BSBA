import streamlit as st
from streamlit_echarts import st_echarts
import pandas as pd
import helpers.report_helper as r

def display_hardest_subject(st, db):
    st.subheader("📉 Hardest Subjects")

    col1, col2 = st.columns([2, 2])
    courses = sorted(r.get_course_options())
    school_years = sorted(r.get_Schoolyear_options())

    with col1:
        course_selected = st.selectbox("Course", ["All"] + courses)
    with col2:
        sy_selected = st.selectbox("School Year", ["All"] + school_years)

    course_filter = None if course_selected == "All" else course_selected
    sy_filter = None if sy_selected == "All" else sy_selected

    df = r.get_hardest_subject(course=course_filter, school_year=sy_filter)

    if not df.empty:
        st.dataframe(df)

        df_top = df.head(10)
        option = {
            "title": {"text": "Top 10 Hardest Subjects by Failure Rate"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df_top["Subject"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": df_top["Failure Rate"].tolist(), "type": "bar"}]
        }
        st_echarts(options=option, height="500px")
    else:
        st.info("No data available.")

def display_easiest_subjects(st, db):
    st.subheader("📈 Easiest Subjects")

    col1, col2 = st.columns([2, 2])
    courses = sorted(r.get_course_options())
    school_years = sorted(r.get_Schoolyear_options())

    with col1:
        course_selected = st.selectbox("Course", ["All"] + courses)
    with col2:
        sy_selected = st.selectbox("School Year", ["All"] + school_years)

    course_filter = None if course_selected == "All" else course_selected
    sy_filter = None if sy_selected == "All" else sy_selected

    df = r.get_easiest_subjects(course=course_filter, school_year=sy_filter)

    if not df.empty:
        st.dataframe(df)

        df_top = df.head(10)
        option = {
            "title": {"text": "Top 10 Easiest Subjects by High Grade Rate"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df_top["Subject"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": df_top["High Rate"].tolist(), "type": "bar"}]
        }
        st_echarts(options=option, height="500px")
    else:
        st.info("No data available.")

def display_average_grades_per_teacher(st, db):
    st.subheader("👩‍🏫 Average Grades per Teacher")

    school_years = ["All"] + r.get_Schoolyear_options()
    semesters = ["All"] + r.get_semester_options()

    selected_year = st.selectbox("Select School Year", school_years)
    selected_semester = st.selectbox("Select Semester", semesters)

    year_filter = None if selected_year == "All" else selected_year
    semester_filter = None if selected_semester == "All" else selected_semester

    df = r.get_avg_grades_per_teacher(school_year=year_filter, semester=semester_filter)

    if not df.empty:
        st.dataframe(df)

        option = {
            "title": {"text": "Average Grades per Teacher"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df["Teacher"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": df["Average Grade"].tolist(), "type": "bar"}]
        }
        st_echarts(options=option, height="500px")
    else:
        st.info("No data available for the selected filters.")

def display_teachers_with_high_failures(st, db):
    st.subheader("❌ Teachers with Most Failures")

    school_years = ["All"] + r.get_Schoolyear_options()
    semesters = ["All"] + r.get_semester_options()

    selected_year = st.selectbox("Select School Year", school_years)
    selected_semester = st.selectbox("Select Semester", semesters)

    year_filter = None if selected_year == "All" else selected_year
    semester_filter = None if selected_semester == "All" else selected_semester

    df = r.get_teachers_with_high_failures(school_year=year_filter, semester=semester_filter)

    if not df.empty:
        st.dataframe(df)

        option = {
            "title": {"text": "Failure Rate per Teacher"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df["Teacher"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": df["Failure Rate"].tolist(), "type": "bar"}]
        }
        st_echarts(options=option, height="500px")
    else:
        st.info("No records found for the selected filters.")
