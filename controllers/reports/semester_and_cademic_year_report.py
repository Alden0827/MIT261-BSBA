

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
	        # D. Semester and Academic Year Analysis
	        "Semester with Lowest GPA",
	        "Best Performing Semester",
	        "Grade Deviation Across Semesters",

	    ]
	)


	# ------------------------------
	# Report Logic
	# ------------------------------
	if report == "-- Select Report --":
	    st.markdown("""
	        ## D. Semester and Academic Year Analysis

	        The **Reporting Module** provides insights into how students perform 
	        across different semesters, highlighting the best and worst academic periods 
	        and analyzing grade stability.

	        ---

	        ## 📑 Reports Available

	        ### 1. ⬇️ Semester with Lowest GPA
	        - **Purpose:** Identify the semester with the lowest overall GPA.  
	        - **Metrics:** Semester, average GPA, total failing students.  
	        - **Use Case:** Detect when student performance dipped and investigate possible causes.  

	        ### 2. 🏆 Best Performing Semester
	        - **Purpose:** Highlight the semester with the strongest performance.  
	        - **Metrics:** Semester, average GPA, top-performing subjects and students.  
	        - **Use Case:** Recognize academic strengths and replicate effective strategies.  

	        ### 3. 📈 Grade Deviation Across Semesters
	        - **Purpose:** Measure variation in student grades across terms.  
	        - **Metrics:** Average GPA (Mean), grade variance (StdDev), student count.  
	        - **Use Case:** Identify stable vs. volatile subjects, supporting curriculum and teaching improvements.  

	        ---

	        ## ⚙️ Features
	        - **Filters:** Course, semester, school year, teacher, student.  
	        - **Visualization:** Interactive charts, graphs, and tables.  
	        - **Export Options:** CSV, Excel, PDF.  
	        - **Drill-Down:** Explore individual subjects or student groups.  
	        - **Insights:** Spot academic trends, highlight best practices, and target areas for support.  
	    """)


	elif report == "Semester with Lowest GPA":
	    with st.spinner('Loading ', report):
	    	header, subjects_df = r.get_lowest_gpa_semester()

	    st.subheader("⬇️ Semester with Lowest GPA")
	    st.markdown(
	        """
	        This table shows the **semester and school year where students recorded 
	        the lowest overall GPA** across all terms.
	        """
	    )
	    st.dataframe(header)   # Semester info

	    st.subheader("📘 GPA per Subject in this Semester")
	    st.markdown(
	        """
	        This table lists the **average GPA of each subject** taken during the 
	        lowest-performing semester, along with the number of enrolled students.
	        """
	    )
	    st.dataframe(subjects_df)  # Subject GPAs

	    # Compute dynamic min/max
	    ymin = subjects_df["GPA"].min()
	    ymax = subjects_df["GPA"].max()
	    margin = 1  # give space

	    # Function to map GPA → color (green → yellow → red)
	    def get_color(val, vmin, vmax):
	        ratio = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
	        if ratio <= 0.5:  # green → yellow
	            return f"rgb({int(255 * (ratio*2))},255,0)"
	        else:  # yellow → red
	            return f"rgb(255,{int(255 * (2 - ratio*2))},0)"

	    gpas = subjects_df["GPA"].tolist()
	    colors = [get_color(v, ymin, ymax) for v in gpas]

	    option = {
	        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
	        "xAxis": {
	            "type": "value",
	            "name": "GPA",
	            "min": float(ymin - margin),
	            "max": float(ymax + margin),
	        },
	        "yAxis": {
	            "type": "category",
	            "data": subjects_df["SubjectCode"].tolist(),
	            "name": "Subject"
	        },
	        "series": [
	            {
	                "name": "GPA",
	                "type": "bar",
	                "data": [
	                    {"value": round(v, 2), "itemStyle": {"color": c}}
	                    for v, c in zip(gpas, colors)
	                ],
	                "label": {
	                    "show": True,
	                    "position": "right",
	                    "formatter": "{c}"
	                },
	            }
	        ]
	    }

	    st.subheader("📊 GPA Distribution per Subject")
	    st.markdown(
	        """
	        The chart below shows the **GPA distribution of subjects** within the 
	        lowest-performing semester.  

	        - **Green bars** → subjects with relatively higher GPA  
	        - **Yellow bars** → mid-range GPA  
	        - **Red bars** → subjects with the lowest GPA  

	        This helps quickly identify which subjects contributed most to the 
	        overall semester decline.
	        """
	    )
	    st_echarts(options=option, height="500px")

	elif report == "Best Performing Semester":
	    header, subjects_df = r.get_best_gpa_semester()

	    st.subheader("🏆 Best Performing Semester")
	    st.markdown(
	        """
	        This table shows the **semester and school year where students recorded 
	        the highest overall GPA** across all terms.
	        """
	    )
	    st.dataframe(header)   # Semester info

	    st.subheader("📘 GPA per Subject in this Semester")
	    st.markdown(
	        """
	        This table lists the **average GPA of each subject** taken during the 
	        best-performing semester, along with the number of enrolled students.
	        """
	    )
	    st.dataframe(subjects_df)  # Subject GPAs

	    # Compute dynamic min/max
	    ymin = subjects_df["GPA"].min()
	    ymax = subjects_df["GPA"].max()
	    margin = 1

	    # Function to map GPA → color (red → yellow → green)
	    def get_color(val, vmin, vmax):
	        ratio = (val - vmin) / (vmax - vmin) if vmax > vmin else 0.5
	        if ratio <= 0.5:  # red → yellow
	            return f"rgb(255,{int(255 * (ratio * 2))},0)"
	        else:  # yellow → green
	            return f"rgb({int(255 * (2 - ratio * 2))},255,0)"

	    gpas = subjects_df["GPA"].tolist()
	    colors = [get_color(v, ymin, ymax) for v in gpas]

	    option = {
	        "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
	        "xAxis": {
	            "type": "value",
	            "name": "GPA",
	            "min": float(ymin - margin),
	            "max": float(ymax + margin),
	        },
	        "yAxis": {
	            "type": "category",
	            # Reverse order so highest GPA is at top
	            "data": subjects_df["SubjectCode"].tolist()[::-1],
	            "name": "Subject"
	        },
	        "series": [
	            {
	                "name": "GPA",
	                "type": "bar",
	                "data": [
	                    {"value": round(v, 2), "itemStyle": {"color": c}}
	                    for v, c in zip(subjects_df["GPA"].tolist()[::-1], colors[::-1])
	                ],
	                "label": {"show": True, "position": "right", "formatter": "{c}"}
	            }
	        ]
	    }


	    st.subheader("📊 GPA Distribution per Subject")
	    st.markdown(
	        """
	        The chart below shows the **GPA distribution of subjects** within the 
	        best-performing semester.  

	        - **Green bars** → subjects with the highest GPA  
	        - **Yellow bars** → mid-range GPA  
	        - **Red bars** → subjects with the lowest GPA  

	        This helps quickly identify which subjects excelled most in the 
	        semester.
	        """
	    )
	    st_echarts(options=option, height="500px")

	elif report == "Grade Deviation Across Semesters":
	    df = r.get_grade_deviation_across_semesters()

	    st.subheader("📊 Grade Variance Across Semesters")
	    st.markdown(
	        """
	        This table lists each **subject**, its **average grade (Mean)**, 
	        the **grade variance (StdDev)** across semesters, 
	        and the **number of enrolled students (Count)**.
	        """
	    )
	    st.dataframe(df)

	    st.subheader("📈 Scatter Plot: GPA Stability vs Difficulty")
	    st.markdown(
	        """
	        - **X-axis:** Average GPA (difficulty)  
	        - **Y-axis:** StdDev (variance)  
	        - **Bubble size:** Number of students (larger = more students)  
	        - **Color:** red = high GPA, green = low GPA
	        """
	    )

	    # Dynamic color mapping
	    gmin, gmax = df["Mean"].min(), df["Mean"].max()

	    def get_color(gpa):
	        ratio = (gpa - gmin) / (gmax - gmin) if gmax > gmin else 0.5
	        if ratio <= 0.5:
	            return f"rgb({int(255 * (ratio * 2))},255,0)"
	        else:
	            return f"rgb(255,{int(255 * (2 - ratio*2))},0)"

	    # Precompute data for ECharts
	    scatter_data = []
	    for _, row in df.iterrows():
	        scatter_data.append({
	            "value": [round(row["Mean"], 2), round(row["StdDev"], 2), max(20, row["Count"] ** 0.5)],
	            "name": row["Subject"],
	            "itemStyle": {"color": get_color(row["Mean"])}
	        })

	    xmin, xmax = df["Mean"].min(), df["Mean"].max()
	    ymin, ymax = df["StdDev"].min(), df["StdDev"].max()
	    margin = 1

	    option = {
	        "tooltip": {
	            "trigger": "item",
	            "formatter": "{b}<br/>Avg GPA: {c[0]}<br/>StdDev: {c[1]}<br/>Bubble size: {c[2]}"
	        },
	        "xAxis": {
	            "name": "Average GPA",
	            "min": float(xmin - margin),
	            "max": float(xmax + margin)
	        },
	        "yAxis": {
	            "name": "Grade Variance (StdDev)",
	            "min": float(ymin - margin),
	            "max": float(ymax + margin)
	        },
	        "series": [{
	            "type": "scatter",
	            "data": scatter_data,
	            "emphasis": {"label": {"show": True, "formatter": "{b}", "position": "top"}}
	        }]
	    }

	    st_echarts(options=option, height="500px")

