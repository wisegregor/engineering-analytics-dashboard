# utils/snowflake.py
import streamlit as st
import snowflake.connector
import pandas as pd


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


def run_query(sql: str) -> pd.DataFrame:
    """Simple helper to run a query and return a pandas DataFrame."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    df = cur.fetch_pandas_all()
    cur.close()
    return df
