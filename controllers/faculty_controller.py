import helpers.data_helper
import pandas as pd
import streamlit as st
import helpers.data_helper as dh

def faculty_view(db):

    st.title("👨‍🏫 Faculty & Subjects")
    r = dh.data_helper({"db": db})
    # Get all unique teachers from the database for the selectbox
    all_teachers = r.get_instructor_subjects(limit=None)["Teacher"].unique()
    selected_teacher = st.selectbox("Select Faculty", all_teachers)

    # Fetch subjects handled by the selected teacher using the new function
    subj_by_teacher = r.get_instructor_subjects(selected_teacher)

    st.write(f"**Subjects handled by {selected_teacher}:**")
    st.table(subj_by_teacher[["Subject Code", "Description", "Units"]])