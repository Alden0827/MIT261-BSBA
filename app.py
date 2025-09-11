import streamlit as st
from controllers.registrar_controller import registrar_view
from controllers.faculty_controller import faculty_view
from controllers.student_controller import student_view
from controllers.dashboard_controller import dasboard_view
from controllers.login_controller import login_view
from helpers.data_helper import get_students, get_grades, get_semesters, get_subjects
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, AutoReconnect
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

# Main app
def main():
    # ---------------- Header ----------------
    st.markdown(f"""
        <div style="background-color:#4B8BBE;padding:10px;border-radius:5px">
            <h5 style="color:white;text-align:center;">{APP_TITLE}</h5>
        </div>
    """, unsafe_allow_html=True)
    


    # ---------------- Sidebar Navigation ----------------
    st.sidebar.markdown(
        """
        <div style="text-align:center;">
            <img src="https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjvoWxGatGPpCoUDlDd_tHUcWr92COSNaEE4-1rtDQ0aplkWFjqhUBjraQHKx-3AmVB224hNeZWZzt-fTZ8ZQvSA8Wlu-zCh3xZ5FCJTwhyaBkWAm4nYRn4GaPVYT5Kxsp785Cma5prdWRW/s1600/ndmu-seal1.png"
                 style="width:80px; border-radius:50%; margin-bottom:10px;">
            <h4>BSBA Department</h4>
        </div>
        """,
        unsafe_allow_html=True
    )

    menu_options = {
        "admin": ["Student Evaludation", "Faculty", "Registrar"],
        "registrar": ["Registrar"],
        "faculty": ["Faculty"],
        "student": ["Student Evaludation"]
    }

    user_role = st.session_state["user_role"]
    if user_role in menu_options:
        menu = st.sidebar.radio(
            f"Welcome: {st.session_state['fullname']}",

            menu_options[user_role],
            key="sidebar_menu"
        )
    else:
        menu = "Dashboard"



    # ---------------- Pages ----------------
    if menu == "Dashboard":
        # try:
            
        #     dasboard_view(st)
        # except Exception as e:
        #     st.error("⚠️ Failed to load grades.")
        #     st.code(str(e))
        dasboard_view(st)
    elif menu == "Student Evaludation":
        student_view(st)
    elif menu == "Faculty":
        faculty_view(st)
    elif menu == "Registrar":
        registrar_view(st, db)




    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["user_role"] = None
        st.session_state["username"] = None
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


if st.session_state["logged_in"]:
    main()
else:
    login_view()
