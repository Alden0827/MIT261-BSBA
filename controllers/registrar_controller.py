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
            "📈 Analysis & Visualization",
        ]
    )

    # Default value for menu
    menu = main_menu  

    # Show analysis submenu ONLY if "📈 Analysis & Visualization" is selected
    if main_menu == "📈 Analysis & Visualization":
        analysis_menu = st.sidebar.radio(
            "📊 Select Analysis",
            [
                "📖 Prospectus", 
                "📊 Student Performance",
                "👩‍🏫 Teacher & Subject Analysis",
                "📚 Course & Curriculum Insight",
                "📅 Sem & Academic Year Analysis",
                "👥 Student Demographic Analysis"
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
    elif menu == "🧾 Enrollment Approvals":
        from .registrar.enrollment_approval_manager import enrollment_approval_manager_page
        enrollment_approval_manager_page(st,db)
    elif menu == "📊 Student Performance":
        from .reports.student_performance_report import report_page
        report_page(st,db)
    elif menu == "👩‍🏫 Teacher & Subject Analysis":
        from .reports.subject_and_teacher_report import report_page
        report_page(st,db)
    elif menu == "📚 Course & Curriculum Insight":
        from .reports.course_and_curriculum_report import report_page
        report_page(st,db)
    elif menu == "📅 Sem & Academic Year Analysis":
        from .reports.semester_and_cademic_year_report import report_page
        report_page(st,db)
    elif menu == "👥 Student Demographic Analysis":
        from .reports.student_demographics_report import report_page
        report_page(st,db)
