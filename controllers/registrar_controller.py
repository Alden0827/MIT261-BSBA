import streamlit as st
from streamlit_option_menu import option_menu
from controllers.dashboard_controller import dasboard_view

def registrar_view(db):
    # Sidebar Menu
    with st.sidebar:
        st.markdown(
        """
            <style>
            [data-testid="stSidebar"] {
                background-image: url('https://sms.ndmu.edu.ph/storage/carousel/1749470855_ndmu.jpg');
                background-repeat: no-repeat;       
                background-size: auto 100%;         
                background-position: center top;    
            }
            </style>
        """,
        unsafe_allow_html=True
        )

        main_menu = option_menu(
            menu_title="Registrar Menu",
            options=[
                "Dashboard",
                "Curriculum Manager",
                "Subjects",
                "Student Records",
                "Semester Control",
                # "Class Scheduling",
                "Enrollment",
                "Enrolled Students",
                "Reports",
                "Data Analysis"
            ],
            icons=[
                "bar-chart-line", "book", "book-half", "people",
                "calendar", "calendar-check", "file-earmark-text", "graph-up"
            ],
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"padding": "5px", "background-color": "#f0f2f6"},
                "icon": {"color": "#2e7bcf", "font-size": "18px"},
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#2e7bcf", "color": "white"}
            }
        )

    # Submenus
    menu = main_menu

    if main_menu == "Reports":
        with st.sidebar:
            st.markdown(
                """
                <h3 style="color:#ffffff;text-shadow:2px 2px 4px rgba(0,0,0,0.7);">
                    Reports
                </h3>
                """,
                unsafe_allow_html=True
            )

            menu = option_menu(
                menu_title="Basic Reports",
                options=[
                    "Reports",
                    "Prospectus"
                ],
                icons=["file-text", "book"],
                menu_icon="cast",
                default_index=0,
                orientation="vertical",
                styles={
                    "container": {"padding": "0px"},
                    "icon": {"color": "#2e7bcf"},
                    "nav-link": {"font-size": "14px"},
                    "nav-link-selected": {"background-color": "#2e7bcf", "color": "white"}
                }
            )

    elif main_menu == "Data Analysis":
        with st.sidebar:
            menu = option_menu(
                menu_title="Data Analysis with Visualization",
                options=[
                    "Student Performance",
                    "Teacher & Subject",
                    "Course & Curriculum",
                    "Sem & Academic Year",
                    "Student Demographic"
                ],
                icons=["bar-chart-line", "person-badge", "book-half", "calendar", "people"],
                menu_icon="cast",
                default_index=0,
                orientation="vertical",
                styles={
                    "container": {"padding": "0px"},
                    "icon": {"color": "#2e7bcf"},
                    "nav-link": {"font-size": "14px"},
                    "nav-link-selected": {"background-color": "#2e7bcf", "color": "white"}
                }
            )

    # --- Routing (works for all menus) ---
    if menu == "Dashboard":
        dasboard_view(db)
    elif menu == "Curriculum Manager":
        from .registrar.curriculum_manager import curriculum_manager_page
        curriculum_manager_page(db)
    elif menu == "Subjects":
        from .registrar.subjects_manager import subjects_manager_page
        subjects_manager_page(db)
    elif menu == "Student Records":
        from .registrar.student_records_manager import student_records_manager_page
        student_records_manager_page(db)
    elif menu == "Semester Control":
        from .registrar.semester_manager import semester_manager_page
        semester_manager_page(db)
    # elif menu == "Class Scheduling":
    #     from .registrar.class_scheduler_manager import class_scheduler_manager_page
    #     class_scheduler_manager_page(db)
    elif menu == "Enrollment":
        from .registrar.enrollment_manager import enrollment_manager_page
        enrollment_manager_page(db)
    elif menu == "Enrolled Students":
        from .registrar.enrolled_students_manager import enrolled_students_manager_page
        enrolled_students_manager_page(db)
    elif menu == "Enrollment Approvals":
        from .registrar.enrollment_approval_manager import enrollment_approval_manager_page
        enrollment_approval_manager_page(db)
    elif menu == "Student Performance":
        from .reports.student_performance_report import report_page
        report_page(db)
    elif menu == "Teacher & Subject":
        from .reports.subject_and_teacher_report import report_page
        report_page(db)
    elif menu == "Course & Curriculum":
        from .reports.course_and_curriculum_report import report_page
        report_page(db)
    elif menu == "Sem & Academic Year":
        from .reports.semester_and_academic_year_report import report_page
        report_page(db)
    elif menu == "Student Demographic":
        from .reports.student_demographics_report import report_page
        report_page(db)
    elif menu == "Prospectus":
        from .registrar.prospectus_manager import prospectus_page
        prospectus_page()
    elif menu == "Reports":
        from .reports.registrar_main_report import report_page
        report_page(db)
