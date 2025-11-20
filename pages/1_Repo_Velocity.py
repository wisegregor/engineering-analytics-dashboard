# pages/1_Repo_Velocity.py
import streamlit as st
from utils.snowflake import run_query
import plotly.express as px

st.title("📦 Repo Velocity")

df = run_query("SELECT * FROM REPO_VELOCITY ORDER BY WEEK_START")

if df.empty:
    st.warning("No data in REPO_VELOCITY.")
    st.stop()

repos = sorted(df["REPO"].unique())
selected_repo = st.selectbox("Select a repo", repos)

repo_df = df[df["REPO"] == selected_repo].sort_values("WEEK_START")

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        repo_df,
        x="WEEK_START",
        y="PRS_OPENED",
        title="PRs Opened per Week",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        repo_df,
        x="WEEK_START",
        y="PRS_MERGED",
        title="PRs Merged per Week",
    )
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    fig = px.line(
        repo_df,
        x="WEEK_START",
        y="AVG_CYCLE_TIME_HOURS",
        title="Average PR Cycle Time (hrs)",
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.line(
        repo_df,
        x="WEEK_START",
        y="AVG_REVIEW_TIME_HOURS",
        title="Average Review Time (hrs)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### File & Diff Size (per week)")
col5, col6 = st.columns(2)
with col5:
    fig = px.line(
        repo_df,
        x="WEEK_START",
        y="AVG_LINES_ADDED",
        title="Avg Lines Added per PR",
    )
    st.plotly_chart(fig, use_container_width=True)
with col6:
    fig = px.line(
        repo_df,
        x="WEEK_START",
        y="AVG_LINES_DELETED",
        title="Avg Lines Deleted per PR",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Underlying Data")
st.dataframe(repo_df, use_container_width=True)
