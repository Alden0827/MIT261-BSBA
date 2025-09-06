import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from controllers.dashboard_controller import dasboard_view

def registrar_view(st, db):
    # st.title("🎓 Curriculum Manager")

    # Sidebar Menu
    menu = st.sidebar.radio(
        "Registrar Menu",
        [
            "📊 Dashboard",
            "📚 Curriculum Manager",
            "📚 Prospectus",
            "🏫 Subjects",
            "🧑‍ Student Records",
            "🗓 Semester Control",
            "📑 Class Scheduling",
            # "📝 Grade Management",
            "📈 Reports"
        ]
    )

    # ---------------------------
    # 1️⃣ Curriculum Manager
    # ---------------------------
    if menu == "📊 Dashboard":
        dasboard_view(st)

    # ---------------------------
    # 1️⃣ Curriculum Manager
    # ---------------------------
    elif menu == "📚 Curriculum Manager":
        from .registrar.curriculum_manager import curriculum_manager_page 
        curriculum_manager_page(st,db)

    # ---------------------------
    # 1️⃣ Prospectus Manager
    # ---------------------------
    elif menu == "📚 Prospectus":
        from .registrar.prospectus_manager import prospectus_page 
        prospectus_page(st)

    # ---------------------------
    # 🏫 Subjects
    # ---------------------------
    elif menu == "🏫 Subjects":
        from .registrar.subjects_manager import subjects_manager_page
        subjects_manager_page(st,db)

    # ---------------------------
    # 🧑‍🎓 Student Records
    # ---------------------------
    elif menu == "🧑‍ Student Records":
        from .registrar.student_records_manager import student_records_manager_page
        student_records_manager_page(st,db)

    # ---------------------------
    # 2️⃣ Semester Control
    # ---------------------------
    elif menu == "🗓 Semester Control":
        from .registrar.semester_manager import semester_manager_page 
        semester_manager_page(st,db)

    # ---------------------------
    # 3️⃣ Class Scheduling
    # ---------------------------
    elif menu == "📑 Class Scheduling":
        from .registrar.class_scheduler_manager import class_scheduler_manager_page
        class_scheduler_manager_page(st,db)

    # ---------------------------
    # 4️⃣ Enrollment Approvals
    # ---------------------------
    elif menu == "🧑‍ Enrollment Approvals":
        from .registrar.enrollment_approval_manager import enrollment_approval_manager_page
        enrollment_approval_manager_page(st,db)

    # ---------------------------
    # 5️⃣ Grade Management
    # ---------------------------
    elif menu == "📝 Grade Management":
        from grade_manager import grade_manager_page
        grade_manager_page(st,db)

    # ---------------------------
    # 6️⃣ Reports
    # ---------------------------
    elif menu == "📈 Reports":
        from .registrar.report_manager import report_manager_page
        report_manager_page(st,db)