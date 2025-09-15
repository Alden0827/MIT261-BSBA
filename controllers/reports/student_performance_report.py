

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
            # A. Student Performance Analytics
            "Top Performers",
            "Failing Students",
            "Students with Grade Improvement",
            "Distribution of Grades",

        ]
    )


    # ------------------------------
    # Report Logic
    # ------------------------------
    if report == "-- Select Report --":
        st.markdown("""
            ## A. Student Performance Analytics

            The **Student Performance Analytics** dashboard provides detailed insights into how students are performing academically.  
            It helps educators, administrators, and program coordinators **monitor progress, identify risks, and celebrate achievements**.

            ---

            ## 📊 Reports Available

            ### 🏆 Top Performers
            - **Purpose:** Identify students with the highest grades.  
            - **Metrics:** Student name, ID, course, average grade, ranking.  

            ### 📉 Failing Students
            - **Purpose:** Highlight students with failing grades.  
            - **Metrics:** Student name, ID, course, failed subjects, number of failures, average grade.  

            ### 📈 Students with Grade Improvement
            - **Purpose:** Track students who have shown academic progress.  
            - **Metrics:** Student name, ID, previous grades, current grades, improvement %.  

            ### 📊 Distribution of Grades
            - **Purpose:** Visualize the spread of grades across classes or programs.  
            - **Metrics:** Grade ranges (e.g., 60–65, 66–70), frequency, performance clusters.  

            ---

            ## ⚙️ Features
            - 🔍 **Filters:** Course, semester, school year, teacher, student.  
            - 📈 **Visualizations:** Interactive charts, graphs, and summary tables.  
            - 📂 **Export Options:** CSV, Excel, PDF.  
            - 🖱 **Interactivity:** Drill down to individual student or subject performance.  
            - 💡 **Insights:** Identify trends, improvements, and areas requiring attention.  

            """)


    if report == "Top Performers":
                
        # --- Let user select filters first ---
        col_a, col_b = st.columns([2, 2])
        with col_a:
            sem_selected = st.selectbox("Semester", r.get_semester_options())  # helper or query
        with col_b:
            sy_selected = st.selectbox("School Year", r.get_Schoolyear_options())  # helper or query

        # --- Fetch data with parameters (ONE CALL ONLY) ---
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            all_data = r.get_top_performers(school_year=sy_selected, semester=sem_selected)

        print('displaying ', report)
        print('data:', all_data)

        if not all_data.empty:
            df_top = all_data.sort_values("Average", ascending=False).head(10)

            st.subheader("🏆 Top 10 Performers")
            st.markdown('''
            The table below presents the Top 10 Performers for the selected semester and school year. 
            It provides detailed information on each student’s average grade, giving a clear picture of the highest achievers during the period.
            ''')
            st.dataframe(df_top)

            st.markdown('''
            The horizontal bar chart highlights the top 10 students and their corresponding average grades, 
            making it easy to compare performance at a glance. Alongside, the pie chart shows the distribution 
            of these top performers by course, allowing a quick understanding of which programs or 
            courses have produced the most high-achieving students. 
            Together, these visualizations provide both individual 
            recognition and an overview of academic excellence across courses.
            ''')

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

    if report == "Failing Students":
        # --- Fetch all failing students (unfiltered) for dropdowns ---
        
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            all_data = r.get_failing_students()

        if not all_data.empty:

            # --- Dropdown filters ---
            col1, col2 = st.columns([2, 2])
            with col1:
                sem_selected = st.selectbox(
                    "Semester",
                    sorted(all_data["Semester"].dropna().unique())
                )
            with col2:
                sy_selected = st.selectbox(
                    "School Year",
                    sorted(all_data["SchoolYear"].dropna().unique())
                )

            # --- Apply filters ---
            df_fails = r.get_failing_students(
                school_year=sy_selected, semester=sem_selected
            )

            st.subheader("📉 Students with High Failure Rate")
            st.markdown('''
            The table lists all students with high failure rates based on the selected semester and school year. 
            It provides a detailed breakdown of each student’s academic performance, including the number of failed subjects. 
            This allows educators and administrators to identify at-risk students who may need further academic support or intervention.
            ''')
            if not df_fails.empty:
                # --- Table ---
                st.dataframe(df_fails)

                # --- Chart 1: Failures Heatmap (Student vs Course) ---
                student_failures = df_fails.groupby(["Student", "Course"])["Failures"].sum().reset_index()

                students = student_failures["Student"].unique().tolist()
                courses = student_failures["Course"].unique().tolist()

                heatmap_data = [
                    [courses.index(row["Course"]), students.index(row["Student"]), int(row["Failures"])]
                    for _, row in student_failures.iterrows()
                ]
                options1 = {
                    "title": {"text": "Failures per Student by Course"},
                    "tooltip": {
                        "position": "top",
                        "valueFormatter": """
                            function (params) {
                                let student = params.name;      // y-axis = student
                                let course = params.seriesName; // we override below
                                if (params.data) {
                                    let c = params.data[0]; // x index
                                    let s = params.data[1]; // y index
                                    let val = params.data[2]; // failures
                                    course = params.componentSubType === 'heatmap'
                                        ? params.series.xAxis.data[c]
                                        : course;
                                    student = params.series.yAxis.data[s];
                                    return (
                                        '<b>Student:</b> ' + student + '<br>' +
                                        '<b>Course:</b> ' + course + '<br>' +
                                        '<b>Failures:</b> ' + val
                                    );
                                }
                                return '';
                            }
                        """
                    },
                    "grid": {
                        "height": "70%",
                        "top": "10%",
                        "left": "200"   # ✅ wider space for long student names
                    },
                    "xAxis": {
                        "type": "category",
                        "data": courses,
                        "splitArea": {"show": True},
                        "axisLabel": {"rotate": 45}
                    },
                    "yAxis": {
                        "type": "category",
                        "data": students,
                        "splitArea": {"show": True},
                        "axisLabel": {
                            "width": 180,    # ✅ control label width
                            "overflow": "break"  # wrap long names
                        }
                    },
                    "visualMap": {
                        "min": int(student_failures["Failures"].min()),
                        "max": int(student_failures["Failures"].max()),
                        "calculable": True,
                        "orient": "horizontal",
                        "left": "center",
                        "bottom": "5%",
                        "inRange": {
                            "color": ["#e0f3f8", "#fee090", "#f46d43", "#d73027"]
                        }
                    },
                    "series": [{
                        "name": "Failures",
                        "type": "heatmap",
                        "data": heatmap_data,
                        "label": {"show": True},
                        "emphasis": {
                            "itemStyle": {
                                "shadowBlur": 10,
                                "shadowColor": "rgba(0, 0, 0, 0.5)"
                            }
                        }
                    }]
                }

                st.markdown('''
                The heatmap compares students against their enrolled courses, showing the intensity of failures per course. 
                Darker or warmer colors represent higher failure counts, giving a clear visual signal of s
                tudents and courses that require attention.
                ''')
                st_echarts(options=options1, height="1200px")
                # --- Chart 2: Failures by Course (Pie) ---
                course_failures = df_fails.groupby("Course")["Failures"].sum().reset_index()
                options2 = {
                    "title": {"text": "Failures by Course", "left": "center"},
                    "tooltip": {"trigger": "item"},
                    "legend": {"orient": "vertical", "left": "left"},
                    "series": [{
                        "name": "Failures",
                        "type": "pie",
                        "radius": "50%",
                        "data": [
                            {"value": int(v), "name": str(n)}
                            for n, v in zip(course_failures["Course"], course_failures["Failures"])
                        ],
                    }],
                }
                st.markdown('''
                The pie chart summarizes total failures by course, offering insights into which subjects consistently present challenges to students.
                ''')
                st_echarts(options=options2, height="400px")
                # --- Chart 3: Failure Rate Trend (Line) ---
                trend_data = all_data.groupby(["SchoolYear", "Semester"]).agg(
                    {"Failures": "sum", "Subjects Taken": "sum"}
                ).reset_index()
                trend_data["FailureRate"] = trend_data["Failures"] / trend_data["Subjects Taken"]

                # Clean data
                trend_data = trend_data.dropna(subset=["Semester", "SchoolYear"])

                # --- Map semester labels to desired short form ---
                semester_map = {
                    "FirstSem": "1st",
                    "SecondSem": "2nd",
                    "Summer": "Summer"
                }
                trend_data["Semester"] = trend_data["Semester"].map(semester_map)

                # --- Define custom semester order (1st → Summer → 2nd) ---
                semester_order = ["1st", "Summer", "2nd"]
                trend_data["Semester"] = pd.Categorical(
                    trend_data["Semester"],
                    categories=semester_order,
                    ordered=True
                )

                # --- Create continuous X-axis: "2023 1st", "2023 Summer", "2023 2nd" ---
                trend_data["YearSemester"] = (
                    trend_data["SchoolYear"].astype(str) + " " + trend_data["Semester"].astype(str)
                )
                trend_data = trend_data.sort_values(["SchoolYear", "Semester"])

                x_axis = trend_data["YearSemester"].tolist()
                fail_rates = [round(v * 100, 1) for v in trend_data["FailureRate"]][:-1]  #[:-1] is for ommition of the last entry due to now submition yet

                # --- Dynamic Y-axis range ---
                val_min = float(min(fail_rates))
                val_max = float(max(fail_rates))
                if val_min == val_max:  # avoid flat line case
                    val_min -= 1
                    val_max += 1

                options3 = {
                    "title": {"text": "Failure Rate Trend Across Years"},
                    "tooltip": {"trigger": "axis", "formatter": "{b}: {c}%"},
                    "xAxis": {
                        "type": "category",
                        "data": x_axis,
                        "axisLabel": {"rotate": 45}
                    },
                    "yAxis": {
                        "type": "value",
                        "min": val_min - 1,   # ✅ start just below lowest value
                        "max": val_max + 1,   # ✅ end just above highest value
                        "axisLabel": {"formatter": "{value}%"}
                    },
                    "series": [{
                        "name": "Failure Rate",
                        "type": "line",
                        "data": fail_rates,
                        "smooth": True,
                        "symbol": "circle",
                        "symbolSize": 8,
                        "label": {"show": True, "formatter": "{c}%"},
                        "lineStyle": {"width": 3}
                    }],
                    "grid": {"bottom": 100},  # prevent label cutoff
                }

                st.markdown('''
                The line chart illustrates the failure rate trend over time across different school years and semesters. 
                By tracking changes in failure percentages, this visualization highlights patterns and helps in monitoring 
                whether interventions are effective in reducing failures.
                ''')
                st_echarts(options=options3, height="400px")


            else:
                st.info("No failing students found for the selected Semester and School Year.")
        else:
            st.info("No student records found.")

    elif report == "Students with Grade Improvement":
        # Load all data first (unfiltered)
        with st.spinner(f"Preparing data for '{report}' report...", show_time=True):
            all_data = r.get_students_with_improvement()

        # --- Dropdown filters ---
        col1, col2 = st.columns([2, 2])
        with col1:
            sem_selected = st.selectbox(
                "Semester",
                ["All"] + sorted(pd.Series(all_data["Semester"]).dropna().unique())
            )
        with col2:
            sy_selected = st.selectbox(
                "School Year",
                ["All"] + sorted(pd.Series(all_data["SchoolYear"]).dropna().unique())
            )

        # --- Apply filters using selected dropdown values ---
        df = r.get_students_with_improvement(
            selected_semester=sem_selected,
            selected_sy=sy_selected
        )

        st.subheader("📈 Students with Grade Improvement")

        if not df.empty:
            # Show table
            st.markdown('''
            The table below lists all students who have shown improvement in their grades for the selected semester and school year. 
            It provides a clear overview of individual progress, allowing educators to identify students who are benefiting from interventions or extra support.
            ''')

            st.dataframe(df)

            st.subheader("📈 Top 15 Students with Grade Improvement")
            df_top15 = df.head(15).copy()

            # --- Prepare ECharts data ---
            students_labels = df_top15["Student"].tolist()
            improvements = pd.to_numeric(df_top15["Improvement"], errors="coerce").fillna(0).tolist()

            # Ensure min != max
            val_min = float(min(improvements))
            val_max = float(max(improvements))
            
            if val_min == val_max:  
                # avoid flat range → spread artificially
                val_min = val_min - 1
                val_max = val_max + 1

            # --- ECharts config with gradient ---
            option = {
                "title": {
                    "text": f"Top 15 Students with Grade Improvement "
                            f"(Semester: {sem_selected}, SchoolYear: {sy_selected})"
                },
                "tooltip": {
                    "trigger": "axis",
                    "valueFormatter": "function (value) { return value.toFixed(2) + '%'; }"
                },
                "xAxis": {
                    "type": "value",
                    "name": "Improvement (%)",
                    "min": val_min - 1,   # ✅ start axis closer to your lowest value
                    "max": val_max + 1,   # ✅ cap slightly above max
                    "axisLabel": {"formatter": "{value}%"}
                },
                "yAxis": {
                    "type": "category",
                    "data": students_labels,
                    "name": "Student",
                    "inverse": True
                },
                "visualMap": {
                    "type": "continuous",
                    "min": val_min,
                    "max": val_max,
                    "inRange": {
                        "color": ["green", "yellow"]  # ✅ Gradient Red → Yellow → Green
                    },
                    "calculable": True,
                    "orient": "horizontal",
                    "left": "center",
                    "bottom": 10
                },
                "series": [
                    {
                        "data": [round(v, 2) for v in improvements],
                        "type": "bar",
                        "barMaxWidth": "50%",
                        "label": {
                            "show": True,
                            "position": "right",
                            "formatter": "{c}%"
                        }
                    }
                ]
            }
            st.markdown('''
            The bar chart visualizes the Top 15 students with the highest grade improvement. 
            Using a gradient from green to yellow, the chart highlights the degree of improvement for each student. 
            The X-axis dynamically adjusts to the minimum and maximum improvement values, 
            ensuring that even small gains are visible. 
            This visualization makes it easy to quickly recognize top improvers and compare performance across students.
            ''')
            st_echarts(option, height="500px")

        else:
            st.info("No student records found for the selected School Year / Semester.")


    elif report == "Distribution of Grades":
        st.subheader("📊 Grade Distribution")
        st.markdown('''
        The table below provides a detailed view of student performance for the selected semester and school year, 
        allowing educators to inspect exact grades and identify trends in individual performance.
        ''')
        # Load all data first (for filter dropdowns)
        all_data = r.get_distribution_of_grades()  # Returns a DataFrame now

        # --- Dropdown filters ---
        col1, col2 = st.columns([2, 2])
        with col1:
            sem_selected = st.selectbox(
                "Semester",
                ["All"] + sorted(all_data["Semester"].dropna().unique())
            )
        with col2:
            sy_selected = st.selectbox(
                "School Year",
                ["All"] + sorted(all_data["SchoolYear"].dropna().unique())
            )

        # --- Get filtered grades ---
        df_filtered = r.get_distribution_of_grades(
            selected_semester=sem_selected,
            selected_sy=sy_selected
        )

        if not df_filtered.empty:
            # Prepare bins
            bins = [60,65,70,75,80,85,90,95,100]
            bin_labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-1)]
            counts = [0]*(len(bins)-1)

            # Count grades per bin
            for g in df_filtered["Grade"]:
                for i in range(len(bins)-1):
                    if bins[i] <= g < bins[i+1]:
                        counts[i] += 1
                        break

            # Color-coded bins
            colors = []
            for i in range(len(bins)-1):
                if bins[i+1] <= 75:
                    colors.append("#FF4C4C")   # Red → Failing
                elif bins[i+1] <= 90:
                    colors.append("#FFA500")   # Orange → Average
                else:
                    colors.append("#4CAF50")   # Green → High grades

            # --- ECharts Option ---
            option = {
                "title": {"text": f"Grade Distribution (Semester: {sem_selected}, SchoolYear: {sy_selected})"},
                "tooltip": {"trigger": "axis"},
                "xAxis": {"type": "category", "data": bin_labels, "name": "Grade Range"},
                "yAxis": {"type": "value", "name": "Frequency"},
                "series": [{
                    "data": [{"value": count, "itemStyle": {"color": colors[i]}} 
                             for i, count in enumerate(counts)],
                    "type": "bar",
                    "barMaxWidth": "50%"
                }]
            }
            st.markdown('''
            The bar chart visualizes the distribution of grades across defined ranges. 
            Each bar represents the frequency of students falling into a particular grade bracket. 
            Color coding highlights performance levels: red indicates failing grades, orange 
            shows average performance, and green represents high achievement. This visualization 
            makes it easy to quickly assess overall class performance, identify clusters of low or 
            high scores, and evaluate the effectiveness of teaching interventions.
            ''')
            st_echarts(option, height="400px")
        else:
            st.info("No grades found for the selected Semester/School Year.")
