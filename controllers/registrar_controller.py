
import streamlit as st
from data_helper import get_student_grades_with_info
import matplotlib.pyplot as plt

def registrar_view(st, semesters, subjects):

    st.title("📚 Registrar Dashboard")

    # 3-column filters
    col1, col2, col3 = st.columns(3)
    with col1:
        sem_choice = st.selectbox("Select Semester", semesters["Semester"].tolist())
    with col2:
        subj_choice = st.selectbox("Select Subject", subjects["Subject Code"].tolist())
    with col3:
        year_choice = st.selectbox("Select School Year", semesters["SchoolYear"].unique().tolist())

    # Fetch selected rows
    sem_row = semesters[semesters["Semester"] == sem_choice].iloc[0]
    subj_row = subjects[subjects["Subject Code"] == subj_choice].iloc[0]

    st.write("You selected:", sem_choice, subj_choice, year_choice)

    # Get student grades
    df_result = get_student_grades_with_info(
        SchoolYear=year_choice,
        Semester=sem_choice,
        SubjectCode=subj_choice
    )

    # Keep Semester column for GPA trend
    df_filtered = df_result[["StudentID", "Name", "Course", "YearLevel", "Grade", "Semester"]].copy()

    if not df_filtered.empty:
        gpa = df_filtered["Grade"].mean()
        above = (df_filtered["Grade"] >= gpa).sum()
        below = (df_filtered["Grade"] < gpa).sum()

        # Summary info
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**School Year:** {sem_row['SchoolYear']}")
            st.write(f"**Subject Code:** {subj_row['Subject Code']}")
            st.write(f"**Instructor:** {subj_row['Teacher']}")
            st.write(f"**General GPA:** {gpa:.2f}")
            st.write(f"**Below GPA:** {below}")
        with col2:
            st.write(f"**Semester:** {sem_row['Semester']}")
            st.write(f"**Subject Description:** {subj_row['Description']}")
            st.write(f"**Total Enrolled:** {len(df_filtered)}")
            st.write(f"**Above GPA:** {above}")

        st.subheader("📊 Student Grades")
        st.dataframe(df_filtered.drop(columns="Semester"))  # optional: hide Semester in table

        # --- Histogram of Grades ---
        st.subheader("📈 Grade Distribution")
        fig, ax = plt.subplots()
        ax.hist(df_filtered["Grade"], bins=10, edgecolor="black")
        ax.axvline(gpa, color="red", linestyle="--", label=f"GPA {gpa:.2f}")
        ax.set_xlabel("Grade")
        ax.set_ylabel("Number of Students")
        ax.set_title("Grade Distribution Histogram")
        ax.legend()
        st.pyplot(fig)        

    else:
        st.warning("No records for this subject & semester.")