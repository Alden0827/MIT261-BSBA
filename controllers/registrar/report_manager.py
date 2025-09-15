# import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# --- Report Display Functions ---

def display_enrollment_summary(st,db):
    st.subheader("Enrollment Summary")

    # Fetch data
    with st.spinner(f"Fetching total students...", show_time=True):
        total_students = db.students.count_documents({})
    with st.spinner(f"Fetching enrolled student...", show_time=True):
        enrolled_students_cursor = db.enrollments.find({"status": "Enrolled"})
        enrolled_students_list = list(enrolled_students_cursor)
        enrolled_count = len(enrolled_students_list)
    with st.spinner(f"Fetching total class schedule...", show_time=True):
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

# --- Main Page ---

def report_manager_page(st, db):
    st.title("Reports and Analytics")

    reports = {
        "Enrollment Summary": display_enrollment_summary,
        "Grade Distribution": display_grade_distribution,
        "Faculty Workload": display_faculty_workload,
        "Class Schedule": display_class_schedule,
    }

    selected_report = st.selectbox("Select a report", list(reports.keys()))

    if selected_report:
        display_func = reports[selected_report]
        display_func(db)