

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from streamlit_echarts import st_echarts, JsCode
import pandas as pd
# import report_helper as r
# import helpers.report_helper as r
import helpers.report_helper as rh
# from helpers.report_helper import db
# from helpers.report_helper import get_Schoolyear_options, get_course_options

def report_page(db):
    r = rh.report_helper({"db": db})

    # ------------------------------
    # Streamlit App
    # ------------------------------
    st.set_page_config(page_title=" Analytics Reports", layout="wide")
    st.title("📊 Analytics & Visualization")

    report = st.selectbox(
        "Select a Report",
        [
            "-- Select Report --",
            "Year Level Distribution",
            "Student Count per Course",
            "Performance by Year Level"
        ]
    )


    # ------------------------------
    # Report Logic
    # ------------------------------
    if report == "-- Select Report --":
        st.markdown("""
            ## E. Student Demographics

            The **Reporting Module** provides insights into student distribution and academic performance 
            based on year level and course.

            ---

            ## 📑 Reports Available

            ### 1. 🏫 Year Level Distribution
            - **Purpose:** Show how students are distributed across different year levels.  
            - **Metrics:** Year level, number of students.  
            - **Use Case:** Identify enrollment patterns and spot imbalances between year levels.  

            ### 2. 📚 Student Count per Course
            - **Purpose:** Count the total number of students in each course.  
            - **Metrics:** Course name, student count.  
            - **Use Case:** Compare course popularity and track trends in enrollment.  

            ### 3. 📈 Performance by Year Level
            - **Purpose:** Analyze academic performance trends per year level.  
            - **Metrics:** Average grade, highest/lowest grade per year.  
            - **Use Case:** Identify year levels performing above or below expectations, guide interventions.  

            ---

            ## ⚙️ Features
            - **Filters:** Course, semester, school year, teacher, student.  
            - **Visualization:** Interactive charts, graphs, tables.  
            - **Export Options:** CSV, Excel, PDF.  
            - **Insights:** Identify trends, highlight strengths, and address areas needing support.  
        """)


    elif report == "Year Level Distribution":
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            df = r.get_year_level_distribution()  # DataFrame with columns: YearLevel, Count

        st.subheader("🎓 Year Level Distribution")
        st.markdown("""
        This report shows the number of students per year level.
        The chart is color-coded based on the student count, with the minimum and maximum values highlighted.
        """)

        year_levels = df["YearLevel"].tolist()
        counts = df["Count"].tolist()
        min_count = min(counts) - 100
        max_count = max(counts) + 100

        option = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "xAxis": {"type": "category", "data": year_levels, "name": "Year Level"},
            "yAxis": {
                "type": "value",
                "name": "Number of Students",
                "min": min_count,   # Set min based on actual data
                "max": max_count    # Set max based on actual data
            },
            "visualMap": {
                "min": min_count,
                "max": max_count,
                "orient": "vertical",
                "left": "right",
                "top": "middle",
                "text": ["High", "Low"],
                "calculable": True,
                "inRange": {"color": ["RED", "Yellow", "GREEN"]}  # Low = blue, High = red
            },
            "series": [
                {
                    "name": "Students",
                    "type": "bar",
                    "data": counts,
                    "label": {"show": True, "position": "top"}
                }
            ]
        }

        st_echarts(options=option, height="400px")  # ✅ correct

        st.markdown("### Table View")
        st.table(df)

    elif report == "Student Count per Course":
        # Fetch data
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            df = r.get_student_count_per_course()  # DataFrame with columns: Course, Count

        st.subheader("📚 Student Count per Course")
        st.markdown("""
        This report shows the number of students enrolled in each course.
        The bar chart is color-coded based on the number of students, 
        with the minimum and maximum values highlighted for easy comparison.
        """)

        # Prepare chart data
        courses = df["Course"].tolist()
        counts = df["Count"].tolist()
        min_count = min(counts) - 1000
        max_count = max(counts) + 1000

        # ECharts option
        option = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "xAxis": {"type": "category", "data": courses, "name": "Course"},
            "yAxis": {
                "type": "value",
                "name": "Number of Students",
                "min": min_count,  # Set min based on actual data
                "max": max_count   # Set max based on actual data
            },
            "visualMap": {
                "min": min_count,
                "max": max_count,
                "orient": "vertical",
                "left": "right",
                "top": "middle",
                "text": ["High", "Low"],
                "calculable": True,
                "inRange": {"color": ["RED", "Yellow", "GREEN"]}  # Low = blue, High = red
            },
            "series": [
                {
                    "name": "Students",
                    "type": "bar",
                    "data": counts,
                    "label": {"show": True, "position": "top"}
                }
            ]
        }

        # Display chart
        st_echarts(options=option, height="400px")

        # Display table
        st.markdown("### Table View")
        st.table(df)

    elif report == "Performance by Year Level":

        # Fetch data
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            df = r.get_performance_by_year_level()  # DataFrame with columns: YearLevel, Average

        # Prepare chart data
        year_levels = df["YearLevel"].tolist()
        averages = df["Average"].tolist()
        min_avg = min(averages) - 0.2
        max_avg = max(averages)

        st.subheader("📈 Performance by Year Level")
        st.markdown("""
        The **Performance by Year Level** report provides insights into how students in each year level are performing academically. 
        This helps in identifying which year levels are excelling and which may require additional academic support.
        """)

        # Detailed Markdown for Chart
        st.markdown(f"""
        ### Chart Explanation
        - The **bar chart** visualizes the average grades for each year level.
        - **Color Coding:** Bars are color-coded according to the average grade:
            - **Blue** = Lowest average
            - **Green/Yellow** = Mid-range averages
            - **Red** = Highest average
        - **Y-Axis:** Scales dynamically from {min_avg:.2f} to {max_avg:.2f} to reflect true performance differences.
        - **Labels:** The exact average grade is displayed at the top of each bar for quick reference.
        - This visualization allows educators to quickly identify year levels performing above or below the overall average.
        """)

        # ECharts option
        option = {
            "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
            "xAxis": {"type": "category", "data": year_levels, "name": "Year Level"},
            "yAxis": {"type": "value", "name": "Average Grade", "min": min_avg, "max": max_avg},
            "visualMap": {
                "min": min_avg,
                "max": max_avg,
                "orient": "vertical",
                "left": "right",
                "top": "middle",
                "text": ["High", "Low"],
                "calculable": True,
                "inRange": {"color": ["blue", "yellow", "red"]}  # proper colors
            },
            "series": [
                {
                    "name": "Average Grade",
                    "type": "bar",
                    "data": averages,
                    "label": {"show": True, "position": "top"}
                }
            ]
        }

        # Display chart
        st_echarts(options=option, height="400px")

        # Detailed Markdown for Table
        st.markdown("""
        ### Table Explanation
        The table below provides the **exact average grades per year level**:

        - **YearLevel:** Represents the academic year of the students (e.g., 1st Year, 2nd Year, etc.).
        - **Average:** Shows the computed average grade for all students within that year level.
        - This table complements the chart by giving precise numeric values for reporting, analysis, and decision-making.
        - Use this table to cross-check chart data or generate summaries for administrative purposes.
        """)

        st.table(df)
