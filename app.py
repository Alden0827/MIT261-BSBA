import streamlit as st
from controllers.registrar_controller import registrar_view
from controllers.faculty_controller import faculty_view
from controllers.student_controller import student_view
from controllers.dashboard_controller import dasboard_view
from helpers.data_helper import get_students, get_grades, get_semesters, get_subjects
from pymongo.errors import ServerSelectionTimeoutError, AutoReconnect
from config.constants import APP_TITLE, DEFAULT_PAGE_TITLE

st.set_page_config(page_title=DEFAULT_PAGE_TITLE, layout="wide")



# ---------------- Header ----------------
st.markdown(f"""
    <div style="background-color:#4B8BBE;padding:10px;border-radius:5px">
        <h2 style="color:white;text-align:center;">{APP_TITLE}</h2>
    </div>
""", unsafe_allow_html=True)

# ---------------- Load data safely ----------------
students, semesters, subjects = None, None, None

try:
    students = get_students()
    semesters = get_semesters()
    subjects = get_subjects()
except (ServerSelectionTimeoutError, AutoReconnect) as e:
    st.error("❌ Could not connect to MongoDB. Please check your connection.")
    st.code(str(e))
    st.stop()
except Exception as e:
    st.error("⚠️ Unexpected error while loading data.")
    st.code(str(e))
    st.stop()

# ---------------- Sidebar Navigation ----------------
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Student Evaludation", "Faculty", "Registrar"],
    key="sidebar_menu"
)

# ---------------- Pages ----------------
if menu == "Dashboard":
    try:
        grades = get_grades()
        dasboard_view(st, subjects, students, grades, semesters)
    except Exception as e:
        st.error("⚠️ Failed to load grades.")
        st.code(str(e))
elif menu == "Student Evaludation":
    student_view(st, students)
elif menu == "Faculty":
    faculty_view(st)
elif menu == "Registrar":
    registrar_view(st, semesters, subjects)

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
