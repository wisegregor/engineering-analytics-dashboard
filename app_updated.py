import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
from functools import lru_cache

# -----------------------------------------------------------
# PAGE CONFIG & BASIC STYLE
# -----------------------------------------------------------

st.set_page_config(
    page_title="Engineering Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Minimal Apple-ish styling
CUSTOM_CSS = """
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .metric-card {
        padding: 1rem 1.25rem;
        border-radius: 0.9rem;
        background: rgba(30, 30, 30, 0.03);
        border: 1px solid rgba(200, 200, 200, 0.2);
        box-shadow: 0 6px 18px rgba(0,0,0,0.04);
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #888;
        margin-bottom: 0.25rem;
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #111;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #666;
        margin-top: 0.25rem;
    }
    .section-title {
        font-weight: 600;
        margin-top: 0.5rem;
        margin-bottom: 0.25rem;
    }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# -----------------------------------------------------------
# SNOWFLAKE CONNECTION (using secrets)
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
        role=st.secrets["snowflake"]["role"],
    )

@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(query)
    df = cur.fetch_pandas_all()
    cur.close()
    return df

# -----------------------------------------------------------
# SIDEBAR NAVIGATION
# -----------------------------------------------------------

st.sidebar.title("🧭 Navigation")

page = st.sidebar.radio(
    "Go to",
    [
        "Overview",
        "Repo Velocity",
        "Reviewer Load",
        "PR Review Summary",
        "DORA Metrics",
        "Reviewer-Author Heatmap",
        "Settings",
    ]
)

st.sidebar.markdown("---")
st.sidebar.caption("Powered by dbt + Snowflake + Streamlit")

# -----------------------------------------------------------
# GLOBAL DATA LOAD HELPERS
# (lazy-loaded per page to keep it responsive)
# -----------------------------------------------------------

def get_repo_velocity():
    return run_query("SELECT * FROM repo_velocity ORDER BY week_start")

def get_reviewer_load():
    return run_query("SELECT * FROM reviewer_load ORDER BY week_start")

def get_pr_review_summary():
    return run_query("SELECT * FROM pr_review_summary")

def get_dora_metrics():
    return run_query("SELECT * FROM dora_metrics_weekly ORDER BY week_start")

def get_fact_pr_cycle_time():
    return run_query("SELECT * FROM fact_pr_cycle_time")

# -----------------------------------------------------------
# KPI HELPERS
# -----------------------------------------------------------

def format_number(x, decimals=1):
    if x is None:
        return "–"
    try:
        return f"{x:.{decimals}f}"
    except Exception:
        return "–"

def kpi_card(label, value, sublabel=None):
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-sub">{sublabel or ""}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------------------------------------
# PAGE: OVERVIEW
# -----------------------------------------------------------

if page == "Overview":
    st.title("🚀 Engineering Productivity Overview")

    # Load data from marts
    dora_df = get_dora_metrics()
    repo_df = get_repo_velocity()
    rev_df = get_reviewer_load()

    # Recent window: last 4 weeks
    if not dora_df.empty:
        latest_week = dora_df["WEEK_START"].max()
        recent_weeks = dora_df[dora_df["WEEK_START"] >= (latest_week - pd.Timedelta(weeks=4))]
    else:
        recent_weeks = dora_df

    # Compute KPIs
    total_deploys = int(recent_weeks["DEPLOYMENTS"].sum()) if not recent_weeks.empty else 0
    avg_lead_time = recent_weeks["AVG_LEAD_TIME_HOURS"].mean() if not recent_weeks.empty else None
    avg_cfr = recent_weeks["CHANGE_FAILURE_RATE"].mean() if not recent_weeks.empty else None

    recent_reviewer = rev_df[rev_df["WEEK_START"] == rev_df["WEEK_START"].max()] if not rev_df.empty else rev_df
    avg_reviewer_load = recent_reviewer["PRS_REVIEWED"].mean() if not recent_reviewer.empty else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Deployments (Last 4 Weeks)", f"{total_deploys}", "Merged PRs as deployments")
    with col2:
        kpi_card(
            "Avg Lead Time (hrs)",
            format_number(avg_lead_time),
            "DORA Lead Time for Changes"
        )
    with col3:
        kpi_card(
            "Change Failure Rate",
            format_number(avg_cfr, 3),
            "Failed builds / total builds"
        )
    with col4:
        kpi_card(
            "Avg Reviewer Load",
            format_number(avg_reviewer_load),
            "PRs reviewed per reviewer (latest week)"
        )

    st.markdown("### 📈 Deployment & Lead Time Trends")

    if not dora_df.empty:
        # choose top repo by deployments in last N weeks
        repo_by_deploys = (
            recent_weeks.groupby("REPO")["DEPLOYMENTS"].sum().sort_values(ascending=False)
        )
        top_repo = repo_by_deploys.index[0] if not repo_by_deploys.empty else None

        if top_repo:
            focus = dora_df[dora_df["REPO"] == top_repo]

            col_a, col_b = st.columns(2)
            with col_a:
                fig = px.bar(
                    focus,
                    x="WEEK_START",
                    y="DEPLOYMENTS",
                    title=f"Deployments per Week — {top_repo}",
                )
                st.plotly_chart(fig, use_container_width=True)

            with col_b:
                fig = px.line(
                    focus,
                    x="WEEK_START",
                    y="AVG_LEAD_TIME_HOURS",
                    title=f"Lead Time (hrs) — {top_repo}",
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No DORA data available yet.")
    else:
        st.info("No DORA data available yet.")

    st.markdown("### 👥 Reviewer Load (Latest Week)")
    if not rev_df.empty:
        latest_week = rev_df["WEEK_START"].max()
        latest_rev = rev_df[rev_df["WEEK_START"] == latest_week]

        fig = px.bar(
            latest_rev.sort_values("PRS_REVIEWED", ascending=False),
            x="REVIEWER",
            y="PRS_REVIEWED",
            color="REPO",
            title="PRs Reviewed per Reviewer (Latest Week)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No reviewer load data available yet.")

# -----------------------------------------------------------
# PAGE: REPO VELOCITY
# -----------------------------------------------------------

elif page == "Repo Velocity":
    st.title("📦 Repo Velocity (Weekly)")

    df = get_repo_velocity()
    if df.empty:
        st.warning("No repo velocity data available.")
    else:
        repo_list = sorted(df["REPO"].unique())
        selected_repos = st.multiselect(
            "Select repo(s):", options=repo_list, default=repo_list[:1]
        )

        filtered = df[df["REPO"].isin(selected_repos)]

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                filtered,
                x="WEEK_START",
                y="PRS_OPENED",
                color="REPO",
                barmode="group",
                title="PRs Opened Per Week by Repo",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                filtered,
                x="WEEK_START",
                y="AVG_CYCLE_TIME_HOURS",
                color="REPO",
                title="Average PR Cycle Time (hrs) by Repo",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Raw Repo Velocity Data")
        st.dataframe(filtered.sort_values(["WEEK_START", "REPO"]), use_container_width=True)

# -----------------------------------------------------------
# PAGE: REVIEWER LOAD
# -----------------------------------------------------------

elif page == "Reviewer Load":
    st.title("👥 Reviewer Load Balancing")

    df = get_reviewer_load()
    if df.empty:
        st.warning("No reviewer load data available.")
    else:
        reviewer_list = sorted(df["REVIEWER"].unique())
        selected_reviewer = st.selectbox("Select reviewer:", reviewer_list)

        filtered = df[df["REVIEWER"] == selected_reviewer]

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                filtered,
                x="WEEK_START",
                y="PRS_REVIEWED",
                color="REPO",
                title=f"PRs Reviewed per Week — {selected_reviewer}",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                filtered,
                x="WEEK_START",
                y="AVG_REVIEW_TIME_HOURS",
                color="REPO",
                title=f"Average Review Time (hrs) — {selected_reviewer}",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Reviewer Load Raw Data")
        st.dataframe(
            filtered.sort_values(["WEEK_START", "REPO"]),
            use_container_width=True
        )

# -----------------------------------------------------------
# PAGE: PR REVIEW SUMMARY
# -----------------------------------------------------------

elif page == "PR Review Summary":
    st.title("🔍 PR Review Summary (Reviewer Metrics)")

    df = get_pr_review_summary()
    if df.empty:
        st.warning("No PR review summary data available.")
    else:
        st.markdown("#### Reviewer-level metrics")
        st.dataframe(df.sort_values(["REPO", "REVIEWER"]), use_container_width=True)

        # Optional: simple chart
        top_reviewers = df.sort_values("TOTAL_PRS_REVIEWED", ascending=False).head(15) \
            if "TOTAL_PRS_REVIEWED" in df.columns else df.head(0)

        if not top_reviewers.empty:
            st.markdown("#### Top Reviewers by PRs Reviewed")
            fig = px.bar(
                top_reviewers,
                x="REVIEWER",
                y="TOTAL_PRS_REVIEWED",
                color="REPO",
                title="Top Reviewers (by PRs Reviewed)",
            )
            st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# PAGE: DORA METRICS
# -----------------------------------------------------------

elif page == "DORA Metrics":
    st.title("📊 DORA Metrics (Weekly)")

    df = get_dora_metrics()
    if df.empty:
        st.warning("No DORA metrics available.")
    else:
        repo_list = sorted(df["REPO"].dropna().unique())
        selected_repo = st.selectbox("Select repo:", repo_list)

        filtered = df[df["REPO"] == selected_repo]

        col1, col2, col3 = st.columns(3)

        with col1:
            fig = px.bar(
                filtered,
                x="WEEK_START",
                y="DEPLOYMENTS",
                title="Deployment Frequency",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                filtered,
                x="WEEK_START",
                y="AVG_LEAD_TIME_HOURS",
                title="Lead Time (hrs)",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col3:
            fig = px.line(
                filtered,
                x="WEEK_START",
                y="CHANGE_FAILURE_RATE",
                title="Change Failure Rate",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Raw DORA Data")
        st.dataframe(filtered.sort_values("WEEK_START"), use_container_width=True)

# -----------------------------------------------------------
# PAGE: REVIEWER-AUTHOR HEATMAP
# -----------------------------------------------------------

elif page == "Reviewer-Author Heatmap":
    st.title("🔥 Reviewer ↔ Author Interaction Heatmap")

    df = get_fact_pr_cycle_time()
    if df.empty:
        st.warning("No fact_pr_cycle_time data available.")
    else:
        if "REVIEWER" not in df.columns or "PR_AUTHOR" not in df.columns:
            st.error("Required columns REVIEWER and PR_AUTHOR not found in fact_pr_cycle_time.")
        else:
            hm = (
                df.groupby(["REVIEWER", "PR_AUTHOR"])
                .size()
                .reset_index(name="PR_COUNT")
                .rename(columns={"PR_AUTHOR": "AUTHOR"})
            )

            reviewers = sorted(hm["REVIEWER"].unique())
            authors = sorted(hm["AUTHOR"].unique())

            pivot = hm.pivot(index="REVIEWER", columns="AUTHOR", values="PR_COUNT").fillna(0)

            fig = px.imshow(
                pivot,
                labels=dict(x="Author", y="Reviewer", color="PR Count"),
                x=authors,
                y=reviewers,
                aspect="auto",
                title="PR Interactions: Reviewer vs Author",
            )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("### Underlying Data")
            st.dataframe(hm.sort_values("PR_COUNT", ascending=False), use_container_width=True)

# -----------------------------------------------------------
# PAGE: SETTINGS
# -----------------------------------------------------------

elif page == "Settings":
    st.title("⚙️ Settings & Info")

    st.markdown("### Connection Info")
    st.write("Account:", st.secrets["snowflake"]["account"])
    st.write("Warehouse:", st.secrets["snowflake"]["warehouse"])
    st.write("Database:", st.secrets["snowflake"]["database"])
    st.write("Schema:", st.secrets["snowflake"]["schema"])

    st.markdown("### Caching")
    st.write("Query results are cached for 10 minutes (`@st.cache_data`).")
    st.write("Snowflake connection is cached via `@st.cache_resource`.")
