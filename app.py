# app.py (HOMEPAGE for multipage Streamlit app)

import streamlit as st
from utils.snowflake import run_query
from utils.styles import apply_custom_styles
import plotly.express as px

st.set_page_config(
    page_title="Engineering Productivity",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply global styles
apply_custom_styles()

st.title("🚀 Engineering Productivity Overview")

# ----------------------------
# GLOBAL FILTERS (repo)
# ----------------------------
all_repos_df = run_query("SELECT DISTINCT REPO FROM DORA_METRICS_WEEKLY ORDER BY REPO")
all_repos = all_repos_df["REPO"].tolist()

selected_repo = st.sidebar.selectbox(
    "Filter by repo", options=["All"] + all_repos, index=0
)

st.sidebar.markdown("---")
st.sidebar.write("These filters affect the homepage overview only.")

# ----------------------------
# TOP-LEVEL KPIs (from DORA)
# ----------------------------
where_clause = "" if selected_repo == "All" else f"WHERE REPO = '{selected_repo}'"

kpi_sql = f"""
SELECT
    AVG(DEPLOYMENTS)               AS AVG_DEPLOYMENTS_PER_WEEK,
    AVG(AVG_LEAD_TIME_HOURS)       AS AVG_LEAD_TIME_HOURS,
    AVG(CHANGE_FAILURE_RATE)       AS AVG_CFR,
    AVG(MTTR_HOURS)                AS AVG_MTTR_HOURS
FROM DORA_METRICS_WEEKLY
{where_clause}
"""

kpi_df = run_query(kpi_sql)

col1, col2, col3, col4 = st.columns(4)
col1.metric(
    "Deployments / Week",
    int(kpi_df["AVG_DEPLOYMENTS_PER_WEEK"][0]) if not kpi_df.empty else "–",
)
col2.metric(
    "Lead Time (hrs)",
    round(kpi_df["AVG_LEAD_TIME_HOURS"][0], 2) if not kpi_df.empty else "–",
)
col3.metric(
    "Change Failure Rate",
    round(kpi_df["AVG_CFR"][0], 3) if not kpi_df.empty else "–",
)
col4.metric(
    "MTTR (hrs)",
    round(kpi_df["AVG_MTTR_HOURS"][0], 2) if not kpi_df.empty else "–",
)

st.markdown("---")

# ----------------------------
# DEPLOYMENT + LEAD TIME TRENDS
# ----------------------------
trend_sql = f"""
SELECT
    REPO,
    WEEK_START,
    DEPLOYMENTS,
    AVG_LEAD_TIME_HOURS,
    CHANGE_FAILURE_RATE
FROM DORA_METRICS_WEEKLY
{where_clause}
ORDER BY WEEK_START
"""

trend_df = run_query(trend_sql)
if trend_df.empty:
    st.warning("No DORA metrics found for this selection.")
else:
    colA, colB = st.columns(2)

    with colA:
        fig = px.bar(
            trend_df,
            x="WEEK_START",
            y="DEPLOYMENTS",
            color="REPO",
            title="Deployments per Week",
        )
        st.plotly_chart(fig, use_container_width=True)

    with colB:
        fig = px.line(
            trend_df,
            x="WEEK_START",
            y="AVG_LEAD_TIME_HOURS",
            color="REPO",
            title="Lead Time per Week (hrs)",
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("### Recent Records (DORA_METRICS_WEEKLY)")
st.dataframe(trend_df.sort_values("WEEK_START", ascending=False).head(50),
             use_container_width=True)
