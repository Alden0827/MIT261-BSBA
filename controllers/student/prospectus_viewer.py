import streamlit as st
import pandas as pd
# from helpers.data_helper import get_student_subjects_grades, get_curriculum, get_students
import helpers.data_helper as dh
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd



def get_student_subjects_grades(db, StudentID=None, limit=1000):
    """
    Returns all subjects and grades for a specific student with columns:
    ["Subject Code", "Description", "Grade", "Semester", "SchoolYear"]
    """
    if StudentID is None:
        return pd.DataFrame()

    student_id = int(StudentID)

    # Fetch all grade documents for the student (all semesters)
    grade_docs = list(db.grades.findMany({"StudentID": student_id}))
    if not grade_docs:
        return pd.DataFrame()

    # Pre-fetch all semester documents to avoid repeated queries
    semester_ids = list({doc.get("SemesterID") for doc in grade_docs})
    semesters = {s["_id"]: s for s in db.semesters.find({"_id": {"$in": semester_ids}})}

    # Pre-fetch all subjects to avoid repeated queries
    all_subject_codes = set()
    for doc in grade_docs:
        all_subject_codes.update(doc.get("SubjectCodes", []))
    subjects = {s["_id"]: s for s in db.subjects.find({"_id": {"$in": list(all_subject_codes)}})}

    # Build rows
    rows = []
    for doc in grade_docs:
        sem = semesters.get(doc.get("SemesterID"))
        semester = sem["Semester"] if sem else None
        school_year = sem["SchoolYear"] if sem else None

        for code, grade in zip(doc.get("SubjectCodes", []), doc.get("Grades", [])):
            subj = subjects.get(code)
            desc = subj["Description"] if subj else None

            rows.append({
                "Subject Code": code,
                "Description": desc,
                "Grade": grade,
                "Semester": semester,
                "SchoolYear": school_year
            })

    # Apply limit if specified
    if limit:
        rows = rows[:limit]

    return pd.DataFrame(rows)

def get_students_info(db, StudentID=None):
    """
    Returns a DataFrame of students with grades including these columns:
    ['_id', 'Name', 'Course', 'YearLevel']

    Column explanations:
    _id       → Student ID
    Name      → Student’s full name
    Course    → Course enrolled
    YearLevel → Year level of the student
    """
    pipeline = [
        {"$match": {"StudentID": StudentID} if StudentID else {}},
        {"$group": {"_id": "$StudentID"}},  # unique students with grades
        {
            "$lookup": {
                "from": "students",
                "localField": "_id",
                "foreignField": "_id",
                "as": "student"
            }
        },
        {"$unwind": "$student"},
        {
            "$project": {
                "_id": "$student._id",
                "Name": "$student.Name",
                "Course": "$student.Course",
                "YearLevel": "$student.YearLevel"
            }
        },
        {"$sort": {"Name": 1}}
    ]

    cursor = db.grades.aggregate(pipeline)
    df = pd.DataFrame(list(cursor))
    
    df.attrs['column_explanations'] = {
        "_id": "Student ID",
        "Name": "Student’s full name",
        "Course": "Course enrolled",
        "YearLevel": "Year level of the student"
    }
    
    return df

def prospectus_page(db):
    r = dh.data_helper({"db": db})

    user_role = st.session_state.get("user_role", "")
    StudentID = st.session_state.get("uid")

    st.title("🧑‍🎓 Student Prospectus & GPA")

    # ---------------- ACTION BAR (TOP) ----------------
    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        if st.button("🖨️ Print Page"):
            st.markdown("<script>window.print()</script>", unsafe_allow_html=True)

    with action_col2:
        pdf_download_placeholder = st.empty()

    # ---------------- Student Selection ----------------
    if user_role == "registrar":
        # registrar can select any student
        students = get_students_info(db)   # all students
        if students.empty:
            st.warning("No students found.")
            return

        selected_student = st.selectbox("Select Student", students["Name"].tolist())
        student_row = students[students["Name"] == selected_student].iloc[0]

    else:
        # student role: only their own record
        students = get_students_info(db, StudentID=StudentID)
        if students.empty:
            st.warning("No student record found.")
            return

        student_row = students.iloc[0]

    # ---------------- Display student info ----------------
    st.write(f"**Student ID:** {student_row['_id']}")
    st.write(f"**Name:** {student_row['Name']}")
    st.write(f"**Course:** {student_row['Course']}")
    # st.write(f"**Year Level:** {student_row['YearLevel']}")

    # --- Get Curriculum and Grades ---
    student_id = student_row["_id"]
    program_code = student_row['Course']

    curriculum_df = r.get_curriculum(program_code)
    stud_grades = get_student_subjects_grades(db, StudentID=student_id)

    if curriculum_df.empty:
        st.warning(f"No curriculum found for the program: {program_code}")
        if not stud_grades.empty:
            st.subheader("Grades")
            st.dataframe(stud_grades)
        return

    # --- Merge curriculum with grades ---
    if not stud_grades.empty:
        grades_to_merge = stud_grades[['Subject Code', 'Grade', 'SchoolYear', 'Semester']].copy()
        prospectus_df = pd.merge(curriculum_df, grades_to_merge, on="Subject Code", how="left")
    else:
        prospectus_df = curriculum_df.copy()
        prospectus_df['Grade'] = np.nan
        prospectus_df['SchoolYear'] = ''
        prospectus_df['Semester'] = ''

    # --- Status Column ---
    def grade_status(grade):
        if pd.isna(grade) or grade == '' or grade == 0:
            return "-"
        elif float(grade) >= 75:
            return "Pass"
        else:
            return "Fail"

    prospectus_df["Status"] = prospectus_df["Grade"].apply(grade_status)

    # --- Styling Functions ---
    def color_status(val):
        if val == "Pass":
            return "color: green; font-weight: bold;"
        elif val == "Fail":
            return "color: red; font-weight: bold;"
        else:
            return ""

    def color_grade(val):
        if val == "-" or pd.isna(val):
            return ""
        elif float(val) >= 75:
            return "color: green;"
        else:
            return "color: red;"

    # --- Display Prospectus per Year/Semester ---
    prospectus_df.sort_values(by=['year', 'semester'], inplace=True)

    for (year, sem), group in prospectus_df.groupby(["year", "semester"]):
        st.subheader(f"📘 Year {year} / {sem} Semester")
        display_df = group[["Subject Code", "Description", "Grade", "Status", "unit", "preRequisites"]].copy()

        # Format Grade column
        display_df['Grade'] = display_df['Grade'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "-")
        display_df.rename(columns={"unit": "Units", "preRequisites": "Prerequisites"}, inplace=True)

        # --- Apply styling ---
        styled_df = display_df.style.applymap(color_status, subset=["Status"]) \
                                    .applymap(color_grade, subset=["Grade"])

        # Display in Streamlit — remove .reset_index()
        st.dataframe(styled_df)

    # --- Calculations for subjects with grades ---
    graded_subjects = prospectus_df.dropna(subset=['Grade'])

    if not graded_subjects.empty:
        # Overall GPA
        gpa = graded_subjects["Grade"].astype(float).mean()
        st.markdown(
            f"<h2 style='text-align: center; color: #2E86C1;'>Overall GPA: {gpa:.2f}</h2>",
            unsafe_allow_html=True
        )

        # GPA Trend
        st.subheader("📈 GPA Trend per Semester")
        gpa_trend = (
            graded_subjects.groupby(["SchoolYear", "Semester"])["Grade"]
            .mean()
            .reset_index()
        )
        gpa_trend["Period"] = gpa_trend["SchoolYear"].astype(str) + " / " + gpa_trend["Semester"].astype(str)
        gpa_trend.sort_values("Period", inplace=True)

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(gpa_trend["Period"], gpa_trend["Grade"], marker='o', linestyle='-')
        ax.set_ylim(50, 100)
        ax.set_xlabel("Semester")
        ax.set_ylabel("Average Grade")
        ax.set_title("GPA Trend per Semester")
        ax.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig)

        chart_buf = BytesIO()
        fig.savefig(chart_buf, format="png", bbox_inches="tight")
        chart_buf.seek(0)
    else:
        st.info("No grades available to calculate GPA or show trend.")
        gpa = None
        gpa_trend = pd.DataFrame()
        chart_buf = None


    # ---------------- PDF GENERATION ----------------
    def create_prospectus_pdf(student_row, prospectus_df, gpa, gpa_trend, chart_buf):
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=36, bottomMargin=30)
        styles = getSampleStyleSheet()
        story = []

        # Header
        story.append(Paragraph(f"Student Prospectus — {student_row['Name']}", styles["Title"]))
        story.append(Paragraph(f"Course: {student_row['Course']} &nbsp;&nbsp; Year Level: {student_row['YearLevel']}", styles["Normal"]))
        story.append(Paragraph(f"Student ID: {student_row['_id']}", styles["Normal"]))
        story.append(Spacer(1, 12))

        # Summary
        story.append(Paragraph("Prospectus Summary", styles["Heading2"]))
        total_subjects = len(prospectus_df)
        passed_subjects = (prospectus_df['Status'] == 'Pass').sum()
        failed_subjects = (prospectus_df['Status'] == 'Failed').sum()
        not_taken = total_subjects - passed_subjects - failed_subjects

        sum_data = [
            ["Overall GPA", f"{gpa:.2f}" if gpa else "—"],
            ["Total Subjects in Curriculum", total_subjects],
            ["Passed", passed_subjects],
            ["Failed", failed_subjects],
            ["Not Yet Taken", not_taken],
        ]
        t_sum = Table(sum_data, hAlign="LEFT", colWidths=[180, 200])
        t_sum.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))
        story.append(t_sum)
        story.append(Spacer(1, 14))

        # Per-Semester Tables
        for (year, sem), group in prospectus_df.groupby(["year", "semester"]):
            story.append(Paragraph(f"Year {year} / {sem} Semester", styles["Heading2"]))

            data = [["Code", "Description", "Units", "Grade", "Status"]]
            for _, r in group.iterrows():
                grade_str = f"{r['Grade']:.2f}" if pd.notna(r['Grade']) else "—"
                data.append([r["Subject Code"], r["Description"], r["unit"], grade_str, r["Status"]])

            tbl = Table(data, hAlign="LEFT", colWidths=[70, 220, 40, 50, 70])
            tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#26364a")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("ALIGN", (2, 1), (-1, -1), "CENTER"),
            ]))
            story.append(tbl)
            story.append(Spacer(1, 16))

        # GPA Trend
        if chart_buf:
            story.append(Paragraph("GPA Trend Chart", styles["Heading2"]))
            story.append(Image(chart_buf, width=400, height=180))

        doc.build(story)
        buf.seek(0)
        return buf.read()

    # --- Download Button ---
    pdf_buffer = create_prospectus_pdf(student_row, prospectus_df, gpa, gpa_trend, chart_buf)
    if pdf_buffer:
        pdf_download_placeholder.download_button(
            "📄 Download Prospectus (PDF)",
            data=pdf_buffer,
            file_name=f"prospectus_{student_row['_id']}.pdf",
            mime="application/pdf"
        )
