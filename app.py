import streamlit as st
from data_helper import get_students, get_grades, get_semesters, get_subjects
from registrar_controller import registrar_view
from faculty_controller import faculty_view
from student_controller import student_view
from dashboard_controller import dasboard_view

st.set_page_config(page_title="University Dashboard", layout="wide")

# ---------------- Header ----------------
st.markdown("""
    <div style="background-color:#4B8BBE;padding:10px;border-radius:5px">
        <h2 style="color:white;text-align:center;">🏫 University Dashboard</h2>
    </div>
""", unsafe_allow_html=True)

# Load data
students = get_students()
semesters = get_semesters()
subjects = get_subjects()

# Sidebar Navigation
menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Student Evaludation", "Faculty", "Registrar"],
    key="sidebar_menu"  # unique key
)

# ---------------- Pages ----------------
if menu == "Dashboard":
    grades = get_grades()
    dasboard_view(st, subjects, students, grades, semesters)
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
