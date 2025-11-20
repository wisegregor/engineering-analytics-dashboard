# pages/3_PR_Review_Summary.py
import streamlit as st
from utils.snowflake import run_query
import plotly.express as px

st.title("🔍 PR Review Summary")

df = run_query("SELECT * FROM PR_REVIEW_SUMMARY")

if df.empty:
    st.warning("No data in PR_REVIEW_SUMMARY.")
    st.stop()

repos = sorted(df["REPO"].unique())
selected_repo = st.selectbox("Filter by repo", ["All"] + repos, index=0)

if selected_repo != "All":
    df = df[df["REPO"] == selected_repo]

st.markdown("### Reviewer Performance Table")
st.dataframe(
    df[
        [
            "REPO",
            "REVIEWER",
            "TOTAL_PRS_REVIEWED",
            "AVG_REVIEW_TIME_HOURS",
            "AVG_PR_CYCLE_TIME_HOURS",
            "AVG_CHANGED_FILES",
            "AVG_FILES_CHANGED",
            "AVG_LINES_ADDED",
            "AVG_LINES_DELETED",
            "FIRST_PR_DATE",
            "LAST_PR_DATE",
        ]
    ],
    use_container_width=True,
)

st.markdown("### Review Time vs Volume")

fig = px.scatter(
    df,
    x="TOTAL_PRS_REVIEWED",
    y="AVG_REVIEW_TIME_HOURS",
    color="REVIEWER",
    hover_data=["REPO"],
    title="Average Review Time vs PR Volume (per reviewer)",
)
st.plotly_chart(fig, use_container_width=True)
