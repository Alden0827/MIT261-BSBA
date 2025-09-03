import pandas as pd
def report_manager_page(st,db):

    st.subheader("Reports & Analytics")
    enrollments = list(db.enrollments.find({"status": "Enrolled"}))
    data = []
    for e in enrollments:
        student = db.students.find_one({"_id": e["studentId"]})
        data.append({"student": student["studentName"], "grade": e.get("grade", 0)})
    df = pd.DataFrame(data)
    if not df.empty:
        st.write("GPA per Student")
        fig, ax = plt.subplots()
        ax.bar(df["student"], df["grade"])
        ax.set_ylabel("Grade")
        ax.set_xlabel("Student")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    # Enrollment Stats
    st.metric("Total Students", db.students.count_documents({}))
    st.metric("Currently Enrolled", db.enrollments.count_documents({"status": "Enrolled"}))
    st.metric("Total Classes", db.classSchedule.count_documents({}))