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
        if user_role == 'faculty':

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
                    "Custom Query Builder"
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
        from .faculty.teacher_reports import class_grade_distribution
        from helpers.data_helper import data_helper

        dh = data_helper({"db": db})

        # Get data for filters
        semesters = dh.get_semester_names()
        school_years = dh.get_school_years()

        teacher_name = None

        # If the user is a teacher, default to their name.
        # Otherwise, show a dropdown to select a faculty member.
        if st.session_state["user_role"] == "teacher":
            teacher_name = st.session_state["fullname"]
        else:
            teachers_df = dh.get_instructor_subjects()
            teacher_names = teachers_df['Teacher'].unique()
            teacher_name = st.selectbox("Select Faculty Name", teacher_names)

        # Common filters for semester and school year
        semester = st.selectbox("Select Semester", semesters)
        school_year = st.selectbox("Select School Year", school_years)

        # Display the report if a teacher is selected
        if teacher_name:
            class_grade_distribution(db, teacher_name, semester, school_year)
        else:
            st.warning("Please select a faculty member to view the report.")

    elif menu == "Student Progress Tracker":
        from .faculty.student_progress_tracker import student_progress_tracker_page
        student_progress_tracker_page(db)
    elif menu == "Subject Difficulty":        
        pass
    elif menu == "Intervention Candidates List":        
        pass
    elif menu == "Grade Submission Status":        
        pass
    elif menu == "Custom Query Builder":        
        pass
    elif menu == "Intervention Candidates List":        
        pass
