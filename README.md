# **📊 Engineering Analytics Dashboard**

*A modular engineering-productivity platform powered by Snowflake, dbt, and Streamlit*

<p align="center">
  <a href="https://engineering-analytics-dashboard-sxhkwqvff8fsndqmnpkns5.streamlit.app/" target="_blank">
    <img src="https://img.shields.io/badge/🔴 Live_Dashboard-Open_App-F54242?style=for-the-badge" alt="Live App">
  </a>
</p>

This dashboard provides a unified view of engineering productivity across repositories, reviewers, and teams — including **Repo Velocity**, **Reviewer Load**, **PR Review Summary**, and **DORA Metrics**.

Built with a **modern analytics stack**:
**dbt → Snowflake → Streamlit → Plotly**

---

## 🔥 Features

### 📦 **1. Repo Velocity**

* PRs opened & merged per week
* Cycle time trends
* Engineering throughput over time

### 👥 **2. Reviewer Load**

* Reviewer workload balancing
* Avg review time per engineer
* Reviewer-specific weekly trends

### 🔍 **3. PR Review Summary**

* Reviewer efficiency metrics
* Review counts & PR interaction stats
* Full benchmarking table for all reviewers

### 📊 **4. DORA Metrics**

* Deployment frequency
* Lead time for changes
* Change failure rate
* MTTR (mean time to restore)

---

## 🖼️ Screenshots (placeholders — will add real ones later)

> Replace the filenames with real screenshots when ready.

![Dashboard Homepage](screenshots/homepage.png)
![Repo Velocity](screenshots/repo_velocity.png)
![Reviewer Load](screenshots/reviewer_load.png)
![DORA Metrics](screenshots/dora_metrics.png)

---

## 🏗️ Architecture Overview

```text
            ┌──────────────────┐
            │        dbt        │
            │ (transformations) │
            └────────┬─────────┘
                     │
                     ▼
           ┌────────────────────┐
           │     Snowflake      │
           │  (metrics tables)  │
           └────────┬───────────┘
                     │  SQL
                     ▼
         ┌────────────────────────┐
         │   Python / Streamlit   │
         │  utils/snowflake.py    │
         └────────┬───────────────┘
                  │ DataFrames
                  ▼
        ┌────────────────────────────┐
        │  Engineering Dashboard UI   │
        │  (Streamlit multipage app)  │
        └────────────────────────────┘
```

---

## 🚀 Local Development

```
git clone https://github.com/wisegregor/engineering-analytics-dashboard.git
cd engineering-analytics-dashboard
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
streamlit run app.py
```

Make sure to add your Snowflake credentials:

```
.streamlit/secrets.toml
```

---