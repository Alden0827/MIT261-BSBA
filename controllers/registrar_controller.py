import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from controllers.dashboard_controller import dasboard_view

def registrar_view(st, db):
    # Sidebar Menu
    main_menu = st.sidebar.radio(
        "Registrar Menu",
        [
            "📊 Dashboard",
            "📚 Curriculum Manager",
            "📘 Subjects",
            "🧑‍🎓 Student Records",
            "🗓️ Semester Control",
            "🗂️ Class Scheduling",
            "📜 Enrollment",
            "📈 Reports",
        ]
    )

    # Default value for menu
    menu = main_menu  

    # Show analysis submenu ONLY if "📈 Analysis & Visualization" is selected
    if main_menu == "📈 Reports":
        analysis_menu = st.sidebar.radio(
            "📊 Analysis & Visualization",
            [
                "📖 Prospectus", 
                "📊 Student Performance",
                "👩‍🏫 Teacher & Subject",
                "📚 Course & Curriculum",
                "📅 Sem & Academic Year",
                "👥 Student Demographic"
            ]
        )
        menu = analysis_menu

    if menu == "📊 Dashboard":
        dasboard_view(st)
    elif menu == "📚 Curriculum Manager":
        from .registrar.curriculum_manager import curriculum_manager_page 
        curriculum_manager_page(st,db)
    elif menu == "📖 Prospectus":
        from .registrar.prospectus_manager import prospectus_page 
        prospectus_page(st)
    elif menu == "📘 Subjects":
        from .registrar.subjects_manager import subjects_manager_page
        subjects_manager_page(st,db)
    elif menu == "🧑‍🎓 Student Records":
        from .registrar.student_records_manager import student_records_manager_page
        student_records_manager_page(st,db)
    elif menu == "🗓️ Semester Control":
        from .registrar.semester_manager import semester_manager_page 
        semester_manager_page(st,db)
    elif menu == "🗂️ Class Scheduling":
        from .registrar.class_scheduler_manager import class_scheduler_manager_page
        class_scheduler_manager_page(st,db)
    elif menu == "📜 Enrollment":
        from .registrar.enrollment_manager import enrollment_manager_page
        enrollment_manager_page(st,db)
    elif menu == "🧾 Enrollment Approvals":
        from .registrar.enrollment_approval_manager import enrollment_approval_manager_page
        enrollment_approval_manager_page(st,db)
    elif menu == "📊 Student Performance":
        student_performance_menu = st.sidebar.radio(
            "Student Performance Reports",
            [
                "Top Performers",
                "Failing Students",
                "Students with Grade Improvement",
                "Distribution of Grades",
            ]
        )
        if student_performance_menu == "Top Performers":
            from .reports.student_performance_report import display_top_performers
            display_top_performers(st, db)
        elif student_performance_menu == "Failing Students":
            from .reports.student_performance_report import display_failing_students
            display_failing_students(st, db)
        elif student_performance_menu == "Students with Grade Improvement":
            from .reports.student_performance_report import display_students_with_grade_improvement
            display_students_with_grade_improvement(st, db)
        elif student_performance_menu == "Distribution of Grades":
            from .reports.student_performance_report import display_distribution_of_grades
            display_distribution_of_grades(st, db)
    elif menu == "👩‍🏫 Teacher & Subject":
        teacher_subject_menu = st.sidebar.radio(
            "Teacher & Subject Reports",
            [
                "Hardest Subject",
                "Easiest Subjects",
                "Average Grades per Teacher",
                "Teachers with High Failures",
            ]
        )
        if teacher_subject_menu == "Hardest Subject":
            from .reports.subject_and_teacher_report import display_hardest_subject
            display_hardest_subject(st, db)
        elif teacher_subject_menu == "Easiest Subjects":
            from .reports.subject_and_teacher_report import display_easiest_subjects
            display_easiest_subjects(st, db)
        elif teacher_subject_menu == "Average Grades per Teacher":
            from .reports.subject_and_teacher_report import display_average_grades_per_teacher
            display_average_grades_per_teacher(st, db)
        elif teacher_subject_menu == "Teachers with High Failures":
            from .reports.subject_and_teacher_report import display_teachers_with_high_failures
            display_teachers_with_high_failures(st, db)
    elif menu == "📚 Course & Curriculum":
        course_curriculum_menu = st.sidebar.radio(
            "Course & Curriculum Reports",
            [
                "Grade Trend per Course",
                "Subject Load Intensity",
                "GE vs Major Subjects Performance",
            ]
        )
        if course_curriculum_menu == "Grade Trend per Course":
            from .reports.course_and_curriculum_report import display_grade_trend_per_course
            display_grade_trend_per_course(st, db)
        elif course_curriculum_menu == "Subject Load Intensity":
            from .reports.course_and_curriculum_report import display_subject_load_intensity
            display_subject_load_intensity(st, db)
        elif course_curriculum_menu == "GE vs Major Subjects Performance":
            from .reports.course_and_curriculum_report import display_ge_vs_major_subjects_performance
            display_ge_vs_major_subjects_performance(st, db)
    elif menu == "📅 Sem & Academic Year":
        from .reports.semester_and_cademic_year_report import report_page
        report_page(st,db)
    elif menu == "👥 Student Demographic":
        from .reports.student_demographics_report import report_page
        report_page(st,db)
