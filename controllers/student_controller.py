import streamlit as st
import pandas as pd
from helpers.data_helper import get_student_subjects_grades
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
import matplotlib.pyplot as plt
from helpers.data_helper import get_students

def student_view(st):
    students = get_students()
    st.title("🧑‍🎓 Student Prospectus & GPA")

    # ---------------- ACTION BAR (TOP) ----------------
    action_col1, action_col2 = st.columns([1, 1])

    with action_col1:
        if st.button("🖨️ Print Page"):
            # trigger browser print
            st.markdown("<script>window.print()</script>", unsafe_allow_html=True)

    with action_col2:
        pdf_download_placeholder = st.empty()  # will show button later

    # ---------------- Student Selection ----------------
    selected_student = st.selectbox("Select Student", students["Name"].tolist())
    student_row = students[students["Name"] == selected_student].iloc[0]

    st.write(f"**Student ID:** {student_row['_id']}")  
    st.write(f"**Course:** {student_row['Course']}")
    st.write(f"**Year Level:** {student_row['YearLevel']}")

    # Get all grades of the student
    student_id = student_row["_id"]  
    stud_grades = get_student_subjects_grades(StudentID=student_id)

    if not stud_grades.empty:
        # Add Status column
        def grade_status(grade):
            if pd.isna(grade):
                return "INC"
            elif grade >= 75:
                return "Pass"
            else:
                return "Failed"

        stud_grades["Status"] = stud_grades["Grade"].apply(grade_status)

        # Group by SchoolYear / Semester
        for (year, sem), group in stud_grades.groupby(["SchoolYear", "Semester"]):
            st.subheader(f"📘 {year} / {sem}")
            display_df = group[["Subject Code", "Description", "Grade", "Status"]].reset_index(drop=True)
            st.dataframe(display_df)

        # Overall GPA
        gpa = stud_grades["Grade"].mean()
        st.markdown(
            f"<h2 style='text-align: center; color: #2E86C1;'>Overall GPA: {gpa:.2f}</h2>", 
            unsafe_allow_html=True
        )

        # GPA Trend
        st.subheader("📈 GPA Trend per Semester")
        gpa_trend = (
            stud_grades.groupby(["SchoolYear", "Semester"])["Grade"]
            .mean()
            .reset_index()
        )
        gpa_trend["Period"] = gpa_trend["SchoolYear"].astype(str) + " / " + gpa_trend["Semester"]

        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(gpa_trend["Period"], gpa_trend["Grade"], marker='o', linestyle='-')
        ax.set_ylim(50, 100)
        ax.set_xlabel("Semester")
        ax.set_ylabel("Average Grade")
        ax.set_title("GPA Trend per Semester")
        ax.grid(True)
        plt.xticks(rotation=45)
        st.pyplot(fig)

        # Save GPA chart to image (for embedding in PDF)
        chart_buf = BytesIO()
        fig.savefig(chart_buf, format="png", bbox_inches="tight")
        chart_buf.seek(0)

        # ---------------- PDF GENERATION ----------------
        def create_pdf(student_row, stud_grades, gpa, gpa_trend, chart_buf):
            buf = BytesIO()
            doc = SimpleDocTemplate(
                buf, pagesize=A4,
                rightMargin=30, leftMargin=30,
                topMargin=36, bottomMargin=30
            )
            styles = getSampleStyleSheet()
            story = []

            # --- Student Info Header ---
            story.append(Paragraph(f"Student Evaluation Sheet — {student_row['Name']}", styles["Title"]))
            story.append(Paragraph(f"Course: {student_row['Course']} &nbsp;&nbsp; Year Level: {student_row['YearLevel']}", styles["Normal"]))
            story.append(Paragraph(f"Student ID: {student_row['_id']}", styles["Normal"]))
            story.append(Spacer(1, 12))

            # --- Prospectus Summary ---
            story.append(Paragraph("Prospectus Summary", styles["Heading2"]))
            sum_data = [
                ["Overall GPA", f"{gpa:.2f}" if gpa else "—"],
                ["Total Subjects", len(stud_grades)],
                ["Passed", (stud_grades['Status'] == "Pass").sum()],
                ["Failed", (stud_grades['Status'] == "Failed").sum()],
                ["Incomplete", (stud_grades['Status'] == "INC").sum()],
            ]
            t_sum = Table(sum_data, hAlign="LEFT", colWidths=[180, 200])
            t_sum.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]))
            story.append(t_sum)
            story.append(Spacer(1, 14))

            # --- Per-Semester Tables ---
            for (year, sem), group in stud_grades.groupby(["SchoolYear", "Semester"]):
                sem_title = f"{year} / {sem}"
                story.append(Paragraph(sem_title, styles["Heading2"]))

                data = [["Subject Code", "Description", "Grade", "Status"]]
                for _, r in group.iterrows():
                    data.append([r["Subject Code"], r["Description"], r["Grade"], r["Status"]])

                tbl = Table(data, hAlign="LEFT", colWidths=[80, 200, 60, 80])
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#26364a")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ]))
                story.append(tbl)
                story.append(Spacer(1, 16))

            # --- Overall GPA Section ---
            story.append(Paragraph(f"Overall GPA: {gpa:.2f}", styles["Heading2"]))
            story.append(Spacer(1, 12))

            # --- GPA Trend Table ---
            if not gpa_trend.empty:
                story.append(Paragraph("GPA Trend", styles["Heading2"]))
                trend = [["Semester", "Average GPA"]] + gpa_trend[["Period", "Grade"]].values.tolist()
                t2 = Table(trend, hAlign="LEFT", colWidths=[200, 100])
                t2.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eef2ff")),
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ]))
                story.append(t2)
                story.append(Spacer(1, 14))

                # Embed GPA Chart Image
                story.append(Paragraph("GPA Trend Chart", styles["Heading2"]))
                story.append(Image(chart_buf, width=400, height=180))
                story.append(Spacer(1, 16))

            doc.build(story)
            buf.seek(0)
            return buf.read()

        # Generate PDF
        pdf_buffer = create_pdf(student_row, stud_grades, gpa, gpa_trend, chart_buf)
        pdf_download_placeholder.download_button(
            "📄 Download PDF", 
            data=pdf_buffer, 
            file_name=f"prospectus_{student_row['_id']}.pdf", 
            mime="application/pdf"
        )
