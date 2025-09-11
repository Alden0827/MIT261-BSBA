

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
from streamlit_echarts import st_echarts, JsCode
import pandas as pd
import report_helper as r
from report_helper import db
from report_helper import get_Schoolyear_options, get_course_options


# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title=" Analytics Reports", layout="wide")
st.title("📊 Analytics & Visualization")

report = st.selectbox(
    "Select a Report",
    [
        "-- Select Report --",
        # "Top Performers",
        # "Failing Students",
        # "Students with Grade Improvement",
        # "Distribution of Grades",
        # "Hardest Subject",
        # "Easiest Subjects",
        # "Average Grades per Teacher",
        # "Teachers with High Failures",
        # "Grade Trend per Course",
        # "Subject Load Intensity",
        # "GE vs Major Subjects Performance",
        # "Semester with Lowest GPA",
        # "Best Performing Semester",
        # "Grade Deviation Across Semesters",
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
        # Reporting Module Overview

        The **Reporting Module** provides comprehensive insights into student academic performance, teacher efficiency, course trends, and subject difficulty.

        ---

        ## Reports Available

        ### 1. Top Performers
        - **Purpose:** Identify students with the highest grades.
        - **Metrics:** Student name, ID, course, average grade.

        ### 2. Failing Students
        - **Purpose:** Highlight students with failing grades.
        - **Metrics:** Student name, ID, course, failed subjects, average grade.

        ### 3. Students with Grade Improvement
        - **Purpose:** Track students who have shown improvement.
        - **Metrics:** Student name, ID, previous grades, current grades, improvement %.

        ### 4. Distribution of Grades
        - **Purpose:** Visualize the distribution of grades.
        - **Metrics:** Frequency of each grade or grade range.

        ### 5. Hardest Subject
        - **Purpose:** Subjects with the lowest average grades.
        - **Metrics:** Subject name, average grade, failure rate.

        ### 6. Easiest Subjects
        - **Purpose:** Subjects with the highest average grades.
        - **Metrics:** Subject name, average grade, pass rate.

        ### 7. Average Grades per Teacher
        - **Purpose:** Evaluate teacher performance.
        - **Metrics:** Teacher name, subjects taught, student averages.

        ### 8. Teachers with High Failures
        - **Purpose:** Identify teachers whose students have high failure rates.
        - **Metrics:** Teacher name, subjects taught, failing students.

        ### 9. Grade Trend per Course
        - **Purpose:** Track performance trends per course.
        - **Metrics:** Course, semester/year, average grade trend.

        ### 10. Subject Load Intensity
        - **Purpose:** Analyze subjects taken per student.
        - **Metrics:** Student ID, total subjects per semester.

        ### 11. GE vs Major Subjects Performance
        - **Purpose:** Compare student performance in GE vs Major subjects.
        - **Metrics:** Student ID, GE average, Major average, difference.

        ### 12. Semester with Lowest GPA
        - **Purpose:** Identify the semester with the lowest GPA.
        - **Metrics:** Semester, average GPA, total failing students.

        ### 13. Best Performing Semester
        - **Purpose:** Highlight the semester with highest performance.
        - **Metrics:** Semester, average GPA, top students.

        ### 14. Grade Deviation Across Semesters
        - **Purpose:** Measure variation in student grades.
        - **Metrics:** Student ID, grade deviation %.

        ### 15. Year Level Distribution
        - **Purpose:** Show student distribution across year levels.
        - **Metrics:** Year level, number of students.

        ### 16. Student Count per Course
        - **Purpose:** Count students in each course.
        - **Metrics:** Course name, total students.

        ### 17. Performance by Year Level
        - **Purpose:** Analyze performance by year level.
        - **Metrics:** Year level, average grade, highest/lowest grade.

        ---

        ## Features
        - **Filters:** Course, semester, school year, teacher, student.
        - **Visualization:** Charts, graphs, tables.
        - **Export Options:** CSV, Excel, PDF.
        - **Interactivity:** Drill-down to individual student or subject performance.
        - **Insights:** Identify trends, improvements, and areas requiring attention.
        """)


if report == "Top Performers":
    print('Loading ', report)

    # --- Let user select filters first ---
    col_a, col_b = st.columns([2, 2])
    with col_a:
        sem_selected = st.selectbox("Semester", r.get_semester_options())  # helper or query
    with col_b:
        sy_selected = st.selectbox("School Year", r.get_Schoolyear_options())  # helper or query

    # --- Fetch data with parameters (ONE CALL ONLY) ---
    all_data = r.get_top_performers(school_year=sy_selected, semester=sem_selected)

    print('displaying ', report)
    print('data:', all_data)

    if not all_data.empty:
        df_top = all_data.sort_values("Average", ascending=False).head(10)

        st.subheader("🏆 Top 10 Performers")
        '''
        The table below presents the Top 10 Performers for the selected semester and school year. 
        It provides detailed information on each student’s average grade, giving a clear picture of the highest achievers during the period.
        '''
        st.dataframe(df_top)

        '''
        The horizontal bar chart highlights the top 10 students and their corresponding average grades, 
        making it easy to compare performance at a glance. Alongside, the pie chart shows the distribution 
        of these top performers by course, allowing a quick understanding of which programs or 
        courses have produced the most high-achieving students. 
        Together, these visualizations provide both individual 
        recognition and an overview of academic excellence across courses.
        '''

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
        '''
        The table lists all students with high failure rates based on the selected semester and school year. 
        It provides a detailed breakdown of each student’s academic performance, including the number of failed subjects. 
        This allows educators and administrators to identify at-risk students who may need further academic support or intervention.
        '''
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

            '''
            The heatmap compares students against their enrolled courses, showing the intensity of failures per course. 
            Darker or warmer colors represent higher failure counts, giving a clear visual signal of s
            tudents and courses that require attention.
            '''
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
            '''
            The pie chart summarizes total failures by course, offering insights into which subjects consistently present challenges to students.
            '''
            st_echarts(options=options2, height="400px")

            # --- Chart 3: Failure Rate Trend (Line) ---
            trend_data = all_data.groupby(["SchoolYear", "Semester"]).agg(
                {"Failures": "sum", "Subjects Taken": "sum"}
            ).reset_index()
            trend_data["FailureRate"] = trend_data["Failures"] / trend_data["Subjects Taken"]

            # Clean data
            trend_data = trend_data.dropna(subset=["Semester", "SchoolYear"])

            # Define semester order
            semester_order = ["1st", "2nd", "Summer"]
            trend_data["Semester"] = pd.Categorical(
                trend_data["Semester"],
                categories=semester_order,
                ordered=True
            )

            # Create continuous X-axis: "2023 1st", "2023 2nd", ...
            trend_data["YearSemester"] = (
                trend_data["SchoolYear"].astype(str) + " " + trend_data["Semester"].astype(str)
            )
            trend_data = trend_data.sort_values(["SchoolYear", "Semester"])

            x_axis = trend_data["YearSemester"].tolist()
            fail_rates = [round(v * 100, 1) for v in trend_data["FailureRate"]]

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
            '''
            The line chart illustrates the failure rate trend over time across different school years and semesters. 
            By tracking changes in failure percentages, this visualization highlights patterns and helps in monitoring 
            whether interventions are effective in reducing failures.
            '''
            st_echarts(options=options3, height="400px")


        else:
            st.info("No failing students found for the selected Semester and School Year.")
    else:
        st.info("No student records found.")

elif report == "Students with Grade Improvement":
    # Load all data first (unfiltered)
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
        '''
        The table below lists all students who have shown improvement in their grades for the selected semester and school year. 
        It provides a clear overview of individual progress, allowing educators to identify students who are benefiting from interventions or extra support.
        '''

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
        '''
        The bar chart visualizes the Top 15 students with the highest grade improvement. 
        Using a gradient from green to yellow, the chart highlights the degree of improvement for each student. 
        The X-axis dynamically adjusts to the minimum and maximum improvement values, 
        ensuring that even small gains are visible. 
        This visualization makes it easy to quickly recognize top improvers and compare performance across students.
        '''
        st_echarts(option, height="500px")

    else:
        st.info("No student records found for the selected School Year / Semester.")


elif report == "Distribution of Grades":
    st.subheader("📊 Grade Distribution")
    '''
    The table below provides a detailed view of student performance for the selected semester and school year, 
    allowing educators to inspect exact grades and identify trends in individual performance.
    '''
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
        '''
        The bar chart visualizes the distribution of grades across defined ranges. 
        Each bar represents the frequency of students falling into a particular grade bracket. 
        Color coding highlights performance levels: red indicates failing grades, orange 
        shows average performance, and green represents high achievement. This visualization 
        makes it easy to quickly assess overall class performance, identify clusters of low or 
        high scores, and evaluate the effectiveness of teaching interventions.
        '''
        st_echarts(option, height="400px")
    else:
        st.info("No grades found for the selected Semester/School Year.")


elif report == "Hardest Subject":
    # --- Dropdown filters ---

    col1, col2 = st.columns([2, 2])

    courses = sorted(get_course_options())
    school_years = sorted(get_Schoolyear_options())

    with col1:
        course_selected = st.selectbox("Course", ["All"] + courses)
    with col2:
        sy_selected = st.selectbox("School Year", ["All"] + school_years)

    # --- Apply filters ---
    course_filter = None if course_selected == "All" else course_selected
    sy_filter = None if sy_selected == "All" else sy_selected

    print("Selected course:", course_selected)
    print("Selected school year:", sy_selected)

    df = r.get_hardest_subject(course=course_filter, school_year=sy_filter)

    if not df.empty:

        st.subheader("📉 Hardest Subjects")

        # --- Add ECharts Bar Chart ---
        if not df.empty:

            '''
            The table lists subjects with the highest failure rates based on the selected course and school year. 
            It allows educators to identify which subjects consistently challenge students 
            and may require additional support, curriculum review, or targeted interventions.
            '''
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
            '''
            The bar chart visualizes the top 10 hardest subjects by failure rate. 
            Bars are color-coded for clarity: green indicates low failure rates, 
            orange represents moderate difficulty, and red highlights the most challenging subjects. 
            The chart allows for quick comparison between subjects, making it easy to pinpoint 
            areas where students struggle the most and prioritize academic support.
            '''
            st_echarts(options=options, height="500px")




elif report == "Easiest Subjects":
    # --- Dropdown filters ---


    col1, col2 = st.columns([2, 2])

    courses = sorted(get_course_options())
    school_years = sorted(get_Schoolyear_options())

    with col1:
        course_selected = st.selectbox("Course", ["All"] + courses)
    with col2:
        sy_selected = st.selectbox("School Year", ["All"] + school_years)

    # --- Apply filters ---
    course_filter = None if course_selected == "All" else course_selected
    sy_filter = None if sy_selected == "All" else sy_selected

    df = r.get_easiest_subjects(course=course_filter, school_year=sy_filter)

    if not df.empty:

        st.subheader("📈 Easiest Subjects")
        '''
        The table lists subjects where students achieve the highest grades, 
        based on the selected course and school year. This provides a clear 
        view of subjects in which students excel, helping educators recognize 
        areas of strength and effective teaching practices.
        '''
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

            '''
            The bar chart visualizes the top 10 easiest subjects by high-grade rate (grades ≥ 90%). 
            Bars are color-coded: green represents subjects with the highest success rates, orange for 
            moderate success, and red for lower high-grade rates. This chart allows for quick comparison of 
            subjects where students consistently perform well, 
            helping in curriculum evaluation and identifying exemplary teaching outcomes.
            '''
            st_echarts(options=options, height="500px")

elif report == "Average Grades per Teacher":

    st.subheader("👩‍🏫 Average Grades per Teacher")

    # -------------------------
    # Streamlit Filters
    # -------------------------
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
    df = r.get_avg_grades_per_teacher(school_year=year_filter, semester=semester_filter)
    '''
        The table below lists the computed average grades per teacher, allowing for an easy comparison of a
        cademic performance across faculty members. This provides a straightforward numerical 
        reference that can be used for record-keeping and further analysis.
    '''
    st.dataframe(df)

    # -------------------------
    # Find min & max averages
    # -------------------------
    if not df.empty:
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

        '''
            The bar chart below visually represents the distribution of teachers’ average grades. 
            Using a color gradient from red (lower averages) to green (higher averages), 
            the chart makes it easier to quickly identify performance trends, highlight strengths, 
            and spot areas that may require additional academic support.
        '''
        st_echarts(options=options, height="500px")
    else:
        st.info("No data available for the selected filters.")


elif report == "Teachers with High Failures":

    # -------------------------
    # Streamlit Filters
    # -------------------------
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

    st.dataframe(df)

    if not df.empty:
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


elif report == "Semester with Lowest GPA":
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


elif report == "Year Level Distribution":
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
    df = r.get_performance_by_year_level()  # DataFrame with columns: YearLevel, Average

    # Prepare chart data
    year_levels = df["YearLevel"].tolist()
    averages = df["Average"].tolist()
    min_avg = min(averages) - 100
    max_avg = max(averages) + 100

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
