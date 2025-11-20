import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

# -----------------------------------------------------------
# PAGE CONFIG & BASIC STYLE
# -----------------------------------------------------------

st.set_page_config(
    page_title="Engineering Analytics Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    .metric-card {
        padding: 1rem 1.25rem;
        border-radius: 0.9rem;
        background-color: var(--background-color);
        border: 1px solid rgba(200, 200, 200, 0.15);
        box-shadow: 0 0 12px rgba(0,0,0,0.04);
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--secondary-text-color);
    }
    .metric-value {
        font-size: 1.4rem;
        font-weight: 600;
        color: var(--text-color);
    }
    .metric-sub {
        font-size: 0.8rem;
        color: var(--secondary-text-color);
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
# DATA LOAD HELPERS
# -----------------------------------------------------------

@st.cache_data(ttl=600)
def get_repo_velocity():
    return run_query("SELECT * FROM repo_velocity ORDER BY week_start")

@st.cache_data(ttl=600)
def get_reviewer_load():
    return run_query("SELECT * FROM reviewer_load ORDER BY week_start")

@st.cache_data(ttl=600)
def get_pr_review_summary():
    return run_query("SELECT * FROM pr_review_summary")

@st.cache_data(ttl=600)
def get_dora_metrics():
    return run_query("SELECT * FROM dora_metrics_weekly ORDER BY week_start")

@st.cache_data(ttl=600)
def get_fact_pr_cycle_time():
    return run_query("SELECT * FROM fact_pr_cycle_time")

# -----------------------------------------------------------
# GLOBAL FILTERS (sidebar)
# -----------------------------------------------------------

facts_preview = get_fact_pr_cycle_time()

with st.sidebar:
    st.title("🧭 Navigation")

    page = st.radio(
        "Go to",
        [
            "Overview",
            "Repo Velocity",
            "Reviewer Load",
            "PR Review Summary",
            "DORA Metrics",
            "Contributor Leaderboard",
            "Reviewer-Author Heatmap",
            "Cycle Time Prediction",
            "Settings",
        ],
    )

    st.markdown("---")
    st.subheader("Global Filters")

    # Repos from fact table (fallbacks if empty)
    if not facts_preview.empty and "REPO" in facts_preview.columns:
        all_repos = sorted(facts_preview["REPO"].dropna().unique())
    else:
        all_repos = []

    selected_repos = st.multiselect(
        "Repos",
        options=all_repos,
        default=all_repos,
    )
    st.session_state["selected_repos"] = selected_repos or all_repos

    # Date range based on CREATED_AT if available
    if not facts_preview.empty and "CREATED_AT" in facts_preview.columns:
        facts_preview["CREATED_AT"] = pd.to_datetime(facts_preview["CREATED_AT"])
        min_date = facts_preview["CREATED_AT"].min().date()
        max_date = facts_preview["CREATED_AT"].max().date()
        dr = st.date_input(
            "Created date range",
            value=[min_date, max_date],
        )
        if isinstance(dr, list) and len(dr) == 2:
            st.session_state["date_range"] = dr

    st.markdown("---")
    st.caption("Powered by dbt • Snowflake • Streamlit")

def apply_global_filters(
    df: pd.DataFrame,
    repo_col: str | None = "REPO",
    date_col: str | None = None,
) -> pd.DataFrame:
    if df.empty:
        return df

    # filter by repo
    if repo_col and repo_col in df.columns and "selected_repos" in st.session_state:
        repos = st.session_state["selected_repos"]
        if repos:
            df = df[df[repo_col].isin(repos)]

    # filter by date
    if date_col and date_col in df.columns and "date_range" in st.session_state:
        start_date, end_date = st.session_state["date_range"]
        df[date_col] = pd.to_datetime(df[date_col])
        df = df[(df[date_col].dt.date >= start_date) & (df[date_col].dt.date <= end_date)]

    return df

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

    dora_df = apply_global_filters(get_dora_metrics(), repo_col="REPO", date_col="WEEK_START")
    rev_df = apply_global_filters(get_reviewer_load(), repo_col="REPO", date_col="WEEK_START")

    # KPIs based on last 4 weeks of DORA
    if not dora_df.empty:
        latest_week = dora_df["WEEK_START"].max()
        recent_weeks = dora_df[dora_df["WEEK_START"] >= (latest_week - pd.Timedelta(weeks=4))]
    else:
        recent_weeks = dora_df

    total_deploys = int(recent_weeks["DEPLOYMENTS"].sum()) if not recent_weeks.empty else 0
    avg_lead_time = recent_weeks["AVG_LEAD_TIME_HOURS"].mean() if not recent_weeks.empty else None
    avg_cfr = recent_weeks["CHANGE_FAILURE_RATE"].mean() if not recent_weeks.empty else None

    latest_rev = rev_df[rev_df["WEEK_START"] == rev_df["WEEK_START"].max()] if not rev_df.empty else rev_df
    avg_reviewer_load = latest_rev["PRS_REVIEWED"].mean() if not latest_rev.empty else None

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        kpi_card("Deployments (Last 4 Weeks)", f"{total_deploys}", "Merged PRs as deployments")
    with col2:
        kpi_card("Avg Lead Time (hrs)", format_number(avg_lead_time), "DORA Lead Time for Changes")
    with col3:
        kpi_card("Change Failure Rate", format_number(avg_cfr, 3), "Failed builds / total builds")
    with col4:
        kpi_card("Avg Reviewer Load", format_number(avg_reviewer_load), "PRs reviewed per reviewer")

    st.markdown("### 📈 Deployment & Lead Time Trends")

    if not dora_df.empty:
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

# -----------------------------------------------------------
# PAGE: REPO VELOCITY
# -----------------------------------------------------------

elif page == "Repo Velocity":
    st.title("📦 Repo Velocity (Weekly)")

    df = apply_global_filters(get_repo_velocity(), repo_col="REPO", date_col="WEEK_START")

    if df.empty:
        st.warning("No repo velocity data available.")
    else:
        repo_list = sorted(df["REPO"].unique())
        selected_repos = st.multiselect("Repos (override global filter):", repo_list, default=repo_list)
        if selected_repos:
            df = df[df["REPO"].isin(selected_repos)]

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                df,
                x="WEEK_START",
                y="PRS_OPENED",
                color="REPO",
                barmode="group",
                title="PRs Opened Per Week by Repo",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.line(
                df,
                x="WEEK_START",
                y="AVG_CYCLE_TIME_HOURS",
                color="REPO",
                title="Average PR Cycle Time (hrs) by Repo",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Raw Repo Velocity Data")
        st.dataframe(df.sort_values(["WEEK_START", "REPO"]), use_container_width=True)

# -----------------------------------------------------------
# PAGE: REVIEWER LOAD
# -----------------------------------------------------------

elif page == "Reviewer Load":
    st.title("👥 Reviewer Load Balancing")

    df = apply_global_filters(get_reviewer_load(), repo_col="REPO", date_col="WEEK_START")

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
        st.dataframe(filtered.sort_values(["WEEK_START", "REPO"]), use_container_width=True)

# -----------------------------------------------------------
# PAGE: PR REVIEW SUMMARY
# -----------------------------------------------------------

elif page == "PR Review Summary":
    st.title("🔍 PR Review Summary (Reviewer Metrics)")

    df = apply_global_filters(get_pr_review_summary(), repo_col="REPO")

    if df.empty:
        st.warning("No PR review summary data available.")
    else:
        st.markdown("#### Reviewer-level metrics")
        st.dataframe(df.sort_values(["REPO", "REVIEWER"]), use_container_width=True)

        if "TOTAL_PRS_REVIEWED" in df.columns:
            top_reviewers = df.sort_values("TOTAL_PRS_REVIEWED", ascending=False).head(15)
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

    df = apply_global_filters(get_dora_metrics(), repo_col="REPO", date_col="WEEK_START")

    if df.empty:
        st.warning("No DORA metrics available.")
    else:
        repo_list = sorted(df["REPO"].dropna().unique())
        selected_repo = st.selectbox("Select repo:", repo_list)

        filtered = df[df["REPO"] == selected_repo]

        col1, col2, col3 = st.columns(3)
        with col1:
            fig = px.bar(filtered, x="WEEK_START", y="DEPLOYMENTS", title="Deployment Frequency")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.line(filtered, x="WEEK_START", y="AVG_LEAD_TIME_HOURS", title="Lead Time (hrs)")
            st.plotly_chart(fig, use_container_width=True)
        with col3:
            fig = px.line(filtered, x="WEEK_START", y="CHANGE_FAILURE_RATE", title="Change Failure Rate")
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("### Raw DORA Data")
        st.dataframe(filtered.sort_values("WEEK_START"), use_container_width=True)

# -----------------------------------------------------------
# PAGE: CONTRIBUTOR LEADERBOARD
# -----------------------------------------------------------

elif page == "Contributor Leaderboard":
    st.title("🏅 Contributor Leaderboard")

    facts = apply_global_filters(get_fact_pr_cycle_time(), repo_col="REPO", date_col="CREATED_AT")

    if facts.empty or "PR_AUTHOR" not in facts.columns:
        st.warning("fact_pr_cycle_time with PR_AUTHOR is required for this page.")
    else:
        metrics = (
            facts.groupby("PR_AUTHOR")
            .agg(
                PR_COUNT=("PR_ID", "nunique") if "PR_ID" in facts.columns else ("PR_AUTHOR", "size"),
                AVG_CYCLE_HRS=("PR_CYCLE_TIME_HOURS", "mean") if "PR_CYCLE_TIME_HOURS" in facts.columns else ("PR_AUTHOR", "size"),
                AVG_LINES_ADDED=("LINES_ADDED", "mean") if "LINES_ADDED" in facts.columns else ("PR_AUTHOR", "size"),
                AVG_LINES_DELETED=("LINES_DELETED", "mean") if "LINES_DELETED" in facts.columns else ("PR_AUTHOR", "size"),
            )
            .reset_index()
            .rename(columns={"PR_AUTHOR": "AUTHOR"})
        )

        metrics = metrics.sort_values("PR_COUNT", ascending=False)

        st.markdown("### Top Contributors (by PRs Opened)")
        st.dataframe(metrics, use_container_width=True)

        fig = px.bar(
            metrics.head(20),
            x="AUTHOR",
            y="PR_COUNT",
            title="Top 20 Authors by PR Count",
        )
        st.plotly_chart(fig, use_container_width=True)

# -----------------------------------------------------------
# PAGE: REVIEWER-AUTHOR HEATMAP
# -----------------------------------------------------------

elif page == "Reviewer-Author Heatmap":
    st.title("🔥 Reviewer ↔ Author Interaction Heatmap")

    df = apply_global_filters(get_fact_pr_cycle_time(), repo_col="REPO", date_col="CREATED_AT")

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
# PAGE: CYCLE TIME PREDICTION (ML)
# -----------------------------------------------------------

elif page == "Cycle Time Prediction":
    st.title("🧠 Cycle Time Prediction (ML Demo)")

    facts = apply_global_filters(get_fact_pr_cycle_time(), repo_col="REPO", date_col="CREATED_AT")

    required_cols = ["PR_CYCLE_TIME_HOURS", "LINES_ADDED", "LINES_DELETED", "FILES_CHANGED"]
    missing = [c for c in required_cols if c not in facts.columns]

    if missing:
        st.error(f"Missing required columns in fact_pr_cycle_time: {missing}")
    else:
        ml_df = facts[required_cols].dropna()
        if len(ml_df) < 200:
            st.warning("Not enough rows with complete data to train a reliable model (need ~200+).")
        else:
            X = ml_df[["LINES_ADDED", "LINES_DELETED", "FILES_CHANGED"]]
            y = ml_df["PR_CYCLE_TIME_HOURS"]

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            model = RandomForestRegressor(
                n_estimators=150,
                random_state=42,
                n_jobs=-1,
            )
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            mae = mean_absolute_error(y_test, y_pred)

            st.markdown("### Model Performance")
            st.write(f"Mean Absolute Error on Hold-out Set: **{mae:.2f} hours**")

            st.markdown("### What-if Prediction")
            col1, col2, col3 = st.columns(3)
            with col1:
                lines_added = st.number_input("Lines added", min_value=0, value=int(X["LINES_ADDED"].median()))
            with col2:
                lines_deleted = st.number_input("Lines deleted", min_value=0, value=int(X["LINES_DELETED"].median()))
            with col3:
                files_changed = st.number_input("Files changed", min_value=0, value=int(X["FILES_CHANGED"].median()))

            if st.button("Predict cycle time"):
                sample = pd.DataFrame(
                    {
                        "LINES_ADDED": [lines_added],
                        "LINES_DELETED": [lines_deleted],
                        "FILES_CHANGED": [files_changed],
                    }
                )
                pred = model.predict(sample)[0]
                st.success(f"Predicted PR cycle time: **{pred:.2f} hours**")

            st.markdown("### Feature Importance")
            importance = pd.DataFrame(
                {
                    "feature": ["LINES_ADDED", "LINES_DELETED", "FILES_CHANGED"],
                    "importance": model.feature_importances_,
                }
            ).sort_values("importance", ascending=False)

            fig = px.bar(
                importance,
                x="feature",
                y="importance",
                title="Feature Importance",
            )
            st.plotly_chart(fig, use_container_width=True)

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
