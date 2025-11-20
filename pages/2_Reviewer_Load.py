# pages/2_Reviewer_Load.py
import streamlit as st
from utils.snowflake import run_query
import plotly.express as px

st.title("👥 Reviewer Load")

df = run_query("SELECT * FROM REVIEWER_LOAD ORDER BY WEEK_START")

if df.empty:
    st.warning("No data in REVIEWER_LOAD.")
    st.stop()

reviewers = sorted(df["REVIEWER"].unique())
selected_reviewer = st.selectbox("Select a reviewer", reviewers)

rv_df = df[df["REVIEWER"] == selected_reviewer].sort_values("WEEK_START")

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        rv_df,
        x="WEEK_START",
        y="PRS_REVIEWED",
        color="REPO",
        title="PRs Reviewed per Week",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.line(
        rv_df,
        x="WEEK_START",
        y="AVG_REVIEW_TIME_HOURS",
        color="REPO",
        title="Avg Review Time (hrs)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Workload & Diff Size")

col3, col4 = st.columns(2)
with col3:
    fig = px.line(
        rv_df,
        x="WEEK_START",
        y="AVG_LINES_ADDED",
        color="REPO",
        title="Avg Lines Added in Reviewed PRs",
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.line(
        rv_df,
        x="WEEK_START",
        y="AVG_LINES_DELETED",
        color="REPO",
        title="Avg Lines Deleted in Reviewed PRs",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Reviewer Rank Snapshot (this week)")
latest_week = rv_df["WEEK_START"].max()
latest_df = df[df["WEEK_START"] == latest_week].sort_values(
    "REVIEWER_RANK_THIS_WEEK"
)

st.write(f"Week of {latest_week}")
st.dataframe(
    latest_df[
        [
            "REVIEWER",
            "REPO",
            "PRS_REVIEWED",
            "AVG_REVIEW_TIME_HOURS",
            "REVIEWER_RANK_THIS_WEEK",
        ]
    ],
    use_container_width=True,
)
