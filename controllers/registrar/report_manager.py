import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

# --- Report Display Functions ---

def display_enrollment_summary(db):
    st.subheader("Enrollment Summary")

    # Fetch data
    total_students = db.students.count_documents({})
    enrolled_students_cursor = db.enrollments.find({"status": "Enrolled"})
    enrolled_students_list = list(enrolled_students_cursor)
    enrolled_count = len(enrolled_students_list)
    total_classes = db.classSchedule.count_documents({})

    # Display metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Students", total_students)
    col2.metric("Currently Enrolled", enrolled_count)
    col3.metric("Total Classes", total_classes)

    st.markdown("---")

    # Display list of enrolled students
    st.subheader("Enrolled Students")
    student_data = []
    for enrollment in enrolled_students_list:
        student = db.students.find_one({"_id": enrollment["studentId"]})
        if student:
            student_data.append({
                "Name": student.get("Name", "N/A"),
                "Course": student.get("Course", "N/A"),
                "Year Level": student.get("YearLevel", "N/A"),
            })

    if student_data:
        enrolled_df = pd.DataFrame(student_data)
        st.dataframe(enrolled_df)
    else:
        st.write("No students are currently enrolled.")

def get_letter_grade(score):
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    else:
        return 'F'

def display_grade_distribution(db):
    st.subheader("Grade Distribution Report")

    # Fetch all grades from enrollments
    all_enrollments = list(db.enrollments.find({"grade": {"$ne": None}}))

    if not all_enrollments:
        st.write("No grades available to generate a distribution report.")
        return

    grades = [enrollment['grade'] for enrollment in all_enrollments]
    letter_grades = [get_letter_grade(score) for score in grades]

    grade_counts = pd.Series(letter_grades).value_counts().sort_index()

    # Display bar chart
    st.markdown("### Grade Distribution")
    fig, ax = plt.subplots()
    grade_counts.plot(kind='bar', ax=ax)
    ax.set_title('Distribution of Grades')
    ax.set_xlabel('Letter Grade')
    ax.set_ylabel('Number of Students')
    st.pyplot(fig)

    # Display table of all grades
    st.markdown("### All Student Grades")
    grade_data = []
    for enrollment in all_enrollments:
        student = db.students.find_one({"_id": enrollment["studentId"]})
        if student:
            grade_data.append({
                "Student Name": student.get("Name", "N/A"),
                "Grade": enrollment.get("grade", "N/A"),
                "Letter Grade": get_letter_grade(enrollment.get("grade", 0))
            })

    if grade_data:
        grades_df = pd.DataFrame(grade_data)
        st.dataframe(grades_df)

def display_faculty_workload(db):
    st.subheader("Faculty Workload Report")

    # Aggregate pipeline to get workload
    pipeline = [
        {
            "$lookup": {
                "from": "enrollments",
                "localField": "_id",
                "foreignField": "classOfferingId",
                "as": "enrolled_students"
            }
        },
        {
            "$lookup": {
                "from": "faculty",
                "localField": "facultyId",
                "foreignField": "_id",
                "as": "faculty_info"
            }
        },
        {
            "$unwind": "$faculty_info"
        },
        {
            "$lookup": {
                "from": "subjects",
                "localField": "subjectId",
                "foreignField": "_id",
                "as": "subject_info"
            }
        },
        {
            "$unwind": "$subject_info"
        },
        {
            "$project": {
                "faculty_name": "$faculty_info.facultyName",
                "subject_name": "$subject_info.Description",
                "student_count": {"$size": "$enrolled_students"}
            }
        },
        {
            "$group": {
                "_id": "$faculty_name",
                "total_students": {"$sum": "$student_count"},
                "subjects_taught": {"$push": "$subject_name"}
            }
        }
    ]

    workload_data = list(db.classSchedule.aggregate(pipeline))

    if not workload_data:
        st.write("No faculty workload data available.")
        return

    # Display data in a more structured way
    for faculty in workload_data:
        st.markdown(f"#### {faculty['_id']}")
        col1, col2 = st.columns(2)
        col1.metric("Total Students", faculty['total_students'])
        col2.metric("Classes Taught", len(faculty['subjects_taught']))

        with st.expander("View Taught Subjects"):
            for subject in faculty['subjects_taught']:
                st.write(f"- {subject}")
        st.markdown("---")

def display_class_schedule(db):
    st.subheader("Class Schedule Report")

    pipeline = [
        {"$lookup": {"from": "subjects", "localField": "subjectId", "foreignField": "_id", "as": "subject_info"}},
        {"$unwind": "$subject_info"},
        {"$lookup": {"from": "faculty", "localField": "facultyId", "foreignField": "_id", "as": "faculty_info"}},
        {"$unwind": "$faculty_info"},
        {"$project": {
            "Subject": "$subject_info.Description",
            "Section": "$section",
            "Faculty": "$faculty_info.facultyName",
            "Schedule": "$schedule"
        }}
    ]
    schedule_data = list(db.classSchedule.aggregate(pipeline))

    if not schedule_data:
        st.write("No class schedule data available.")
        return

    schedule_df = pd.json_normalize(schedule_data, 'Schedule', ['Subject', 'Section', 'Faculty'])

    # Reordering and renaming columns for better presentation
    if not schedule_df.empty:
        schedule_df = schedule_df[['Subject', 'Section', 'Faculty', 'day', 'time', 'room']]
        schedule_df.rename(columns={'day': 'Day', 'time': 'Time', 'room': 'Room'}, inplace=True)
        st.dataframe(schedule_df)
    else:
        st.write("No schedule entries found.")

# --- PDF Generation Functions ---

class PDF(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4', title=''):
        super().__init__(orientation, unit, format)
        self.title = title

    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_enrollment_summary_pdf(db):
    pdf = PDF('P', 'mm', 'A4', title='Enrollment Summary Report')
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Summary Metrics
    total_students = db.students.count_documents({})
    enrolled_students_cursor = db.enrollments.find({"status": "Enrolled"})
    enrolled_students_list = list(enrolled_students_cursor)
    enrolled_count = len(enrolled_students_list)
    total_classes = db.classSchedule.count_documents({})

    pdf.cell(0, 10, f"Total Students: {total_students}", ln=True)
    pdf.cell(0, 10, f"Currently Enrolled: {enrolled_count}", ln=True)
    pdf.cell(0, 10, f"Total Classes: {total_classes}", ln=True)
    pdf.ln(10)

    # Table of Enrolled Students
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(80, 10, 'Name', 1)
    pdf.cell(60, 10, 'Course', 1)
    pdf.cell(40, 10, 'Year Level', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 10)
    for enrollment in enrolled_students_list:
        student = db.students.find_one({"_id": enrollment["studentId"]})
        if student:
            pdf.cell(80, 10, student.get("Name", "N/A"), 1)
            pdf.cell(60, 10, student.get("Course", "N/A"), 1)
            pdf.cell(40, 10, str(student.get("YearLevel", "N/A")), 1)
            pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

def generate_grade_distribution_pdf(db):
    pdf = PDF('P', 'mm', 'A4', title='Grade Distribution Report')
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    all_enrollments = list(db.enrollments.find({"grade": {"$ne": None}}))
    if not all_enrollments:
        pdf.cell(0, 10, "No grades available for this report.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    grades = [enrollment['grade'] for enrollment in all_enrollments]
    letter_grades = [get_letter_grade(score) for score in grades]
    grade_counts = pd.Series(letter_grades).value_counts().sort_index()

    # Generate and save chart
    fig, ax = plt.subplots()
    grade_counts.plot(kind='bar', ax=ax)
    ax.set_title('Distribution of Grades')
    ax.set_xlabel('Letter Grade')
    ax.set_ylabel('Number of Students')
    chart_path = '/tmp/grade_dist_chart.png'
    fig.savefig(chart_path)
    plt.close(fig)

    # Add chart to PDF
    pdf.image(chart_path, x=10, y=pdf.get_y(), w=190)
    pdf.ln(80) # Move down to make space for the chart

    # Add table of grades
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(80, 10, 'Student Name', 1)
    pdf.cell(30, 10, 'Grade', 1)
    pdf.cell(30, 10, 'Letter Grade', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 10)
    for enrollment in all_enrollments:
        student = db.students.find_one({"_id": enrollment["studentId"]})
        if student:
            pdf.cell(80, 10, student.get("Name", "N/A"), 1)
            pdf.cell(30, 10, str(enrollment.get("grade", "N/A")), 1)
            pdf.cell(30, 10, get_letter_grade(enrollment.get("grade", 0)), 1)
            pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

def generate_faculty_workload_pdf(db):
    pdf = PDF('P', 'mm', 'A4', title='Faculty Workload Report')
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pipeline = [
        {"$lookup": {"from": "enrollments", "localField": "_id", "foreignField": "classOfferingId", "as": "enrolled_students"}},
        {"$lookup": {"from": "faculty", "localField": "facultyId", "foreignField": "_id", "as": "faculty_info"}},
        {"$unwind": "$faculty_info"},
        {"$lookup": {"from": "subjects", "localField": "subjectId", "foreignField": "_id", "as": "subject_info"}},
        {"$unwind": "$subject_info"},
        {"$project": {"faculty_name": "$faculty_info.facultyName", "subject_name": "$subject_info.Description", "student_count": {"$size": "$enrolled_students"}}},
        {"$group": {"_id": "$faculty_name", "total_students": {"$sum": "$student_count"}, "subjects_taught": {"$push": "$subject_name"}}}
    ]
    workload_data = list(db.classSchedule.aggregate(pipeline))

    if not workload_data:
        pdf.cell(0, 10, "No faculty workload data available.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    for faculty in workload_data:
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, faculty['_id'], ln=True)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 10, f"Total Students: {faculty['total_students']}", ln=True)
        pdf.cell(0, 10, f"Classes Taught: {len(faculty['subjects_taught'])}", ln=True)
        pdf.cell(0, 10, "Subjects:", ln=True)
        pdf.set_font('Arial', 'I', 10)
        for subject in faculty['subjects_taught']:
            pdf.cell(10)
            pdf.cell(0, 10, f"- {subject}", ln=True)
        pdf.ln(5)

    return pdf.output(dest='S').encode('latin-1')

def generate_class_schedule_pdf(db):
    pdf = PDF('L', 'mm', 'A4', title='Class Schedule Report') # Landscape mode
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    pipeline = [
        {"$lookup": {"from": "subjects", "localField": "subjectId", "foreignField": "_id", "as": "subject_info"}},
        {"$unwind": "$subject_info"},
        {"$lookup": {"from": "faculty", "localField": "facultyId", "foreignField": "_id", "as": "faculty_info"}},
        {"$unwind": "$faculty_info"},
        {"$project": {
            "Subject": "$subject_info.Description",
            "Section": "$section",
            "Faculty": "$faculty_info.facultyName",
            "Schedule": "$schedule"
        }}
    ]
    schedule_data = list(db.classSchedule.aggregate(pipeline))

    if not schedule_data:
        pdf.cell(0, 10, "No class schedule data available.", ln=True)
        return pdf.output(dest='S').encode('latin-1')

    # Table Header
    pdf.set_font('Arial', 'B', 8)
    pdf.cell(70, 10, 'Subject', 1)
    pdf.cell(30, 10, 'Section', 1)
    pdf.cell(60, 10, 'Faculty', 1)
    pdf.cell(25, 10, 'Day', 1)
    pdf.cell(40, 10, 'Time', 1)
    pdf.cell(25, 10, 'Room', 1)
    pdf.ln()

    # Table Body
    pdf.set_font('Arial', '', 8)
    for item in schedule_data:
        for schedule_entry in item['Schedule']:
            pdf.cell(70, 10, item['Subject'], 1)
            pdf.cell(30, 10, item['Section'], 1)
            pdf.cell(60, 10, item['Faculty'], 1)
            pdf.cell(25, 10, schedule_entry.get('day', 'N/A'), 1)
            pdf.cell(40, 10, schedule_entry.get('time', 'N/A'), 1)
            pdf.cell(25, 10, schedule_entry.get('room', 'N/A'), 1)
            pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# --- Main Page ---

def report_manager_page(st, db):
    st.title("Reports and Analytics")

    reports = {
        "Enrollment Summary": (display_enrollment_summary, generate_enrollment_summary_pdf),
        "Grade Distribution": (display_grade_distribution, generate_grade_distribution_pdf),
        "Faculty Workload": (display_faculty_workload, generate_faculty_workload_pdf),
        "Class Schedule": (display_class_schedule, generate_class_schedule_pdf),
    }

    selected_report = st.selectbox("Select a report", list(reports.keys()))

    if selected_report:
        display_func, pdf_func = reports[selected_report]

        display_func(db)

        if pdf_func:
            pdf_data = pdf_func(db)
            st.download_button(
                label="Download as PDF",
                data=pdf_data,
                file_name=f"{selected_report.replace(' ', '_').lower()}.pdf",
                mime="application/pdf"
            )