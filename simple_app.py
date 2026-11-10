"""SFF at a Glance – a simpler, plain-language version of the SFF dashboard for campus-wide audiences.

Run:  python -m streamlit run simple_app.py
It reads the same database as the full dashboard (app.py); run `python -m tools.build_db` after data changes.
Activities can be updated and added on "What we're doing about it"; approvals stay in the full dashboard.
"""
import streamlit as st

st.set_page_config(page_title="SFF at a Glance", page_icon="🎓", layout="wide")

import importlib  # noqa: E402
import os  # noqa: E402
import sys  # noqa: E402

# Streamlit reloads page files when they change, but not always the shared code they import (sff\, views\common.py).
# Reload any of those whose file changed since it was loaded, so updated files work without restarting the app.
_SHARED = ["sff.config", "sff.activity_edits", "sff.cohort", "sff.etl", "sff.data", "sff.charts", "sff.report",
           "views.common"]
for _name in _SHARED:
    _m = sys.modules.get(_name)
    _f = getattr(_m, "__file__", None)
    if not _f or not os.path.exists(_f):
        continue
    _t = os.path.getmtime(_f)
    if getattr(_m, "_src_mtime", None) != _t:   # first check in this app session, or the file changed
        importlib.reload(_m)
        _m._src_mtime = _t

from simple import theme  # noqa: E402

theme.inject_css()

pages = st.navigation({
    "Progress": [st.Page("simple/progress.py", title="How our students are doing", icon="🎓", default=True)],
    "The plan": [st.Page("simple/plan.py", title="What we're doing about it", icon="🧭"),
                 st.Page("simple/manage.py", title="Update activities", icon="✏️")],
})
st.sidebar.title("Cerritos College")
st.sidebar.caption("Students First Framework  \nSFF at a Glance")
pages.run()
