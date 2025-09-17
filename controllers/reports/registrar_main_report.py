# report_page.py
import streamlit as st

# import helpers.registrar_main_report_helper as r
import helpers.registrar_main_report_helper as rh

# from helpers.data_helper import student_find    
from streamlit_echarts import st_echarts
import helpers.data_helper as dh
import pandas as pd

def report_page(db):
    r = rh.report_helper({"db": db})
    r2 = dh.data_helper({"db": db})
    st.set_page_config(page_title="Academic Reports", layout="wide")
    st.title("📊 Academic Analytics & Insights")

    report = st.selectbox(
        "Select a Report",
        [
            "-- Select Report --",
            "1. Student Academic Stand",
            "2. Subject Pass/Fail Distribution",
            "3. Enrollment Trend Analysis",
            "4. Incomplete Grades",
            "5. Retention and Dropout Rates",
            "6. Top Performers per Program",
            "7. Curriculum Progress Viewer"
        ]
    )

    if report == "-- Select Report --":
        st.markdown("""
        ### 📑 Overview

        This **Academic Reporting Module** provides a detailed view of student performance, curriculum coverage, 
        subject-level outcomes, and retention metrics. It supports administrators and educators in identifying 
        top performers, at-risk students, and curriculum gaps.

        ---  

        **Reports Available:**

        1. **Student Academic Stand Report** – Identify top achievers and students on probation.
        2. **Subject Pass/Fail Distribution** – Review performance per subject per term.
        3. **Enrollment Trend Analysis** – Track new enrollees, dropouts, and retention rates.
        4. **Incomplete Grades Report** – Follow up on missing or incomplete grades.
        5. **Retention and Dropout Rates** – Measure student persistence across semesters.
        6. **Top Performers per Program** – Highlight the highest GPA students per program.
        7. **Curriculum Progress Viewer** – Track subject requirements, units, and prerequisites.

        ---
        """)

    # ------------------------------
    # 1. Student Academic Stand
    # ------------------------------

    elif report == "1. Student Academic Stand":
        st.subheader("🎓 Student Academic Stand Report")
        st.markdown("""
        **Insight:**  
        Quickly identify **high achievers** for recognition, and **students needing support** for early interventions. This view helps in academic counseling and program-level performance assessment.
        """)

        # --- Filters ---
        courses = ["All"] + r2.get_courses()
        year_levels = ["All"] + r2.get_year_levels()

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)

        # --- Apply filters ---
        course_filter = selected_course if selected_course != "All" else None
        year_level_filter = selected_year_level if selected_year_level != "All" else None

        # -------------------------------
        # A. Dean's List
        # -------------------------------
        st.markdown("### A. Dean's List (:rainbow[Top 10 Students])")
        st.markdown("**Criteria:** No grade < 85% & GPA >= 90%")

        with st.spinner(f"Preparing data for student' academic Stand Reporting - Dean's List.", show_time=True):
            df_deans = r.get_deans_list(course=course_filter, year_level=year_level_filter)  # fetch data

        if not df_deans.empty:
            st.info("No Dean’s List entries found for the chosen semester/year. This means no students met the GPA and grade requirements with the applied filters.")
        else:

            # Display table
            st.dataframe(df_deans, use_container_width=True)

            # Chart data
            names_deans = df_deans["Name"].tolist()
            gpas_deans = df_deans["GPA"].tolist()

            option_deans = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "xAxis": {"type": "value", "name": "GPA", "min": 90},
                "yAxis": {"type": "category", "data": names_deans[::-1]},
                "series": [
                    {
                        "name": "GPA",
                        "type": "bar",
                        "data": gpas_deans[::-1],
                        "label": {"show": True, "position": "right", "formatter": "{c}"},
                        "itemStyle": {
                            "color": {
                                "type": "linear",
                                "x": 0,
                                "y": 0,
                                "x2": 1,
                                "y2": 0,
                                "colorStops": [
                                    {"offset": 0, "color": "#3b82f6"},
                                    {"offset": 1, "color": "#10b981"},
                                ],
                            }
                        },
                    }
                ],
            }

        # -------------------------------
        # B. Academic Probation
        # -------------------------------
        st.markdown("### B. Academic Probation (10 Students)")
        st.markdown("**Criteria:** No grade < 75 OR >= 30% FAILS")

        with st.spinner(f"Preparing data for academic probation.", show_time=True):
            df_probation = r.get_academic_probation_batch_checkpoint(course=course_filter, year_level=year_level_filter)

        if not df_probation.empty:

            # Display table
            st.dataframe(df_probation, use_container_width=True)

            # Chart data (safe conversion)
            required_cols = ["Name", "GPA", "Fail%"]
            if not all(col in df_probation.columns for col in required_cols):
                st.error(f"❌ Missing required columns: {required_cols}")
                st.write("Available columns:", df_probation.columns.tolist())
            else:
                df_probation["GPA"] = pd.to_numeric(df_probation["GPA"], errors="coerce")
                df_probation["Fail%"] = pd.to_numeric(df_probation["Fail%"], errors="coerce")

                names_prob = df_probation["Name"].astype(str).tolist()
                gpas_prob = df_probation["GPA"].fillna(0).tolist()
                fails_prob = df_probation["Fail%"].fillna(0).tolist()

                option_prob = {
                    "tooltip": {"trigger": "axis"},
                    "legend": {"data": ["GPA", "Fail%"]},
                    "xAxis": [{"type": "value", "name": "Score"}],
                    "yAxis": [{"type": "category", "data": names_prob[::-1]}],
                    "series": [
                        {
                            "name": "GPA",
                            "type": "bar",
                            "data": gpas_prob[::-1],
                            "label": {"show": True, "position": "right"},
                            "itemStyle": {"color": "#ef4444"},
                        },
                        {
                            "name": "Fail%",
                            "type": "line",
                            "data": fails_prob[::-1],
                            "label": {"show": True, "position": "top"},
                            "lineStyle": {"color": "#f59e0b", "width": 2},
                            "symbol": "circle",
                            "symbolSize": 8,
                        },
                    ],
                }


                # -------------------------------
                # Show Charts Side by Side
                # -------------------------------
                st.markdown("### 📊 Visual Comparison")

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### 🏅 Dean's List")
                st_echarts(option_deans, height="500px", key="deans_chart")

            with col2:
                st.markdown("#### ⚠️ Academic Probation")
                st_echarts(option_prob, height="500px", key="probation_chart")


    # ------------------------------
    # 2. Subject Pass/Fail Distribution
    # ------------------------------
    elif report == "2. Subject Pass/Fail Distribution":
        st.subheader("📊 Subject Pass/Fail Distribution")
        
        # --- Filters ---
        courses = ["All"] + r2.get_courses()
        year_levels = ["All"] + r2.get_year_levels()

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)

        # --- Apply filters ---
        course_filter = selected_course if selected_course != "All" else None
        year_level_filter = selected_year_level if selected_year_level != "All" else None

        with st.spinner(f"Preparing data for {report}.", show_time = True):
            df_subjects = r.get_subject_pass_fail(course=course_filter, year_level=year_level_filter)  # columns: ['Subject Code', 'Subject Name', 'Semester', 'Pass Count', 'Fail Count', 'Pass %', 'Fail %']
        st.dataframe(df_subjects)

        st.markdown("""
        **Insight:**  
        Provides a clear picture of **subject-level performance per semester**, enabling targeted support for subjects 
        with higher failure rates. Administrators can plan remediation programs effectively.
        """)

        if not df_subjects.empty:
            # Aggregate data by Subject Code and Subject Name
            df_chart = df_subjects.groupby(['Subject Code', 'Subject Name']).agg(
                {'Pass Count': 'sum', 'Fail Count': 'sum'}
            ).reset_index()

            # Calculate totals and percentages (good practice)
            df_chart['Total Count'] = df_chart['Pass Count'] + df_chart['Fail Count']
            df_chart['Pass %'] = (df_chart['Pass Count'] / df_chart['Total Count']) * 100
            df_chart['Fail %'] = (df_chart['Fail Count'] / df_chart['Total Count']) * 100
            
            # Stacked ECharts
            option = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "legend": {"data": ["Pass Count", "Fail Count"]},  # optional order for legend
                "xAxis": [
                    {
                        "type": "category",
                        "data": df_chart["Subject Name"].tolist(),
                        "axisLabel": {"interval": 0, "rotate": 30},
                    }
                ],
                "yAxis": [{"type": "value", "name": "Students"}],
                "series": [
                    {
                        "name": "Fail Count",
                        "type": "bar",
                        "stack": "total",
                        "emphasis": {"focus": "series"},
                        "data": df_chart["Fail Count"].tolist(),
                        "itemStyle": {"color": "#ef4444"},
                    },
                    {
                        "name": "Pass Count",
                        "type": "bar",
                        "stack": "total",
                        "emphasis": {"focus": "series"},
                        "data": df_chart["Pass Count"].tolist(),
                        "itemStyle": {"color": "#3b82f6"},
                    }
                ],
            }
            st_echarts(options=option, height="500px")

    # ------------------------------
    # 3. Enrollment Trend Analysis
    # ------------------------------
    elif report == "3. Enrollment Trend Analysis":
        st.subheader("📈 Enrollment Trend Analysis")

        # --- Filters ---
        courses = ["All"] + r2.get_courses()
        year_levels = ["All"] + r2.get_year_levels()

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)

        # --- Apply filters ---
        course_filter = selected_course if selected_course != "All" else None
        year_level_filter = selected_year_level if selected_year_level != "All" else None

        with st.spinner(f"Preparing data for {report}.", show_time = True):
            df_enrollment = r.get_enrollment_trend(course=course_filter, year_level=year_level_filter)  # columns: ['Semester', 'Total Enrollment', 'New Enrollees', 'Dropouts', 'Retention Rate (%)']
        st.dataframe(df_enrollment)

        st.markdown("""
        **Insight:**  
        Observe semester-to-semester enrollment trends, **track retention rates**, and identify patterns of student dropouts. 
        Helps institutions plan resource allocation and intervention strategies.
        """)


        # Prepare ECharts options
        option = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["Total Enrollment", "New Enrollees", "Dropouts", "Retention Rate (%)"]},
            "xAxis": {"type": "category", "data": df_enrollment["Semester"].tolist()},
            "yAxis": [
                {"type": "value", "name": "Students"},
                {"type": "value", "name": "Retention (%)", "min": 0, "max": 100}
            ],
            "series": [
                {
                    "name": "Total Enrollment",
                    "type": "bar",
                    "data": df_enrollment["Total Enrollment"].tolist()
                },
                {
                    "name": "New Enrollees",
                    "type": "bar",
                    "data": df_enrollment["New Enrollees"].tolist()
                },
                {
                    "name": "Dropouts",
                    "type": "bar",
                    "data": df_enrollment["Dropouts"].tolist()
                },
                {
                    "name": "Retention Rate (%)",
                    "type": "line",
                    "yAxisIndex": 1,
                    "data": df_enrollment["Retention Rate (%)"].tolist()
                }
            ]
        }

        st_echarts(options=option, height="450px")

    # ------------------------------
    # 4. Incomplete Grades
    # ------------------------------
    elif report == "4. Incomplete Grades":
        st.subheader("⚠️ Incomplete Grades Report")

        # --- Filters ---
        courses = ["All"] + r2.get_courses()
        year_levels = ["All"] + r2.get_year_levels()

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)

        # --- Apply filters ---
        course_filter = selected_course if selected_course != "All" else None
        year_level_filter = selected_year_level if selected_year_level != "All" else None

        with st.spinner(f"Preparing data for {report}.", show_time = True):
            df_incomplete = r.get_incomplete_grades(course=course_filter, year_level=year_level_filter)  # columns: ['Student ID', 'Name', 'Course Code', 'Course Title', 'Term', 'Grade Status']
        st.dataframe(df_incomplete)

        st.markdown("""
        **Insight:**  
        Enables the Registrar’s Office to follow up with **students and instructors** regarding incomplete or missing grades, 
        ensuring timely grade submissions.
        """)

        if not df_incomplete.empty:
            # --- Chart ---
            st.markdown("### 📊 Incomplete Grades per Course")

            # Group by course and count
            incomplete_counts = df_incomplete.groupby("Course Title").size().reset_index(name="Count")
            incomplete_counts = incomplete_counts.sort_values("Count", ascending=False)

            option = {
                "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                "xAxis": {
                    "type": "category",
                    "data": incomplete_counts["Course Title"].tolist(),
                    "axisLabel": {"interval": 0, "rotate": 30},
                },
                "yAxis": {"type": "value", "name": "Number of Incomplete Grades"},
                "series": [{
                    "name": "Incomplete Grades",
                    "type": "bar",
                    "data": incomplete_counts["Count"].tolist(),
                    "itemStyle": {"color": "#f59e0b"},
                    "label": {"show": True, "position": "top"}
                }]
            }
            st_echarts(options=option, height="500px")

    # ------------------------------
    # 5. Retention and Dropout Rates
    # ------------------------------
    elif report == "5. Retention and Dropout Rates":
        st.subheader("📊 Retention and Dropout Rates")

        # --- Filters ---
        courses = ["All"] + r2.get_courses()
        year_levels = ["All"] + r2.get_year_levels()

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)

        # --- Apply filters ---
        course_filter = selected_course if selected_course != "All" else None
        year_level_filter = selected_year_level if selected_year_level != "All" else None

        with st.spinner(f"Preparing data for {report}.", show_time = True):
            df_retention = r.get_retention_rates(course=course_filter, year_level=year_level_filter)  # columns: ['Semester to Semester', 'Retained', 'Dropped Out', 'Retention Rate (%)']
        
        st.dataframe(df_retention)

        st.markdown("""
        **Insight:**  
        Measures **student persistence** across semesters and identifies retention issues early, 
        providing actionable data for academic planning and intervention programs.
        """)

        if not df_retention.empty:
            # --- Chart ---
            st.markdown("### 📊 Retention vs. Dropout")

            option = {
                "tooltip": {"trigger": "axis"},
                "legend": {"data": ["Retained", "Dropped Out", "Retention Rate (%)"]},
                "xAxis": {
                    "type": "category",
                    "data": df_retention["Semester"].tolist(),
                    "axisLabel": {"interval": 0, "rotate": 30},
                },
                "yAxis": [
                    {"type": "value", "name": "Number of Students"},
                    {"type": "value", "name": "Rate (%)", "min": 0, "max": 100}
                ],
                "series": [
                    {
                        "name": "Retained",
                        "type": "bar",
                        "data": df_retention["Retained"].tolist(),
                        "itemStyle": {"color": "#10b981"}
                    },
                    {
                        "name": "Dropped Out",
                        "type": "bar",
                        "data": df_retention["Dropped Out"].tolist(),
                        "itemStyle": {"color": "#ef4444"}
                    },
                    {
                        "name": "Retention Rate (%)",
                        "type": "line",
                        "yAxisIndex": 1,
                        "data": df_retention["Retention Rate (%)"].tolist(),
                        "itemStyle": {"color": "#3b82f6"}
                    }
                ]
            }
            st_echarts(options=option, height="500px")

    # ------------------------------
    # 6. Top Performers per Program
    # ------------------------------
    elif report == "6. Top Performers per Program":
        st.subheader("🏆 Top Performers per Program")
        
        # --- Filters ---
        courses = ["All"] + r2.get_courses()
        year_levels = ["All"] + r2.get_year_levels()

        col1, col2 = st.columns(2)
        with col1:
            selected_course = st.selectbox("Filter by Course", courses)
        with col2:
            selected_year_level = st.selectbox("Filter by Year Level", year_levels)

        # --- Apply filters ---
        course_filter = selected_course if selected_course != "All" else None
        year_level_filter = selected_year_level if selected_year_level != "All" else None

        with st.spinner(f"Preparing data for {report}.", show_time = True):
            df_top = r.get_top_performers(course=course_filter, year_level=year_level_filter)  # columns: ['Program', 'Semester', 'Student ID', 'Student Name', 'GPA', 'Rank']
        
        st.dataframe(df_top)

        st.markdown("""
        **Insight:**  
        Highlights **high-achieving students** in each program. Useful for **recognition, awards, and program benchmarking**.
        """)

        if not df_top.empty:
            # --- Chart ---
            st.markdown("### 📊 Top 5 Performers by GPA per Program")

            # Filter for top 5 in each program
            df_top_5 = df_top[df_top['Rank'] <= 5]

            # Create a chart for each program
            programs = df_top_5['Program'].unique()
            for program in programs:
                st.markdown(f"#### {program}")
                program_data = df_top_5[df_top_5['Program'] == program]

                option = {
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                    "xAxis": {
                        "type": "category",
                        "data": program_data["Student Name"].tolist(),
                        "axisLabel": {"interval": 0, "rotate": 30},
                    },
                    "yAxis": {"type": "value", "name": "GPA", "min": 85},
                    "series": [{
                        "name": "GPA",
                        "type": "bar",
                        "data": program_data["GPA"].tolist(),
                        "label": {"show": True, "position": "top"},
                        "itemStyle": {
                            "color": {
                                "type": "linear", "x": 0, "y": 0, "x2": 0, "y2": 1,
                                "colorStops": [
                                    {"offset": 0, "color": "#10b981"},
                                    {"offset": 1, "color": "#3b82f6"}
                                ]
                            }
                        }
                    }]
                }
                st_echarts(options=option, height="400px", key=f"top_performers_{program}")

    # ------------------------------
    # 7. Curriculum Progress Viewer
    # ------------------------------
    elif report == "7. Curriculum Progress Viewer":
        st.subheader("📚 Curriculum Progress Viewer")

        # --- Step 1: Select Course ---
        courses = sorted(db.students.distinct("Course"))
        selected_course = st.selectbox("Select Course:", courses)

        # --- Step 2: Search Student by Name ---
        search_name = st.text_input("Search Student by Name (wildcard):")
        search_trigger = st.button("Search Student")

        if search_trigger:
            if search_name.strip():
                with st.spinner("Searching please wait...",show_time=True):
                    results = r2.student_find(search_name, db.students, course=selected_course)
                if results:
                    st.session_state.search_results = results
                else:
                    st.warning("No student found.")
                    st.session_state.search_results = []
            else:
                st.warning("Please enter a name to search.")
                st.session_state.search_results = []

        # --- Step 3: Show search results as inline rows with select buttons ---
        if "search_results" in st.session_state and st.session_state.search_results:
            st.subheader("Search Results")
            for student in st.session_state.search_results:
                col1, col2 = st.columns([5, 1])
                col1.write(f"{student['Name']} | {student.get('Course','')} | Year Level: {student.get('YearLevel','')}")
                if col2.button("Select", key=f"select_{student['_id']}"):
                    st.session_state.selected_student = student
                    st.session_state.search_results = []  # clear search results
                    st.rerun()  # reload page to show curriculum


        # --- Step 4: Display Curriculum if a student is selected ---
        if (
            "selected_student" in st.session_state 
            and st.session_state.selected_student 
            and search_trigger is False  # only show after explicit selection, not auto-load
        ):
            student = st.session_state.selected_student
            st.markdown(f"""
            <div style="border:2px solid #1E90FF; padding:10px; border-radius:5px; background-color:#E6F0FF">
            <strong>Name:</strong> {student['Name']}<br>
            <strong>Student ID:</strong> {student['_id']}<br>
            <strong>Course:</strong> {student['Course']}<br>
            <strong>Year Level:</strong> {student.get('YearLevel', '')}<br>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner(f"Loading curriculum for {student['Course']}..."):
                df_curriculum = r.get_curriculum_progress(program=student['Course'])

            if not df_curriculum.empty:
                df_curriculum = df_curriculum.sort_values(["Year", "Semester", "Subject Code"])
                years = df_curriculum['Year'].unique()

                for year in years:
                    with st.expander(f"🎓 Year: {year}", expanded=True):
                        year_data = df_curriculum[df_curriculum['Year'] == year]
                        semesters = year_data['Semester'].unique()
                        for semester in semesters:
                            with st.expander(f"📚 Semester: {semester}", expanded=True):
                                sem_data = year_data[year_data['Semester'] == semester]
                                sem_display = sem_data[[
                                    "Subject Code", "Subject Description", "Lec Hours",
                                    "Lab Hours", "Units", "Prerequisites"
                                ]]
                                st.dataframe(sem_display, use_container_width=True)
                                total_units = sem_data["Units"].sum()
                                st.markdown(f"**Total Units:** {total_units}")

                # --- Chart for Curriculum ---
                st.markdown("### 📊 Curriculum Workload Distribution")

                # Group by Year and Semester to sum units
                workload = df_curriculum.groupby(['Year', 'Semester'])['Units'].sum().reset_index()
                workload['Term'] = workload['Year'].astype(str) + ' - ' + workload['Semester'].astype(str)

                option = {
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                    "xAxis": {
                        "type": "category",
                        "data": workload["Term"].tolist(),
                        "name": "Term"
                    },
                    "yAxis": {"type": "value", "name": "Total Units"},
                    "series": [{
                        "name": "Total Units",
                        "type": "bar",
                        "data": workload["Units"].tolist(),
                        "label": {"show": True, "position": "top"},
                        "itemStyle": {"color": "#8369CF"}
                    }]
                }
                st_echarts(options=option, height="400px")


        st.markdown("""
        **Insight:**  
        Provides a comprehensive view of curriculum structure, subject prerequisites, and credit distribution.  
        Supports **curriculum planning and academic advising** for students to track progress toward graduation.
        """)
