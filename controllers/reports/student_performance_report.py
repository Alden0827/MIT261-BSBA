import streamlit as st
import matplotlib.pyplot as plt
from streamlit_echarts import st_echarts, JsCode
import pandas as pd
import helpers.report_helper as r

def display_top_performers(st, db):
    st.subheader("🏆 Top 10 Performers")

    col_a, col_b = st.columns([2, 2])
    with col_a:
        sem_selected = st.selectbox("Semester", r.get_semester_options())
    with col_b:
        sy_selected = st.selectbox("School Year", r.get_Schoolyear_options())

    all_data = r.get_top_performers(school_year=sy_selected, semester=sem_selected)

    if not all_data.empty:
        df_top = all_data.sort_values("Average", ascending=False).head(10)
        st.dataframe(df_top)

        col1, col2 = st.columns(2)
        with col1:
            fig, ax = plt.subplots()
            ax.barh(df_top["Student"], df_top["Average"])
            ax.set_xlabel("Average Grade")
            ax.set_ylabel("Student")
            ax.set_title("Top 10 Performers")
            plt.gca().invert_yaxis()
            st.pyplot(fig)

        with col2:
            course_avg = df_top.groupby("Course")["Average"].mean()
            fig2, ax2 = plt.subplots()
            ax2.pie(course_avg, labels=course_avg.index, autopct="%1.1f%%", startangle=90)
            ax2.set_title("Top Performers by Course")
            st.pyplot(fig2)
    else:
        st.info("No records found for the selected Semester and School Year.")

def display_failing_students(st, db):
    st.subheader("📉 Students with High Failure Rate")

    all_data = r.get_failing_students()
    if not all_data.empty:
        col1, col2 = st.columns([2, 2])
        with col1:
            sem_selected = st.selectbox("Semester", sorted(all_data["Semester"].dropna().unique()))
        with col2:
            sy_selected = st.selectbox("School Year", sorted(all_data["SchoolYear"].dropna().unique()))

        df_fails = r.get_failing_students(school_year=sy_selected, semester=sem_selected)

        if not df_fails.empty:
            st.dataframe(df_fails)

            student_failures = df_fails.groupby(["Student", "Course"])["Failures"].sum().reset_index()
            students = student_failures["Student"].unique().tolist()
            courses = student_failures["Course"].unique().tolist()
            heatmap_data = [[courses.index(row["Course"]), students.index(row["Student"]), int(row["Failures"])] for _, row in student_failures.iterrows()]

            options1 = {
                "title": {"text": "Failures per Student by Course"},
                "tooltip": {"position": "top"},
                "grid": {"height": "70%", "top": "10%"},
                "xAxis": {"type": "category", "data": courses, "splitArea": {"show": True}},
                "yAxis": {"type": "category", "data": students, "splitArea": {"show": True}},
                "visualMap": {
                    "min": 0, "max": 10, "calculable": True, "orient": "horizontal", "left": "center", "bottom": "5%"
                },
                "series": [{"name": "Failures", "type": "heatmap", "data": heatmap_data, "label": {"show": True}, "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0, 0, 0, 0.5)"}}}]
            }
            st_echarts(options=options1, height="500px")
        else:
            st.info("No failing students found for the selected Semester and School Year.")
    else:
        st.info("No student records found.")

def display_students_with_grade_improvement(st, db):
    st.subheader("📈 Students with Grade Improvement")

    all_data = r.get_students_with_improvement()
    col1, col2 = st.columns([2, 2])
    with col1:
        sem_selected = st.selectbox("Semester", ["All"] + sorted(pd.Series(all_data["Semester"]).dropna().unique()))
    with col2:
        sy_selected = st.selectbox("School Year", ["All"] + sorted(pd.Series(all_data["SchoolYear"]).dropna().unique()))

    df = r.get_students_with_improvement(selected_semester=sem_selected, selected_sy=sy_selected)

    if not df.empty:
        st.dataframe(df)

        df_top15 = df.head(15).copy()
        students_labels = df_top15["Student"].tolist()
        improvements = pd.to_numeric(df_top15["Improvement"], errors="coerce").fillna(0).tolist()

        option = {
            "title": {"text": f"Top 15 Students with Grade Improvement (Semester: {sem_selected}, SchoolYear: {sy_selected})"},
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "xAxis": {"type": "value", "name": "Improvement (%)"},
            "yAxis": {"type": "category", "data": students_labels, "name": "Student", "inverse": True},
            "series": [{"data": [round(v, 2) for v in improvements], "type": "bar"}]
        }
        st_echarts(option, height="500px")
    else:
        st.info("No student records found for the selected School Year / Semester.")

def display_distribution_of_grades(st, db):
    st.subheader("📊 Grade Distribution")

    all_data = r.get_distribution_of_grades()
    col1, col2 = st.columns([2, 2])
    with col1:
        sem_selected = st.selectbox("Semester", ["All"] + sorted(all_data["Semester"].dropna().unique()))
    with col2:
        sy_selected = st.selectbox("School Year", ["All"] + sorted(all_data["SchoolYear"].dropna().unique()))

    df_filtered = r.get_distribution_of_grades(selected_semester=sem_selected, selected_sy=sy_selected)

    if not df_filtered.empty:
        bins = [60, 65, 70, 75, 80, 85, 90, 95, 100]
        bin_labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-1)]
        counts = [0] * (len(bins) - 1)

        for g in df_filtered["Grade"]:
            for i in range(len(bins) - 1):
                if bins[i] <= g < bins[i+1]:
                    counts[i] += 1
                    break

        option = {
            "title": {"text": f"Grade Distribution (Semester: {sem_selected}, SchoolYear: {sy_selected})"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": bin_labels, "name": "Grade Range"},
            "yAxis": {"type": "value", "name": "Frequency"},
            "series": [{"data": counts, "type": "bar"}]
        }
        st_echarts(option, height="400px")
    else:
        st.info("No grades found for the selected Semester/School Year.")

def display_incomplete_grades_report(st, db):
    st.subheader("📝 Incomplete Grades Report")

    col1, col2 = st.columns([2, 2])
    with col1:
        sy_selected = st.selectbox("School Year", ["All"] + r.get_Schoolyear_options())
    with col2:
        sem_selected = st.selectbox("Semester", ["All"] + r.get_semester_options())

    sy_filter = None if sy_selected == "All" else sy_selected
    sem_filter = None if sem_selected == "All" else sem_selected

    df = r.get_incomplete_grades(school_year=sy_filter, semester=sem_filter)

    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No students with incomplete grades found for the selected filters.")

def display_student_academic_standing_report(st, db):
    st.subheader("🎓 Student Academic Standing Report")

    col1, col2 = st.columns([2, 2])
    with col1:
        sy_selected = st.selectbox("School Year", ["All"] + r.get_Schoolyear_options())
    with col2:
        sem_selected = st.selectbox("Semester", ["All"] + r.get_semester_options())

    sy_filter = None if sy_selected == "All" else sy_selected
    sem_filter = None if sem_selected == "All" else sem_selected

    df = r.get_student_academic_standing(school_year=sy_filter, semester=sem_filter)

    if not df.empty:
        st.dataframe(df)
    else:
        st.info("No student academic standing data found for the selected filters.")
