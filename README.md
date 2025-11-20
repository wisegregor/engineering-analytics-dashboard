# 🚀 Engineering Analytics Dashboard  
_A modular engineering-productivity platform powered by Snowflake, dbt, and Streamlit_

This dashboard provides a unified view of engineering productivity metrics across repositories, reviewers, and teams — including **Repo Velocity**, **Reviewer Load**, **PR Review Summary**, and **DORA Metrics**.  

Built with a **modern data stack**:  
**dbt → Snowflake → Streamlit → Plotly**  

---

## 🔥 Features

### 📦 **1. Repo Velocity**
- PRs opened & merged per week  
- Cycle time trends  
- Weekly engineering throughput  

### 👥 **2. Reviewer Load**
- Workload balancing across reviewers  
- Avg review time per engineer  
- Reviewer-specific trends  

### 🔍 **3. PR Review Summary**
- Reviewer efficiency metrics  
- Review counts & time analysis  
- Full reviewer benchmarking table  

### 📊 **4. DORA Metrics**
- Deployment frequency  
- Lead time for changes  
- Change failure rate  
- MTTR (mean time to restore)  

---

## 🖼️ Screenshots (placeholders — add later)

> Replace these with real screenshots once the app loads consistently.

![Dashboard Homepage](screenshots/homepage.png)  
![Repo Velocity](screenshots/repo_velocity.png)  
![Reviewer Load](screenshots/reviewer_load.png)  
![DORA Metrics](screenshots/dora_metrics.png)

---

## 🏗️ Architecture Overview

```text
            ┌──────────────────┐
            │      dbt         │
            │ (transformations)│
            └────────┬─────────┘
                     │
                     ▼
           ┌────────────────────┐
           │     Snowflake      │
           │  (metrics tables)  │
           └────────┬───────────┘
                     │ SQL
                     ▼
         ┌────────────────────────┐
         │   Python / Streamlit   │
         │  utils/snowflake.py    │
         └────────┬───────────────┘
                  │ DataFrames
                  ▼
        ┌────────────────────────────┐
        │ Engineering Dashboard UI   │
        │ (Streamlit multipage app)  │
        └────────────────────────────┘
