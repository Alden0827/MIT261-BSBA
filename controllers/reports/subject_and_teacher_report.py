

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from streamlit_echarts import st_echarts, JsCode
import pandas as pd
# import report_helper as r
import helpers.report_helper as rh
# from helpers.report_helper import db
# from helpers.report_helper import get_Schoolyear_options, get_course_options

def report_page(db):
    r = rh.report_helper({"db": db})
    # ------------------------------
    # Streamlit App
    # ------------------------------
    st.set_page_config(page_title=" Analytics Reports", layout="wide")
    st.title("Analytics & Visualization")

    report = st.selectbox(
        "Select a Report",
        [
            "-- Select Report --",
            # B. Subject and Teacher Analytics
            "Hardest Subject",
            "Easiest Subjects",
            "Average Grades per Teacher",
            "Teachers with High Failures",
        ]
    )


    # ------------------------------
    # Report Logic
    # ------------------------------
    if report == "-- Select Report --":
        st.markdown("""
            ## B. Subject and Teacher Analytics

            The **Reporting Module** provides insights into student performance, subject difficulty, 
            and teacher effectiveness. Use the menu above to select a report and apply filters such 
            as course, semester, and school year for more specific analysis.

            ---

            ## 📑 Reports Available

            ### 1. 📉 Hardest Subjects
            - **Purpose:** Identify subjects where students struggle the most.  
            - **Metrics:** Subject name, average grade, failure rate (%).  
            - **Use Case:** Pinpoint subjects that may need curriculum review or additional academic support.  

            ### 2. 📈 Easiest Subjects
            - **Purpose:** Highlight subjects where students excel.  
            - **Metrics:** Subject name, average grade, high-grade rate (%).  
            - **Use Case:** Recognize effective teaching methods and subject strengths.  

            ### 3. 👩‍🏫 Average Grades per Teacher
            - **Purpose:** Evaluate teacher performance based on student outcomes.  
            - **Metrics:** Teacher name, subjects taught, computed average grades.  
            - **Use Case:** Support faculty performance reviews and track teaching effectiveness.  

            ### 4. ❌ Teachers with High Failures
            - **Purpose:** Detect instructors with high student failure rates.  
            - **Metrics:** Teacher name, subjects handled, failure rates (%).  
            - **Use Case:** Identify areas where teaching strategies or additional resources may be required.  

            ---

            ## ⚙️ Features
            - **Filters:** Course, semester, school year, teacher, student.  
            - **Visualization:** Interactive charts, graphs, and summary tables.  
            - **Export Options:** Download results as CSV, Excel, or PDF.  
            - **Drill-Down:** Navigate from overview reports to individual student or subject data.  
            - **Insights:** Spot academic trends, highlight strengths, and address areas needing improvement.  
        """)


    elif report == "Hardest Subject":
        # --- Dropdown filters ---

        col1, col2 = st.columns([2, 2])

        with st.spinner(f"Loading courses and school year...", show_time=True):
            courses = sorted(r.get_course_options())
            school_years = sorted(r.get_Schoolyear_options())

        with col1:
            course_selected = st.selectbox("Course", ["All"] + courses)
        with col2:
            sy_selected = st.selectbox("School Year", ["All"] + school_years)

        # --- Apply filters ---
        course_filter = None if course_selected == "All" else course_selected
        sy_filter = None if sy_selected == "All" else sy_selected

        print("Selected course:", course_selected)
        print("Selected school year:", sy_selected)

        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            df = r.get_hardest_subject(course=course_filter, school_year=sy_filter)

        if not df.empty:

            st.subheader("📉 Hardest Subjects")

            # --- Add ECharts Bar Chart ---
            if not df.empty:

                st.markdown('''
                The table lists subjects with the highest failure rates based on the selected course and school year. 
                It allows educators to identify which subjects consistently challenge students 
                and may require additional support, curriculum review, or targeted interventions.
                ''')
                st.dataframe(df)


                df = df.head(10).copy()

                x_labels = df["Description"].replace("", pd.NA).fillna(df["Subject"]).tolist()
                y_values = df["Failure Rate"].astype(float).round(2).tolist()

                def get_color(value):
                    if value < 20:
                        return "#5cb85c"  # green
                    elif value < 50:
                        return "#f0ad4e"  # orange
                    else:
                        return "#d9534f"  # red

                options = {
                    "title": {"text": "Top 10 Hardest Subjects (Failure Rate)", "left": "center"},
                    "tooltip": {"trigger": "axis"},
                    "xAxis": {
                        "type": "category",
                        "data": x_labels,
                        "axisLabel": {"rotate": 30}
                    },
                    "yAxis": {"type": "value", "name": "Failure Rate (%)"},
                    "series": [
                        {
                            "data": [
                                {"value": v, "itemStyle": {"color": get_color(v)}}
                                for v in y_values
                            ],
                            "type": "bar",
                            "label": {"show": True, "position": "top"}
                        }
                    ]
                }
                st.markdown('''
                The bar chart visualizes the top 10 hardest subjects by failure rate. 
                Bars are color-coded for clarity: green indicates low failure rates, 
                orange represents moderate difficulty, and red highlights the most challenging subjects. 
                The chart allows for quick comparison between subjects, making it easy to pinpoint 
                areas where students struggle the most and prioritize academic support.
                ''')
                st_echarts(options=options, height="500px")




    elif report == "Easiest Subjects":
        # --- Dropdown filters ---


        col1, col2 = st.columns([2, 2])

        with st.spinner(f"Loading courses and school year...", show_time=True):
            courses = sorted(r.get_course_options())
            school_years = sorted(r.get_Schoolyear_options())

        with col1:
            course_selected = st.selectbox("Course", ["All"] + courses)
        with col2:
            sy_selected = st.selectbox("School Year", ["All"] + school_years)

        # --- Apply filters ---
        course_filter = None if course_selected == "All" else course_selected
        sy_filter = None if sy_selected == "All" else sy_selected

        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            df = r.get_easiest_subjects(course=course_filter, school_year=sy_filter)

        if not df.empty:

            st.subheader("📈 Easiest Subjects")
            st.markdown('''
            The table lists subjects where students achieve the highest grades, 
            based on the selected course and school year. This provides a clear 
            view of subjects in which students excel, helping educators recognize 
            areas of strength and effective teaching practices.
            ''')
            st.dataframe(df)

            # --- Add ECharts Bar Chart ---
            if not df.empty:
                df = df.head(10).copy()

                # fallback to Subject when Description missing or empty
                x_labels = df["Description"].replace("", pd.NA).fillna(df["Subject"]).tolist()
                y_values = df["High Rate"].astype(float).round(2).tolist()

                def get_color(value):
                    # value is percent 0..100
                    if value >= 40:
                        return "#5cb85c"  # green
                    elif value >=30:
                        return "#f0ad4e"  # orange
                    else:
                        return "#d9534f"  # red

                options = {
                    "title": {"text": "Top 10 Easiest Subjects (High Grades >=90)", "left": "center"},
                    "tooltip": {"trigger": "axis", "formatter": "{b}: {c}%"},
                    "xAxis": {
                        "type": "category",
                        "data": x_labels,
                        "axisLabel": {"rotate": 30, "interval": 0}
                    },
                    "yAxis": {
                        "type": "value", 
                        "name": "High Grade Rate (%)",
                        "min" : min(y_values)-1,
                        "max" : max(y_values)+1,
                    },
                    "series": [
                        {
                            "data": [
                                {"value": v, "itemStyle": {"color": get_color(v)}}
                                for v in y_values
                            ],
                            "type": "bar",
                            "label": {"show": True, "position": "top", "formatter": "{c}%"}
                        }
                    ]
                }

                st.markdown('''
                The bar chart visualizes the top 10 easiest subjects by high-grade rate (grades ≥ 90%). 
                Bars are color-coded: green represents subjects with the highest success rates, orange for 
                moderate success, and red for lower high-grade rates. This chart allows for quick comparison of 
                subjects where students consistently perform well, 
                helping in curriculum evaluation and identifying exemplary teaching outcomes.
                ''')
                st_echarts(options=options, height="500px")

    elif report == "Average Grades per Teacher":

        st.subheader("👩‍🏫 Average Grades per Teacher")

        # -------------------------
        # Streamlit Filters
        # -------------------------
        with st.spinner(f"Loading courses and school year...", show_time=True):        
            school_years = ["All"] + r.get_Schoolyear_options()
            semesters = ["All"] + r.get_semester_options()

        selected_year = st.selectbox("Select School Year", school_years)
        selected_semester = st.selectbox("Select Semester", semesters)

        # Convert "All" to None for the helper function
        year_filter = None if selected_year == "All" else selected_year
        semester_filter = None if selected_semester == "All" else selected_semester

        # -------------------------
        # Fetch filtered data
        # -------------------------
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):        
            df = r.get_avg_grades_per_teacher(school_year=year_filter, semester=semester_filter)
        st.markdown('''
            The table below lists the computed average grades per teacher, allowing for an easy comparison of a
            cademic performance across faculty members. This provides a straightforward numerical 
            reference that can be used for record-keeping and further analysis.
        ''')

        # -------------------------
        # Find min & max averages
        # -------------------------
        if not df.empty:

            df = df[df["Teacher"].notna() & ~df["Teacher"].isin(["Not Set", ""])] #remove entries that doesnt have assgned grades/teacher
            st.dataframe(df)


            min_avg = df["Average Grade"].min()
            max_avg = df["Average Grade"].max()

            # -------------------------
            # ECharts visualization
            # -------------------------
            options = {
                "title": {"text": "Average Grades per Teacher"},
                "tooltip": {
                    "trigger": "axis",
                    "valueFormatter": "function (value) { return value.toFixed(2); }"
                },
                "xAxis": {
                    "type": "category",
                    "data": df["Teacher"].tolist(),
                    "axisLabel": {"rotate": 45}
                },
                "yAxis": {
                    "type": "value",
                    "name": "Average Grade",
                    "min": float(min_avg),
                    "max": float(max_avg),
                    "axisLabel": {
                        "valueFormatter": "function (value) { return value.toFixed(2); }"
                    }
                },
                "visualMap": {
                    "type": "continuous",
                    "min": float(min_avg),
                    "max": float(max_avg),
                    "inRange": {
                        "color": ["red", "yellow", "green"]
                    },
                    "calculable": True,
                    "orient": "horizontal",
                    "left": "center",
                    "bottom": 10
                },
                "series": [
                    {
                        "data": [round(v, 2) for v in df["Average Grade"].tolist()],
                        "type": "bar",
                        "label": {
                            "show": True,
                            "position": "top",
                            "valueFormatter": "{c:.2f}"
                        }
                    }
                ]
            }

            st.markdown('''
                The bar chart below visually represents the distribution of teachers’ average grades. 
                Using a color gradient from red (lower averages) to green (higher averages), 
                the chart makes it easier to quickly identify performance trends, highlight strengths, 
                and spot areas that may require additional academic support.
            ''')
            st_echarts(options=options, height="500px")
        else:
            st.info("No data available for the selected filters.")


    elif report == "Teachers with High Failures":

        # -------------------------
        # Streamlit Filters
        # -------------------------
        with st.spinner(f"Loading courses and school year...", show_time=True):
            school_years = ["All"] + r.get_Schoolyear_options()
            semesters = ["All"] + r.get_semester_options()

        selected_year = st.selectbox("Select School Year", school_years)
        selected_semester = st.selectbox("Select Semester", semesters)

        # Convert "All" to None for the helper function
        year_filter = None if selected_year == "All" else selected_year
        semester_filter = None if selected_semester == "All" else selected_semester

        # -------------------------
        # Apply filters
        # -------------------------
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            all_data = r.get_teachers_with_high_failures(school_year=year_filter, semester=semester_filter)
            df = all_data.copy()

        # if sy_selected != "All":
        #     df = df[df["SchoolYear"] == sy_selected]
        # if sem_selected != "All":
        #     df = df[df["Semester"] == sem_selected]

        st.subheader("❌ Teachers with Most Failures")
        st.markdown("""
        The table displays teachers with the highest student failure rates, helping administrators 
        and educators identify instructors whose classes may need additional support or intervention. 
        It provides a clear view of individual teacher performance in terms of student outcomes.
        """)

        

        if not df.empty:
            print('df:',df.iloc[0])
            df = df[df["Teacher"].notna() & ~df["Teacher"].isin(["Not Set", ""])] #remove entries that doesnt have assgned grades/teacher
            st.dataframe(df)
            
            # -------------------------
            # Min & max failure rates
            # -------------------------
            min_rate = df["Failure Rate"].min()
            max_rate = df["Failure Rate"].max()

            # -------------------------
            # ECharts visualization
            # -------------------------
            options = {
                "title": {"text": "Failure Rate per Teacher"},
                "tooltip": {
                    "trigger": "axis",
                    "valueFormatter": "function (p) { return (p.value * 100).toFixed(2) + '%'; }"
                },
                "xAxis": {
                    "type": "category",
                    "data": df["Teacher"].tolist(),
                    "axisLabel": {"rotate": 45}
                },
                "yAxis": {
                    "type": "value",
                    "name": "Failure Rate (%)",
                    "min": float(min_rate),
                    "max": float(max_rate),
                    "axisLabel": {
                        "valueFormatter": "function (value) { return (value * 100).toFixed(0) + '%'; }"
                    }
                },
                "visualMap": {
                    "type": "continuous",
                    "min": float(min_rate),
                    "max": float(max_rate),
                    "inRange": {"color": ["green", "yellow", "red"]},
                    "calculable": True,
                    "orient": "horizontal",
                    "left": "center",
                    "bottom": 10
                },
                "series": [
                    {
                        "data": [round(v, 3) for v in df["Failure Rate"].tolist()],
                        "type": "bar",
                        "label": {
                            "show": True,
                            "position": "top",
                            "valueFormatter": "function (p) { return (p.value * 100).toFixed(1) + '%'; }"
                        }
                    }
                ]
            }

            st.markdown("""
            The bar chart visualizes the failure rate per teacher. Each bar is color-coded with a 
            gradient from red (high failure rate) to green (low failure rate), making it easy to quickly 
            spot teachers whose students are struggling the most. The X-axis lists teachers, and the Y-axis 
            shows their corresponding failure rates in percentages. This visual emphasizes performance 
            differences among teachers and highlights areas requiring attention or improvement.
            """)
            st_echarts(options=options, height="500px")
        else:
            st.info("No records found for the selected filters.")

