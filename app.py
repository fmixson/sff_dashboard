"""SFF Dashboard – Streamlit entry point.

Run:  python -m tools.build_db   (first time / after source files change)
      streamlit run app.py
"""
import streamlit as st

st.set_page_config(page_title="SFF Dashboard", page_icon="📊", layout="wide")

pages = st.navigation({
    "Progress": [
        st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
        st.Page("views/goal.py", title="Goal by Student Group", icon="🎓"),
        st.Page("views/completions.py", title="Completers", icon="📜"),
        st.Page("views/scorecard.py", title="Lever Scorecard", icon="🧭"),
        st.Page("views/strategies.py", title="Strategy Detail", icon="🎯"),
        st.Page("views/kpis.py", title="KPIs", icon="📈"),
        st.Page("views/resources.py", title="Resource Alignment", icon="💵"),
    ],
    "Update": [
        st.Page("views/approvals.py", title="VP Approvals", icon="🗳️"),
        st.Page("views/add_activities.py", title="Add Activities", icon="➕"),
        st.Page("views/activity_status.py", title="Activity Status", icon="☑️"),
    ],
    "Review": [
        st.Page("views/review.py", title="Review & Decisions", icon="📝"),
        st.Page("views/accreditation.py", title="Core Inquiry 3 Evidence", icon="✅"),
    ],
})
st.sidebar.caption("Cerritos College · Students First Framework\nPrototype – Core Inquiry 3")
pages.run()
