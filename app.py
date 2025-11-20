import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector

# -----------------------------------------------------------
# SNOWFLAKE CONNECTION (reads from .streamlit/secrets.toml)
# -----------------------------------------------------------

@st.cache_resource
def get_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
        role=st.secrets["snowflake"]["role"]
    )

# -----------------------------------------------------------
# QUERY HELPER
# -----------------------------------------------------------

def run_query(query: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    df = cur.fetch_pandas_all()
    cur.close()
    return df

# -----------------------------------------------------------
# STREAMLIT UI SETUP
# -----------------------------------------------------------

st.set_page_config(page_title="Engineering Analytics Dashboard", layout="wide")

st.title("🚀 Engineering Productivity Dashboard")
st.markdown("Apple-style SWE analytics powered by dbt + Snowflake + Streamlit.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Repo Velocity",
    "👥 Reviewer Load",
    "🔍 PR Review Summary",
    "📊 DORA Metrics"
])

# -----------------------------------------------------------
# TAB 1 — REPO VELOCITY
# -----------------------------------------------------------

with tab1:
    st.header("📦 Repo Velocity (Weekly)")
    df = run_query("SELECT * FROM repo_velocity ORDER BY week_start DESC")

    repo_list = df['REPO'].unique()
    selected_repo = st.selectbox("Select a repo:", repo_list)

    repo_df = df[df['REPO'] == selected_repo]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(repo_df, x="WEEK_START", y="PRS_OPENED", title="PRs Opened Per Week")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(repo_df, x="WEEK_START", y="AVG_CYCLE_TIME_HOURS",
                      title="Avg PR Cycle Time (hrs)")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# TAB 2 — REVIEWER LOAD
# -----------------------------------------------------------

with tab2:
    st.header("👥 Reviewer Load Balancing")
    df = run_query("SELECT * FROM reviewer_load ORDER BY week_start DESC")

    reviewer_list = df['REVIEWER'].unique()
    selected_reviewer = st.selectbox("Select a reviewer:", reviewer_list)

    rv_df = df[df['REVIEWER'] == selected_reviewer]

    col1, col2 = st.columns(2)

    with col1:
        fig = px.bar(rv_df, x="WEEK_START", y="PRS_REVIEWED",
                     title="PRs Reviewed Per Week")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(rv_df, x="WEEK_START", y="AVG_REVIEW_TIME_HOURS",
                      title="Avg Review Time (hrs)")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# TAB 3 — PR REVIEW SUMMARY
# -----------------------------------------------------------

with tab3:
    st.header("🔍 PR Review Summary (Reviewer Metrics)")
    df = run_query("SELECT * FROM pr_review_summary ORDER BY reviewer")

    st.dataframe(df, use_container_width=True)

# -----------------------------------------------------------
# TAB 4 — DORA METRICS
# -----------------------------------------------------------

with tab4:
    st.header("📊 DORA Metrics (Weekly)")
    df = run_query("SELECT * FROM dora_metrics_weekly ORDER BY week_start DESC")

    repo_list = df['REPO'].dropna().unique()
    selected_repo = st.selectbox("Select repo for DORA metrics:", repo_list)

    dora_df = df[df['REPO'] == selected_repo]

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = px.bar(dora_df, x="WEEK_START", y="DEPLOYMENTS",
                     title="Deployment Frequency")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.line(dora_df, x="WEEK_START", y="AVG_LEAD_TIME_HOURS",
                      title="Lead Time (hrs)")
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = px.line(dora_df, x="WEEK_START", y="CHANGE_FAILURE_RATE",
                      title="Change Failure Rate")
        st.plotly_chart(fig, use_container_width=True)
