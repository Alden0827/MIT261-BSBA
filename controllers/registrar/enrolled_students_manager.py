import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts
from helpers.data_helper import get_students, get_school_years, get_semester_names, get_courses, get_grades, get_semesters

def enrolled_students_manager_page(db):
    st.subheader("🎓 Enrolled Students")

    # --- Filters ---
    school_years = ["All"] + get_school_years()
    semesters = ["All"] + get_semester_names()
    courses = ["All"] + get_courses()

    col1, col2, col3 = st.columns(3)
    with col1:
        selected_year = st.selectbox("Filter by Year", school_years)
    with col2:
        selected_semester = st.selectbox("Filter by Semester", semesters)
    with col3:
        selected_course = st.selectbox("Filter by Course", courses)

    # --- Fetch data ---
    with st.spinner("Loading student list..."):
        students_df = get_students()
        grades_df = get_grades()
        semesters_df = get_semesters()

    # --- Filtering logic ---
    filtered_students = students_df.copy()

    # Merge grades and semesters to get semester info for each student enrollment
    grades_with_semester_info = pd.merge(grades_df, semesters_df, left_on='SemesterID', right_on='_id', how='left')

    # Filter by Year
    if selected_year != "All":
        student_ids_in_year = grades_with_semester_info[grades_with_semester_info['SchoolYear'] == selected_year]['StudentID'].unique()
        filtered_students = filtered_students[filtered_students['_id'].isin(student_ids_in_year)]

    # Filter by Semester
    if selected_semester != "All":
        student_ids_in_semester = grades_with_semester_info[grades_with_semester_info['Semester'] == selected_semester]['StudentID'].unique()
        filtered_students = filtered_students[filtered_students['_id'].isin(student_ids_in_semester)]

    # Filter by Course
    if selected_course != "All":
        filtered_students = filtered_students[filtered_students["Course"] == selected_course]

    # --- Summary and Charts ---
    if filtered_students.empty:
        st.info("No enrolled students match the selected filters.")
    else:
        st.markdown("---")
        st.subheader("Summary & Visualizations")

        # Metrics
        col1, col2 = st.columns(2)
        col1.metric("Total Enrolled Students", len(filtered_students))
        col2.metric("Number of Courses", filtered_students['Course'].nunique())

        # Charts
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            course_counts = filtered_students['Course'].value_counts().reset_index()
            course_counts.columns = ['course', 'count']

            bar_options = {
                "title": {"text": "Enrollment by Course"},
                "tooltip": {},
                "xAxis": {
                    "type": 'category',
                    "data": course_counts['course'].tolist()
                },
                "yAxis": {"type": 'value'},
                "series": [{"data": course_counts['count'].tolist(), "type": "bar"}]
            }
            st_echarts(options=bar_options, height="320px")

        with chart_col2:
            year_level_counts = filtered_students['YearLevel'].value_counts().sort_index()
            pie_data = [{"value": v, "name": str(k)} for k, v in year_level_counts.items()]

            pie_options = {
                "title": {"text": "Enrollment by Year Level", "left": "center"},
                "tooltip": {"trigger": "item", "formatter": '{a} <br/>{b} : {c} ({d}%)'},
                "legend": {"orient": "vertical", "left": "left", "data": [str(k) for k in year_level_counts.keys()]},
                "series": [
                    {
                        "name": "Year Level",
                        "type": "pie",
                        "radius": "55%",
                        "center": ['50%', '60%'],
                        "data": pie_data,
                    }
                ],
            }
            st_echarts(options=pie_options, height="320px")

        st.markdown("---")
        st.subheader("Enrolled Students List")
        # --- Table Header ---
        header_cols = st.columns([1, 3, 2, 1, 2])
        header_cols[0].markdown("**ID**")
        header_cols[1].markdown("**Name**")
        header_cols[2].markdown("**Course**")
        header_cols[3].markdown("**Year**")
        header_cols[4].markdown("**Actions**")
        st.markdown("---")

        # Get SemesterID for discard action
        semester_id = None
        if selected_year != "All" and selected_semester != "All":
            semester_id_series = semesters_df.loc[
                (semesters_df["SchoolYear"] == selected_year) & (semesters_df["Semester"] == selected_semester),
                "_id"
            ]
            if not semester_id_series.empty:
                semester_id = semester_id_series.iloc[0]

        for index, student in filtered_students.iterrows():
            student_id = student["_id"]
            row = st.columns([1, 3, 2, 1, 2])
            row[0].write(student_id)
            row[1].write(student.get("Name", "N/A"))
            row[2].write(student.get("Course", "N/A"))
            row[3].write(student.get("YearLevel", "N/A"))

            with row[4]:
                if semester_id:
                    with st.expander("Discard"):
                        st.warning(f"This will discard the student's enrollment for {selected_semester} {selected_year}.")
                        if st.button("Confirm Discard", key=f"confirm_discard_{student_id}"):
                            db.grades.delete_one({"StudentID": student_id, "SemesterID": semester_id})
                            st.experimental_rerun()
                else:
                    st.caption("Select a semester to enable discard.")

        # --- Export Buttons ---
        st.markdown("---")
        st.subheader("Export Data")
        export_col1, export_col2 = st.columns(2)

        with export_col1:
            from fpdf import FPDF
            def dataframe_to_pdf(df, title="Enrolled Students"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)
                pdf.cell(0, 10, title, 0, 1, 'C')
                pdf.ln(10)
                pdf.set_font("Arial", 'B', 10)
                col_widths = {col: (len(col) + 5) * 2.5 for col in df.columns}
                for col in df.columns:
                    pdf.cell(col_widths[col], 10, col, 1, 0, 'C')
                pdf.ln()
                pdf.set_font("Arial", '', 10)
                for index, row in df.iterrows():
                    for col in df.columns:
                        cell_text = str(row[col])
                        pdf.cell(col_widths[col], 10, cell_text, 1, 0)
                    pdf.ln()
                return pdf.output(dest='S').encode('latin-1')

            pdf_bytes = dataframe_to_pdf(filtered_students)
            export_col1.download_button(
                label="Print to PDF",
                data=pdf_bytes,
                file_name="enrolled_students.pdf",
                mime="application/pdf",
            )

        with export_col2:
            markdown_data = filtered_students.to_markdown(index=False)
            export_col2.download_button(
                label="Export to Markdown",
                data=markdown_data,
                file_name="enrolled_students.md",
                mime="text/markdown",
            )
