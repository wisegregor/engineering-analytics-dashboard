# pages/5_Reviewer_Author_Heatmap.py
import streamlit as st
from utils.snowflake import run_query
import plotly.express as px

st.title("🔥 Reviewer ↔ Author Interaction Heatmap")

df = run_query("SELECT * FROM FACT_PR_CYCLE_TIME")

if df.empty:
    st.warning("No data in FACT_PR_CYCLE_TIME.")
    st.stop()

required_cols = {"REVIEWER", "PR_AUTHOR"}
if not required_cols.issubset(df.columns):
    st.error(f"FACT_PR_CYCLE_TIME is missing columns: {required_cols - set(df.columns)}")
    st.stop()

df = df.rename(columns={"PR_AUTHOR": "AUTHOR"})

hm = (
    df.groupby(["REVIEWER", "AUTHOR"])
    .size()
    .reset_index(name="PR_COUNT")
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
