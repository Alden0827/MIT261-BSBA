

# import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from streamlit_echarts import st_echarts, JsCode
import pandas as pd
# import report_helper as r
import helpers.report_helper as r
# from helpers.report_helper import db
from helpers.report_helper import get_Schoolyear_options, get_course_options

def report_page(st, db):
	# ------------------------------
	# Streamlit App
	# ------------------------------
	st.set_page_config(page_title=" Analytics Reports", layout="wide")
	st.title("📊 Analytics & Visualization")

	report = st.selectbox(
	    "Select a Report",
	    [
	        "-- Select Report --",
	        # C. Course and Curriculum Insights
	        "Grade Trend per Course",
	        "Subject Load Intensity",
	        "GE vs Major Subjects Performance",

	    ]
	)


	# ------------------------------
	# Report Logic
	# ------------------------------
	if report == "-- Select Report --":
	    st.markdown("""
	        # Reporting Module Overview

	        The **Reporting Module** provides comprehensive insights into student academic performance, teacher efficiency, course trends, and subject difficulty.

	        ---

	        ## Reports Available


	        ### 1. Grade Trend per Course
	        - **Purpose:** Track performance trends per course.
	        - **Metrics:** Course, semester/year, average grade trend.

	        ### 2. Subject Load Intensity
	        - **Purpose:** Analyze subjects taken per student.
	        - **Metrics:** Student ID, total subjects per semester.

	        ### 3. GE vs Major Subjects Performance
	        - **Purpose:** Compare student performance in GE vs Major subjects.
	        - **Metrics:** Student ID, GE average, Major average, difference.

	        ---

	        ## Features
	        - **Filters:** Course, semester, school year, teacher, student.
	        - **Visualization:** Charts, graphs, tables.
	        - **Export Options:** CSV, Excel, PDF.
	        - **Interactivity:** Drill-down to individual student or subject performance.
	        - **Insights:** Identify trends, improvements, and areas requiring attention.
	        """)


	elif report == "Grade Trend per Course":
	    df = r.get_grade_trend_per_course()
	    st.subheader("📊 Grade Trends per Course (Heatmap)")

	    if not df.empty:
	        # Prepare axes
	        courses = df['Course'].unique().tolist()
	        years = sorted(df['SchoolYear'].unique().tolist())

	        # Create heatmap data: [x_index, y_index, value]
	        heatmap_data = [
	            [years.index(row['SchoolYear']), courses.index(row['Course']), round(row['Average'], 2)]
	            for _, row in df.iterrows()
	        ]

	        # Determine min and max for visualMap
	        val_min = df['Average'].min()
	        val_max = df['Average'].max()

	        options = {
	            "title": {"text": "Grade Trends per Course", "left": "center"},
	            "tooltip": {
	                "position": "top",
	                "formatter": """
	                    function (params) {
	                        let year = params.series.xAxis.data[params.data[0]];
	                        let course = params.series.yAxis.data[params.data[1]];
	                        let value = params.data[2];
	                        return '<b>Course:</b> ' + course + '<br>' +
	                               '<b>Year:</b> ' + year + '<br>' +
	                               '<b>Average Grade:</b> ' + value;
	                    }
	                """
	            },
	            "grid": {"height": "70%", "top": "10%"},
	            "xAxis": {"type": "category", "data": years, "name": "School Year"},
	            "yAxis": {"type": "category", "data": courses, "name": "Course"},
	            "visualMap": {
	                "min": val_min,
	                "max": val_max,
	                "calculable": True,
	                "orient": "horizontal",
	                "left": "center",
	                "bottom": 10,
	                "inRange": {"color": ["#d73027", "#fee090", "#1a9850"]}  # red → yellow → green
	            },
	            "series": [{
	                "name": "Average Grade",
	                "type": "heatmap",
	                "data": heatmap_data,
	                "label": {"show": True},
	                "emphasis": {"itemStyle": {"shadowBlur": 10, "shadowColor": "rgba(0,0,0,0.5)"}}
	            }]
	        }
	        '''
	        This heatmap visualizes the trend of average grades per course across different school years. 
	        Each row represents a course, and each column represents a school year. 
	        The color intensity indicates the average grade, with red showing lower averages, yellow for moderate performance, 
	        and green for higher averages. This allows educators and administrators to quickly identify courses where 
	        students are consistently performing well or struggling over time, helping guide curriculum adjustments and 
	        targeted interventions.
	        '''
	        st_echarts(options=options, height="600px")
	    else:
	        st.info("No grade data found for the selected filters.")


	elif report == "Subject Load Intensity":
	    # --- Fetch data ---
	    df = r.get_subject_load_intensity()  # Expected columns: ["Course", "Load"]
	    
	    st.subheader("📊 Subject Load Intensity per Course")
	    '''
	    The table displays the average subject load per course, showing how intensive the curriculum is for students in each program. 
	    Higher load values indicate more intensive coursework.
	    '''
	    st.dataframe(df)

	    if not df.empty:
	        # Prepare chart data
	        courses = df["Course"].tolist()
	        loads = df["Load"].round(2).tolist()

	        # Define color based on load intensity
	        def get_color(value):
	            if value >= 5:
	                return "#d9534f"  # Red → Very heavy load
	            elif value >= 4:
	                return "#f0ad4e"  # Orange → Moderate load
	            else:
	                return "#5cb85c"  # Green → Light load

	        colors = [get_color(v) for v in loads]

	        # --- ECharts options ---
	        options = {
	            "title": {"text": "Average Subject Load per Course", "left": "center"},
	            "tooltip": {"trigger": "axis", "formatter": "{b}: {c}"},
	            "xAxis": {"type": "category", "data": courses, "name": "Course", "axisLabel": {"rotate": 30}},
	            "yAxis": {"type": "value", "name": "Load"},
	            "series": [{
	                "data": [{"value": v, "itemStyle": {"color": c}} for v, c in zip(loads, colors)],
	                "type": "bar",
	                "label": {"show": True, "position": "top"}
	            }]
	        }

	        '''
	        The column chart visualizes the subject load intensity for each course. Bars are color-coded:
	        green represents lighter course loads, orange indicates moderate intensity, and red highlights heavier workloads.
	        This chart allows administrators and educators to quickly identify which courses have heavier academic demands.
	        '''
	        st_echarts(options=options, height="500px")
	    else:
	        st.info("No course load data found.")


	elif report == "GE vs Major Subjects Performance":
	    df = r.get_ge_vs_major()

	    st.subheader("📊 General Education vs Major Subjects Performance Over Time")
	    st.markdown(
	        """
	        This chart compares the **average performance of students** in 
	        **General Education (GE)** subjects and **Major** subjects 
	        across different school years.  
	        
	        It helps identify performance trends and differences between subject types.
	        """
	    )
	    st.dataframe(df)

	    years = sorted(df["SchoolYear"].unique().tolist())
	    ge_vals = df[df["Type"] == "GE"].sort_values("SchoolYear")["Average"].tolist()
	    major_vals = df[df["Type"] == "Major"].sort_values("SchoolYear")["Average"].tolist()

	    # Compute dynamic min/max with margins
	    ymin = df["Average"].min()
	    ymax = df["Average"].max()
	    margin = 1  # adjust margin as needed

	    option = {
	        "tooltip": {"trigger": "axis"},
	        "legend": {"data": ["GE", "Major"]},
	        "xAxis": {
	            "type": "category",
	            "data": years,
	            "name": "School Year"
	        },
	        "yAxis": {
	            "type": "value",
	            "name": "Average Grade",
	            "min": float(ymin - margin),
	            "max": float(ymax + margin),
	        },
	        "series": [
	            {
	                "name": "GE",
	                "type": "bar",
	                "data": ge_vals,
	                "barGap": 0,
	                "label": {
	                    "show": True,
	                    "position": "top",
	                    "formatter": "{c:.2f}"  # ✅ Correct property
	                }
	            },
	            {
	                "name": "Major",
	                "type": "bar",
	                "data": major_vals,
	                "label": {
	                    "show": True,
	                    "position": "top",
	                    "formatter": "{c:.2f}"  # ✅ Correct property
	                }
	            },
	        ],
	    }

	    st_echarts(options=option, height="500px")
