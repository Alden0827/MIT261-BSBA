import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import os
import pickle
import time
from helpers.data_helper import get_students, get_grades, get_semesters, get_subjects

CACHE_FILE = "./cache/dashboard_cache.pkl"
CACHE_TTL = 3600  # 1 hour in seconds

def load_or_cache_data(subjects, students, grades, semesters):
    """
    Load cached data from pickle if it exists and is recent.
    Otherwise, cache the current data to pickle.
    """
    if os.path.exists(CACHE_FILE):
        cache_age = time.time() - os.path.getmtime(CACHE_FILE)
        if cache_age < CACHE_TTL:
            with open(CACHE_FILE, "rb") as f:
                return pickle.load(f)

    # Cache does not exist or is expired, save current data
    data = (subjects, students, grades, semesters)
    with open(CACHE_FILE, "wb") as f:
        pickle.dump(data, f)
    return data

def dasboard_view(st):
    # Load cached data
    grades = get_grades()
    students = get_students()
    semesters = get_semesters()
    subjects = get_subjects()
    # subjects, students, grades, semesters = load_or_cache_data(subjects, students, grades, semesters)

    st.title("🎓 University Dashboard")

    # KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", len(students))
    col2.metric("Faculty", subjects["Teacher"].nunique())
    col3.metric("Courses", subjects["Description"].nunique())
    col4.metric("Enrollments", len(grades))

    st.markdown("---")

    # ---------------- Charts Row 1 ----------------
    row1_col1, row1_col2 = st.columns(2)

    # Students per Course
    with row1_col1:
        st.subheader("📊 Students per Course")
        students_per_course = students.groupby("Course")["_id"].count().reset_index()
        students_per_course.rename(columns={"_id": "Count"}, inplace=True)

        fig1, ax1 = plt.subplots(figsize=(6, 4))
        ax1.bar(students_per_course["Course"], students_per_course["Count"], color="skyblue")
        ax1.set_xlabel("Course")
        ax1.set_ylabel("Number of Students")
        ax1.set_title("Students per Course")
        ax1.set_xticklabels(students_per_course["Course"], rotation=45, ha="right")
        for i, v in enumerate(students_per_course["Count"]):
            ax1.text(i, v + 0.5, str(v), ha="center")
        st.pyplot(fig1)

    # Grade Distribution
    with row1_col2:
        st.subheader("📊 Grade Distribution")
        all_grades_list = [g for row in grades["Grades"] for g in row]
        df_grades_dist = pd.DataFrame({"Grade": all_grades_list})

        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.hist(df_grades_dist["Grade"], bins=10, color="salmon", edgecolor="black")
        ax3.set_xlabel("Grade")
        ax3.set_ylabel("Number of Students")
        ax3.set_title("Grade Distribution")
        st.pyplot(fig3)

    st.markdown("---")

    # ---------------- Charts Row 2 ----------------
    st.subheader("📈 Average GPA per Semester")

    # Flatten grades with semester info
    all_grades = []
    for idx, row in grades.iterrows():
        for g, sem_id in zip(
            row["Grades"],
            row["SemesterID"] if isinstance(row["SemesterID"], list) else [row["SemesterID"]] * len(row["Grades"])
        ):
            all_grades.append({"Grade": g, "SemesterID": sem_id})
    df_grades = pd.DataFrame(all_grades)

    # Merge with semesters to get semester names and school year
    df_grades = df_grades.merge(semesters, left_on="SemesterID", right_on="_id", how="left")

    # Create a combined label for semester + school year
    df_grades["SemesterLabel"] = df_grades["Semester"].astype(str) + " " + df_grades["SchoolYear"].astype(str)

    # Calculate average GPA per semester label
    gpa_per_semester = df_grades.groupby("SemesterLabel")["Grade"].mean().reset_index()

    # Plot GPA trend
    fig2, ax2 = plt.subplots(figsize=(12, 4))
    ax2.plot(gpa_per_semester["SemesterLabel"], gpa_per_semester["Grade"], marker="o", color="darkorange")
    ax2.set_xlabel("Semester & School Year")
    ax2.set_ylabel("Average GPA")
    ax2.set_title("Average GPA Trend by Semester")
    ax2.set_ylim(50, 100)
    ax2.set_xticklabels(gpa_per_semester["SemesterLabel"], rotation=45, ha="right")
    ax2.grid(True)
    st.pyplot(fig2)
