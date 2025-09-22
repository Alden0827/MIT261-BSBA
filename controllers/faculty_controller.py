import streamlit as st
from streamlit_option_menu import option_menu
# from controllers.dashboard_controller import dasboard_view
import pandas as pd
# ----------------- Main Page -----------------

def faculty_view(db,user_role):
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

        print(f' -> [{user_role}]',)
        main_menu = ''
        if user_role == 'faculty' or user_role == "registrar":

            main_menu = option_menu(
                menu_title="Faculty Menu",
                options=[
                    "Class Scheduling",
                    "Reports",
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

        elif user_role == 'teacher':

            main_menu = option_menu(
                menu_title="Faculty Menu",
                options=[
                    "Reports",
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
            

        else:
            st.warning('Access Denied')


    # Submenus
    menu = main_menu

    if main_menu == "Reports":
        with st.sidebar:
            menu = option_menu(
                menu_title="Basic Reports",
                options=[
                    "Class Grade Distribution",
                    "Student Progress Tracker",
                    "Subject Difficulty",
                    "Intervention Candidates List",
                    "Grade Submission Status",
                    "Custom Query Builder",
                    "Students Grade Analytics"
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

    # --- Routing (works for all menus) ---
    if menu == "Class Scheduling":
        from .faculty.class_scheduler_manager import class_scheduler_manager_page
        class_scheduler_manager_page(db)
    elif menu == "Class Grade Distribution":
        from .faculty.class_grade_distribution import class_grade_distribution
        class_grade_distribution(db)
    elif menu == "Student Progress Tracker":
        from .faculty.student_progress_tracker import student_progress_tracker_page
        student_progress_tracker_page(db)
    elif menu == "Subject Difficulty":
        from .faculty.subject_difficulty import subject_difficulty_page
        subject_difficulty_page(db)        
        
    elif menu == "Intervention Candidates List":        
        from .faculty.intervention_candidates import intervention_candidates_page
        intervention_candidates_page(db)
    elif menu == "Grade Submission Status":        
        from .faculty.grade_submission_status import grade_submission_status_page
        grade_submission_status_page(db)
    elif menu == "Custom Query Builder":        
        from .faculty.custom_query_builder import custom_query_builder_page
        custom_query_builder_page(db)
    elif menu == "Students Grade Analytics":
        from .faculty.students_grade_analytics import student_grade_analytics_page        
        student_grade_analytics_page(db)
        student_grade_analytics_page