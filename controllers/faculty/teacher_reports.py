import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

def class_grade_distribution(db, teacher_name, semester, school_year):
    st.subheader("📊 Class Grade Distribution")

    # Header info
    st.write(f"**Faculty Name:** {teacher_name}")
    st.write(f"**Semester and School Year:** {semester}, {school_year}")

    # Fetch grades handled by teacher in given term
    grades_cursor = db["grades"].find({
        "Teachers": teacher_name,
        "SemesterID": semester
    })

    data = []
    for g in grades_cursor:
        subject_codes = g.get("SubjectCodes", [])
        grades_list = g.get("Grades", [])
        teachers = g.get("Teachers", [])

        for subj, grade in zip(subject_codes, grades_list):
            # Get subject details
            subj_doc = db["subjects"].find_one({"_id": subj})
            subj_name = subj_doc["Description"] if subj_doc else subj

            # Find row or create new
            row = next((d for d in data if d["Course Code"] == subj), None)
            if not row:
                row = {
                    "Course Code": subj,
                    "Course Name": subj_name,
                    "95-100(%)": 0,
                    "90-94(%)": 0,
                    "85-89(%)": 0,
                    "80-84(%)": 0,
                    "75-79(%)": 0,
                    "Below 75(%)": 0,
                    "Total": 0
                }
                data.append(row)

            # Count into bins
            row["Total"] += 1
            if grade >= 95:
                row["95-100(%)"] += 1
            elif grade >= 90:
                row["90-94(%)"] += 1
            elif grade >= 85:
                row["85-89(%)"] += 1
            elif grade >= 80:
                row["80-84(%)"] += 1
            elif grade >= 75:
                row["75-79(%)"] += 1
            else:
                row["Below 75(%)"] += 1

    # Convert to dataframe
    df = pd.DataFrame(data)

    # Convert counts to percentages
    for col in ["95-100(%)","90-94(%)","85-89(%)","80-84(%)","75-79(%)","Below 75(%)"]:
        df[col] = round((df[col] / df["Total"]) * 100, 2).astype(str) + "%"

    df["Total"] = df["Total"].astype(str)  # keep total as count

    # Show DataFrame
    st.dataframe(df)

    # Histogram per subject
    for _, row in df.iterrows():
        st.write(f"### {row['Course Code']} - {row['Course Name']}")

        categories = ["95-100","90-94","85-89","80-84","75-79","Below 75"]
        values = [float(row[c].replace("%","")) for c in df.columns[2:-1]]

        fig, ax = plt.subplots()
        ax.bar(categories, values)
        ax.set_title(f"Grade Distribution - {row['Course Code']}")
        ax.set_ylabel("Percentage (%)")
        st.pyplot(fig)