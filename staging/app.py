# report_page.py
import streamlit as st
import pandas as pd
import registrar_report_hepler as r

def report_page(st, db):
    st.set_page_config(page_title="Academic Reports", layout="wide")
    st.title("📊 Student Academic Analytics & Insights")

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
        ## 📑 Overview

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

        st.markdown("### A. Dean's List (Top 10 Students)")
        st.markdown("**Criteria:** No grade < 85% & GPA >= 90%")
        df_deans = r.get_deans_list(db)  # expected columns: ['#', 'ID', 'Name', 'Prog', 'Yr', 'GPA', 'Units', 'High']
        st.dataframe(df_deans)

        st.markdown("### B. Academic Probation (10 Students)")
        st.markdown("**Criteria:** No grade < 75 OR >= 30% FAILS")
        df_probation = r.get_academic_probation(db)  # expected columns: ['#', 'ID', 'Name', 'Prog', 'Yr', 'GPA', 'Units', 'High', 'LOW']
        st.dataframe(df_probation)

        st.markdown("""
        **Insight:**  
        Quickly identify **high achievers** for recognition, and **students needing support** for early interventions. 
        This view helps in academic counseling and program-level performance assessment.
        """)

    # ------------------------------
    # 2. Subject Pass/Fail Distribution
    # ------------------------------
    elif report == "2. Subject Pass/Fail Distribution":
        st.subheader("📊 Subject Pass/Fail Distribution")
        df_subjects = r.get_subject_pass_fail(db)  # columns: ['Subject Code', 'Subject Name', 'Semester', 'Pass Count', 'Fail Count', 'Pass %', 'Fail %']
        st.dataframe(df_subjects)

        st.markdown("""
        **Insight:**  
        Provides a clear picture of **subject-level performance per semester**, enabling targeted support for subjects 
        with higher failure rates. Administrators can plan remediation programs effectively.
        """)

    # ------------------------------
    # 3. Enrollment Trend Analysis
    # ------------------------------
    elif report == "3. Enrollment Trend Analysis":
        st.subheader("📈 Enrollment Trend Analysis")
        df_enrollment = r.get_enrollment_trend(db)  # columns: ['Semester', 'Total Enrollment', 'New Enrollees', 'Dropouts', 'Retention Rate (%)']
        st.dataframe(df_enrollment)

        st.markdown("""
        **Insight:**  
        Observe semester-to-semester enrollment trends, **track retention rates**, and identify patterns of student dropouts. 
        Helps institutions plan resource allocation and intervention strategies.
        """)

    # ------------------------------
    # 4. Incomplete Grades
    # ------------------------------
    elif report == "4. Incomplete Grades":
        st.subheader("⚠️ Incomplete Grades Report")
        df_incomplete = r.get_incomplete_grades(db)  # columns: ['Student ID', 'Name', 'Course Code', 'Course Title', 'Term', 'Grade Status']
        st.dataframe(df_incomplete)

        st.markdown("""
        **Insight:**  
        Enables the Registrar’s Office to follow up with **students and instructors** regarding incomplete or missing grades, 
        ensuring timely grade submissions.
        """)

    # ------------------------------
    # 5. Retention and Dropout Rates
    # ------------------------------
    elif report == "5. Retention and Dropout Rates":
        st.subheader("📊 Retention and Dropout Rates")
        df_retention = r.get_retention_rates(db)  # columns: ['Semester to Semester', 'Retained', 'Dropped Out', 'Retention Rate (%)']
        st.dataframe(df_retention)

        st.markdown("""
        **Insight:**  
        Measures **student persistence** across semesters and identifies retention issues early, 
        providing actionable data for academic planning and intervention programs.
        """)

    # ------------------------------
    # 6. Top Performers per Program
    # ------------------------------
    elif report == "6. Top Performers per Program":
        st.subheader("🏆 Top Performers per Program")
        df_top = r.get_top_performers(db)  # columns: ['Program', 'Semester', 'Student ID', 'Student Name', 'GPA', 'Rank']
        st.dataframe(df_top)

        st.markdown("""
        **Insight:**  
        Highlights **high-achieving students** in each program. Useful for **recognition, awards, and program benchmarking**.
        """)

    # ------------------------------
    # 7. Curriculum Progress Viewer
    # ------------------------------
    elif report == "7. Curriculum Progress Viewer":
        st.subheader("📚 Curriculum Progress Viewer")
        df_curriculum = r.get_curriculum_progress(db)  # columns: ['Subject Code', 'Subject Description', 'Lec Hours', 'Lab Hours', 'Units', 'Prerequisites']
        st.dataframe(df_curriculum)

        st.markdown("""
        **Insight:**  
        Provides a comprehensive view of curriculum structure, subject prerequisites, and credit distribution.  
        Supports **curriculum planning and academic advising** for students to track progress toward graduation.
        """)

