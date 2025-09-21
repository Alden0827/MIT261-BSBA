import streamlit as st
from streamlit_option_menu import option_menu
from controllers.dashboard_controller import dasboard_view

def student_view(db):
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
            menu_title="Student Menu",
            options=[
                "Prospectus",
                "Performance Trend",
                "Subject Difficulty",
                "Peer Comparison",
                "Passed/Failed Summary",
            ],
            icons=[
                "book",
                "graph-up",
                "graph-down",
                "people",
                "check-circle",
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

    menu = main_menu
    # --- Routing (works for all menus) ---
    if menu == "Dashboard":
        pass
    elif menu == "Prospectus":
        from .student.prospectus_viewer import prospectus_page
        prospectus_page(db)
    elif menu == "Performance Trend":
        from .student.performance_trend import performance_trend_page
        performance_trend_page(db)
    elif menu == "Subject Difficulty":
        from .student.subject_difficulty import subject_difficulty_page
        subject_difficulty_page(db)
    elif menu == "Peer Comparison":
        from .student.peer_comparison import peer_comparison_page
        peer_comparison_page(db)
    elif menu == "Passed/Failed Summary":
        from .student.passed_failed_summary import passed_failed_summary_page
        passed_failed_summary_page(db)
