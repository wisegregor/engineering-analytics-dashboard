# utils/styles.py
import streamlit as st


def apply_custom_styles():
    """Tweak a few CSS bits so metrics look good in dark mode."""
    st.markdown(
        """
        <style>
        [data-testid="stMetricLabel"] {
            color: var(--text-color) !important;
        }
        [data-testid="stMetricValue"] {
            color: var(--text-color) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
