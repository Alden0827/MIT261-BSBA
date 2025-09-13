import streamlit as st
from streamlit_option_menu import option_menu
from controllers.registrar_controller import registrar_view
from controllers.faculty_controller import faculty_view
from controllers.student_controller import student_view
from controllers.dashboard_controller import dasboard_view
from controllers.login_controller import login_view
from controllers.admin_controller import admin_view
from pymongo import MongoClient
from config.settings import APP_TITLE, DEFAULT_PAGE_TITLE, MONGODB_URI

st.set_page_config(page_title=DEFAULT_PAGE_TITLE, layout="wide")

# Database connection
client = MongoClient(MONGODB_URI)
db = client["mit261"]

# Initialize session state
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
    st.session_state["user_role"] = None
    st.session_state["username"] = None
    st.session_state["fullname"] = ""

# Main app
def main():
    # ---------------- Header ----------------
    st.markdown(f"""
        <div style="background-color:#4B8BBE;padding:10px;border-radius:5px;margin-bottom:10px">
            <h5 style="color:white;text-align:center;">{APP_TITLE}</h5>
        </div>
    """, unsafe_allow_html=True)

    # ---------------- Sidebar ----------------
    with st.sidebar:
        st.markdown(
            """
                <div style="text-align:center; margin-bottom:10px;">
                    <img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjvoWxGatGPpCoUDlDd_tHUcWr92COSNaEE4-1rtDQ0aplkWFjqhUBjraQHKx-3AmVB224hNeZWZzt-fTZ8ZQvSA8Wlu-zCh3xZ5FCJTwhyaBkWAm4nYRn4GaPVYT5Kxsp785Cma5prdWRW/s1600/ndmu-seal1.png"
                         style="width:80px; border-radius:50%; margin-bottom:10px;">
                    <div style="
                        display:inline-block;
                        background-color: rgba(0, 0, 0, 0.5);  /* semi-transparent black */
                        color: #ffffff;                        /* white text */
                        padding: 6px 12px;
                        border-radius: 6px;
                        text-shadow: 1px 1px 3px rgba(0,0,0,0.7);
                        font-size: 18px;
                        font-weight: bold;
                    ">
                        BSBA Department
                    </div>
                </div>
            """,
            unsafe_allow_html=True
        )

        # Role-based menu
        user_role = st.session_state["user_role"]
        menu_options = {
            "admin": ["Student Evaluation", "Faculty", "Registrar", "Admin"],
            "registrar": ["Registrar"],
            "faculty": ["Faculty"],
            "student": ["Student Evaluation"]
        }

        # Combine menu + Logout
        main_menu = menu_options.get(user_role, ["Dashboard"])
        full_menu = main_menu + ["Logout"]

        # Icons
        main_icons = ["bar-chart-line", "person-badge", "book", "gear"][:len(main_menu)]
        full_icons = main_icons + ["box-arrow-right"]

        # Sidebar option menu
        menu = option_menu(
            menu_title=f"Welcome, {st.session_state['fullname']}",
            options=full_menu,
            icons=full_icons,
            menu_icon="cast",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"padding": "5px", "background-color": "#f0f2f6"},
                "icon": {"color": "#2e7bcf", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#d9534f", "color": "white"}
            }
        )

    # ---------------- Pages ----------------
    if menu == "Dashboard":
        dasboard_view(st)
    elif menu == "Student Evaluation":
        student_view(st)
    elif menu == "Faculty":
        faculty_view(st)
    elif menu == "Registrar":
        registrar_view(st, db)
    elif menu == "Admin":
        admin_view(st, db)
    elif menu == "Logout":
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.session_state["username"] = None
        st.session_state["fullname"] = ""
        st.rerun()

    # ---------------- Footer ----------------
    st.markdown("""
        <div style="
            width: 100%;
            background-color:#4B8BBE;
            padding:10px 0;
            text-align:center;
            position: relative;
            bottom: 0;
        ">
            <p style="color:white;margin:0;">© 2025 University Dashboard | Developed by Alden A. Quiñones</p>
        </div>
    """, unsafe_allow_html=True)


# ---------------- App Execution ----------------
if st.session_state["logged_in"]:
    main()
else:
    login_view()
