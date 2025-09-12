import streamlit as st
from streamlit_echarts import st_echarts
import helpers.report_helper as r

def display_grade_trend_per_course(st, db):
    st.subheader("📊 Grade Trends per Course (Heatmap)")
    df = r.get_grade_trend_per_course()
    if not df.empty:
        courses = df['Course'].unique().tolist()
        years = sorted(df['SchoolYear'].unique().tolist())
        heatmap_data = [
            [years.index(row['SchoolYear']), courses.index(row['Course']), round(row['Average'], 2)]
            for _, row in df.iterrows()
        ]
        val_min = df['Average'].min()
        val_max = df['Average'].max()
        options = {
            "tooltip": {"position": "top"},
            "grid": {"height": "70%", "top": "10%"},
            "xAxis": {"type": "category", "data": years, "splitArea": {"show": True}},
            "yAxis": {"type": "category", "data": courses, "splitArea": {"show": True}},
            "visualMap": {
                "min": val_min, "max": val_max, "calculable": True, "orient": "horizontal", "left": "center",
                "bottom": "5%", "inRange": {"color": ["#d73027", "#fee090", "#1a9850"]}
            },
            "series": [{"name": "Average Grade", "type": "heatmap", "data": heatmap_data, "label": {"show": True}}]
        }
        st_echarts(options=options, height="600px")
    else:
        st.info("No grade data found.")

def display_subject_load_intensity(st, db):
    st.subheader("📊 Subject Load Intensity per Course")
    df = r.get_subject_load_intensity()
    if not df.empty:
        st.dataframe(df)

        option = {
            "title": {"text": "Average Subject Load per Course"},
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df["Course"].tolist()},
            "yAxis": {"type": "value"},
            "series": [{"data": df["Load"].tolist(), "type": "bar"}]
        }
        st_echarts(options=option, height="500px")
    else:
        st.info("No course load data found.")

def display_ge_vs_major_subjects_performance(st, db):
    st.subheader("📊 General Education vs Major Subjects Performance Over Time")
    df = r.get_ge_vs_major()
    if not df.empty:
        st.dataframe(df)

        years = sorted(df["SchoolYear"].unique().tolist())
        ge_vals = df[df["Type"] == "GE"].sort_values("SchoolYear")["Average"].tolist()
        major_vals = df[df["Type"] == "Major"].sort_values("SchoolYear")["Average"].tolist()

        option = {
            "tooltip": {"trigger": "axis"},
            "legend": {"data": ["GE", "Major"]},
            "xAxis": {"type": "category", "data": years},
            "yAxis": {"type": "value"},
            "series": [
                {"name": "GE", "type": "bar", "data": ge_vals},
                {"name": "Major", "type": "bar", "data": major_vals},
            ]
        }
        st_echarts(options=option, height="500px")
    else:
        st.info("No data available.")
