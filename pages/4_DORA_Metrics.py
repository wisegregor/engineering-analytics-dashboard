# pages/4_DORA_Metrics.py
import streamlit as st
from utils.snowflake import run_query
import plotly.express as px

st.title("📊 DORA Metrics (Weekly)")

df = run_query("SELECT * FROM DORA_METRICS_WEEKLY ORDER BY WEEK_START")

if df.empty:
    st.warning("No data in DORA_METRICS_WEEKLY.")
    st.stop()

repos = sorted(df["REPO"].unique())
selected_repo = st.selectbox("Select repo", repos)

dora_df = df[df["REPO"] == selected_repo].sort_values("WEEK_START")

col1, col2 = st.columns(2)
with col1:
    fig = px.bar(
        dora_df,
        x="WEEK_START",
        y="DEPLOYMENTS",
        title="Deployment Frequency",
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.line(
        dora_df,
        x="WEEK_START",
        y="AVG_LEAD_TIME_HOURS",
        title="Lead Time (hrs)",
    )
    st.plotly_chart(fig, use_container_width=True)

col3, col4 = st.columns(2)
with col3:
    fig = px.line(
        dora_df,
        x="WEEK_START",
        y="CHANGE_FAILURE_RATE",
        title="Change Failure Rate",
    )
    st.plotly_chart(fig, use_container_width=True)

with col4:
    fig = px.line(
        dora_df,
        x="WEEK_START",
        y="MTTR_HOURS",
        title="MTTR (hrs)",
    )
    st.plotly_chart(fig, use_container_width=True)

st.markdown("### Underlying Data")
st.dataframe(dora_df, use_container_width=True)
