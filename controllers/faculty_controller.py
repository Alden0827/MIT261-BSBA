from helpers.data_helper import get_instructor_subjects
import pandas as pd
import streamlit as st

def faculty_view():

    st.title("👨‍🏫 Faculty & Subjects")

    # Get all unique teachers from the database for the selectbox
    all_teachers = get_instructor_subjects(limit=None)["Teacher"].unique()
    selected_teacher = st.selectbox("Select Faculty", all_teachers)

    # Fetch subjects handled by the selected teacher using the new function
    subj_by_teacher = get_instructor_subjects(selected_teacher)

    st.write(f"**Subjects handled by {selected_teacher}:**")
    st.table(subj_by_teacher[["Subject Code", "Description", "Units"]])