import streamlit as st
import pandas as pd
import report_helper as r
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# ------------------------------
# Streamlit App
# ------------------------------
st.set_page_config(page_title=" Analytics Reports", layout="wide")
st.title("📊 Student Analytics Reports")

report = st.selectbox(
    "Select a Report",
    [
        "Top Performers",
        "Failing Students",
        "Students with Grade Improvement",
        "Distribution of Grades",
        "Hardest Subject",
        "Easiest Subjects",
        "Average Grades per Teacher",
        "Teachers with High Failures",
        "Grade Trend per Course",
        "Subject Load Intensity",
        "GE vs Major Subjects Performance",
        "Semester with Lowest GPA",
        "Best Performing Semester",
        "Grade Deviation Across Semesters",
        "Year Level Distribution",
        "Student Count per Course",
        "Performance by Year Level"
    ]
)


# df_top = r.get_top_performers(school_year=2023, semester='FirstSem')
# print(df_top)


# ------------------------------
# Report Logic
# ------------------------------
if report == "Top Performers":
    # --- Fetch all possible values for dropdowns ---
    all_data = r.get_top_performers()
    if not all_data.empty:
        col_a, col_b = st.columns([2, 2])
        with col_a:
            sem_selected = st.selectbox("Semester", sorted(all_data["Semester"].unique()))
        with col_b:
            sy_selected = st.selectbox("School Year", sorted(all_data["SchoolYear"].unique()))

        # 🔹 Auto filter (no Go button)
        df_top = r.get_top_performers(school_year=sy_selected, semester=sem_selected)

        st.subheader("🏆 Top 10 Performers")

        if not df_top.empty:
            st.dataframe(df_top)

            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots()
                ax.barh(df_top["Student"], df_top["Average"])
                ax.set_xlabel("Average Grade")
                ax.set_ylabel("Student")
                ax.set_title("Top 10 Performers")
                plt.gca().invert_yaxis()
                st.pyplot(fig)

            with col2:
                course_avg = df_top.groupby("Course")["Average"].mean()
                fig2, ax2 = plt.subplots()
                ax2.pie(course_avg, labels=course_avg.index, autopct="%1.1f%%", startangle=90)
                ax2.set_title("Top Performers by Course")
                st.pyplot(fig2)
        else:
            st.info("No records found for the selected Semester and School Year.")
    else:
        st.info("No student records found.")


from streamlit_echarts import st_echarts

from streamlit_echarts import st_echarts
import pandas as pd

if report == "Failing Students":
    # --- Fetch all failing students (unfiltered) for dropdowns ---
    all_data = r.get_failing_students()
    if not all_data.empty:
        # --- Dropdown filters ---
        col1, col2 = st.columns([2, 2])
        with col1:
            sem_selected = st.selectbox(
                "Semester",
                sorted(all_data["Semester"].dropna().unique())
            )
        with col2:
            sy_selected = st.selectbox(
                "School Year",
                sorted(all_data["SchoolYear"].dropna().unique())
            )

        # --- Apply filters ---
        df_fails = r.get_failing_students(
            school_year=sy_selected, semester=sem_selected
        )

        st.subheader("📉 Students with High Failure Rate")

        if not df_fails.empty:
            # --- Table ---
            st.dataframe(df_fails)

            # --- Chart 1: Failures per Student (Bar) ---
            student_failures = df_fails.tail(20)[["Student", "Failures"]]
            options1 = {
                "title": {"text": "Top Failing Students"},
                "tooltip": {},
                "xAxis": {"type": "value"},
                "yAxis": {"type": "category", "data": student_failures["Student"].tolist()},
                "series": [{
                    "type": "bar",
                    "data": student_failures["Failures"].tolist(),
                    "itemStyle": {"color": "#FF6B6B"},
                }],
            }
            st_echarts(options=options1, height="400px")

            # --- Chart 2: Failures by Course (Pie) ---
            course_failures = df_fails.groupby("Course")["Failures"].sum().reset_index()
            options2 = {
                "title": {"text": "Failures by Course", "left": "center"},
                "tooltip": {"trigger": "item"},
                "legend": {"orient": "vertical", "left": "left"},
                "series": [{
                    "name": "Failures",
                    "type": "pie",
                    "radius": "50%",
                    "data": [
                        {"value": int(v), "name": str(n)}
                        for n, v in zip(course_failures["Course"], course_failures["Failures"])
                    ],
                }],
            }
            st_echarts(options=options2, height="400px")

            # --- Chart 3: Failure Rate Trend (Line) ---
            trend_data = all_data.groupby(["SchoolYear", "Semester"]).agg(
                {"Failures": "sum", "Subjects Taken": "sum"}
            ).reset_index()
            trend_data["FailureRate"] = trend_data["Failures"] / trend_data["Subjects Taken"]

            # Clean data
            trend_data = trend_data.dropna(subset=["Semester", "SchoolYear"])

            # Define semester order
            semester_order = ["1st", "2nd", "Summer"]
            trend_data["Semester"] = pd.Categorical(
                trend_data["Semester"],
                categories=semester_order,
                ordered=True
            )

            # Create continuous X-axis: "2023 1st", "2023 2nd", ...
            trend_data["YearSemester"] = trend_data["SchoolYear"].astype(str) + " " + trend_data["Semester"].astype(str)
            trend_data = trend_data.sort_values(["SchoolYear", "Semester"])

            x_axis = trend_data["YearSemester"].tolist()

            series_data = [{
                "name": "Failure Rate",
                "type": "line",
                "data": [round(v * 100, 1) for v in trend_data["FailureRate"]],
                "smooth": True,
            }]

            options3 = {
                "title": {"text": "Failure Rate Trend Across Years"},
                "tooltip": {"trigger": "axis", "formatter": "{b}: {c}%"},
                "xAxis": {"type": "category", "data": x_axis, "axisLabel": {"rotate": 45}},
                "yAxis": {"type": "value", "axisLabel": {"formatter": "{value}%"}},
                "series": series_data,
                "grid": {"bottom": 100},  # to prevent label cutoff
            }

            st_echarts(options=options3, height="400px")

        else:
            st.info("No failing students found for the selected Semester and School Year.")
    else:
        st.info("No student records found.")


elif report == "Students with Grade Improvement":
    # Load all data first (unfiltered)
    all_data = r.get_students_with_improvement()

    # --- Dropdown filters ---
    col1, col2 = st.columns([2, 2])
    with col1:
        sem_selected = st.selectbox(
            "Semester",
            ["All"] + sorted(pd.Series(all_data["Semester"]).dropna().unique())
        )
    with col2:
        sy_selected = st.selectbox(
            "School Year",
            ["All"] + sorted(pd.Series(all_data["SchoolYear"]).dropna().unique())
        )

    # --- Apply filters using selected dropdown values ---
    df = r.get_students_with_improvement(
        selected_semester=sem_selected,
        selected_sy=sy_selected
    )

    st.subheader("📈 Students with Grade Improvement")

    if not df.empty:
        # Show table
        st.dataframe(df)

        st.subheader("📈 Top 15 Students with Grade Improvement")
        df_top15 = df.head(15).copy()

        # --- Prepare ECharts data ---
        students_labels = df_top15["Student"].tolist()
        improvements = df_top15["Improvement"].tolist()

        # Color coding: negative/red, small improvement/orange, good/green
        colors = []
        for val in improvements:
            if val <= 14:
                colors.append("#FF4C4C")   # Red
            elif val <= 18:
                colors.append("#FFA500")   # Orange
            else:
                colors.append("#4CAF50")   # Green

        option = {
            "title": {"text": f"Top 15 Students with Grade Improvement (Semester: {sem_selected}, SchoolYear: {sy_selected})"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "value", "name": "Improvement"},
            "yAxis": {"type": "category", "data": students_labels, "name": "Student", "inverse": True},
            "series": [{
                "data": [{"value": val, "itemStyle": {"color": colors[i]}} for i, val in enumerate(improvements)],
                "type": "bar",
                "barMaxWidth": "50%"
            }]
        }

        st_echarts(option, height="500px")

    else:
        st.info("No student records found for the selected School Year / Semester.")


elif report == "Distribution of Grades":
    st.subheader("📊 Grade Distribution")

    # Load all data first (for filter dropdowns)
    all_data = r.get_distribution_of_grades()  # Returns a DataFrame now

    # --- Dropdown filters ---
    col1, col2 = st.columns([2, 2])
    with col1:
        sem_selected = st.selectbox(
            "Semester",
            ["All"] + sorted(all_data["Semester"].dropna().unique())
        )
    with col2:
        sy_selected = st.selectbox(
            "School Year",
            ["All"] + sorted(all_data["SchoolYear"].dropna().unique())
        )

    # --- Get filtered grades ---
    df_filtered = r.get_distribution_of_grades(
        selected_semester=sem_selected,
        selected_sy=sy_selected
    )

    if not df_filtered.empty:
        # Prepare bins
        bins = [60,65,70,75,80,85,90,95,100]
        bin_labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins)-1)]
        counts = [0]*(len(bins)-1)

        # Count grades per bin
        for g in df_filtered["Grade"]:
            for i in range(len(bins)-1):
                if bins[i] <= g < bins[i+1]:
                    counts[i] += 1
                    break

        # Color-coded bins
        colors = []
        for i in range(len(bins)-1):
            if bins[i+1] <= 75:
                colors.append("#FF4C4C")   # Red → Failing
            elif bins[i+1] <= 90:
                colors.append("#FFA500")   # Orange → Average
            else:
                colors.append("#4CAF50")   # Green → High grades

        # --- ECharts Option ---
        option = {
            "title": {"text": f"Grade Distribution (Semester: {sem_selected}, SchoolYear: {sy_selected})"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": bin_labels, "name": "Grade Range"},
            "yAxis": {"type": "value", "name": "Frequency"},
            "series": [{
                "data": [{"value": count, "itemStyle": {"color": colors[i]}} 
                         for i, count in enumerate(counts)],
                "type": "bar",
                "barMaxWidth": "50%"
            }]
        }

        st_echarts(option, height="400px")
    else:
        st.info("No grades found for the selected Semester/School Year.")


elif report == "Hardest Subject":
    df = r.get_hardest_subject()
    st.subheader("📉 Hardest Subjects")
    st.dataframe(df)

elif report == "Easiest Subjects":
    df = r.get_easiest_subjects()
    st.subheader("📈 Easiest Subjects")
    st.dataframe(df)

elif report == "Average Grades per Teacher":
    df = r.get_avg_grades_per_teacher()
    st.subheader("👩‍🏫 Average Grades per Teacher")
    st.dataframe(df)

elif report == "Teachers with High Failures":
    df = r.get_teachers_with_high_failures()
    st.subheader("❌ Teachers with Most Failures")
    st.dataframe(df)

elif report == "Grade Trend per Course":
    df = r.get_grade_trend_per_course()
    st.subheader("📊 Grade Trends per Course")
    st.line_chart(df, x="SchoolYear", y="Average", color="Course")

elif report == "Subject Load Intensity":
    df = r.get_subject_load_intensity()
    st.subheader("📚 Subject Load Intensity")
    st.bar_chart(df.set_index("Course"))

elif report == "GE vs Major Subjects Performance":
    df = r.get_ge_vs_major()
    st.subheader("📖 GE vs Major Subject Performance")
    st.bar_chart(df.set_index("Type"))

elif report == "Semester with Lowest GPA":
    df = r.get_lowest_gpa_semester()
    st.subheader("⬇️ Semester with Lowest GPA")
    st.dataframe(df)

elif report == "Best Performing Semester":
    df = r.get_best_gpa_semester()
    st.subheader("⬆️ Best Performing Semester")
    st.dataframe(df)

elif report == "Grade Deviation Across Semesters":
    df = r.get_grade_deviation_across_semesters()
    st.subheader("📊 Grade Variance Across Semesters")
    st.dataframe(df)

elif report == "Year Level Distribution":
    df = r.get_year_level_distribution()
    st.subheader("🎓 Year Level Distribution")
    st.bar_chart(df.set_index("YearLevel"))

elif report == "Student Count per Course":
    df = r.get_student_count_per_course()
    st.subheader("📚 Student Count per Course")
    st.bar_chart(df.set_index("Course"))

elif report == "Performance by Year Level":
    df = r.get_performance_by_year_level()
    st.subheader("📈 Performance by Year Level")
    st.bar_chart(df.set_index("YearLevel"))
