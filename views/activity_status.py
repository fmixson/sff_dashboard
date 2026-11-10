import streamlit as st

from sff import data as D
from views import common

st.title("Activity Status")
st.caption("Deans and managers record each approved activity's **expected result** at the start of the year, then "
           "update its **status** and **result vs. expected** at mid-year (January) and year-end. These feed the "
           "Lever Scorecard, Review & Decisions, and the Strategy Progress Report.")
common.approved_note()

req = D.with_activity_status(D.all_activities(common.requests()), D.load_activity_status())
acts_all = req

if acts_all.empty:
    st.warning("No activities yet. Requests become activities once they have VP/area approval (**VP Approvals** "
               "page); activities outside resource allocation are added on the **Add Activities** page.")
    st.stop()

f1, f2, f3, f4 = st.columns(4)
fy = f1.selectbox("Fiscal year", sorted(acts_all["fiscal_year"].unique(), reverse=True), key="as_fy")
a = acts_all[acts_all["fiscal_year"] == fy]
area = f2.selectbox("Area", ["All"] + sorted(a["area"].unique()), key="as_area")
if area != "All":
    a = a[a["area"] == area]
div = f3.selectbox("Division", ["All"] + sorted(a["division"].dropna().unique()), key="as_div")
if div != "All":
    a = a[a["division"] == div]
status = f4.multiselect("Show status", D.ACTIVITY_STATUSES, key="as_status")
g1, g2 = st.columns(2)
typ = g1.radio("Type", ["All", D.TYPE_REQUEST, D.TYPE_MANUAL], horizontal=True, key="as_type")
if typ != "All":
    a = a[a["activity_type"] == typ]
if g2.checkbox("Only activities with no expected result", key="as_noexp"):
    a = a[a["expected_result"].fillna("").astype(str).str.strip().eq("")]
if status:
    a = a[a["activity_status"].isin(status)]

a = a.sort_values(["strategy", "division", "department"])
common.activity_status_editor(a, key=f"as_{fy}_{area}_{div}", show_strategy=True)

with st.expander("Status history (all updates)"):
    hist = D.load_activity_status()
    if hist.empty:
        st.info("No updates recorded yet.")
    else:
        h = hist.merge(req[["activity_key", "request", "division", "strategy"]], on="activity_key", how="left")
        st.dataframe(h.sort_values("timestamp", ascending=False)[
            ["timestamp", "strategy", "division", "request", "expected_result", "status", "result_rating",
             "outcome", "entered_by"]],
            hide_index=True, width="stretch")
