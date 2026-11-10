import streamlit as st

from sff import config as C, data as D
from views import common

st.title("Review & Decisions")
st.caption("Use during the accountable body's review. Each save is added to the decision log in the database "
           "with a timestamp, recorder, and meeting name; history is never overwritten. Export the log to attach "
           "to meeting minutes, or download the full Strategy Progress Report on the Core Inquiry 3 Evidence page.")

m = common.current_matrix()
strat = D.strategies(m)

meta1, meta2 = st.columns(2)
reviewer = meta1.text_input("Recorded by", placeholder="Name")
meeting = meta2.text_input("Meeting", placeholder="e.g., SFF Review – Feb 2027")

levers = common.lever_filter("review_lever")
# evidence beside each rating: linked-KPI trend, measure ratings, activity completion
res, _ = common.kpi_results()
summ = D.kpi_summary(res, list(D.kpis(m)["code"]), D.load_kpi_targets(m)).set_index("kpi_code")["trend"]
links = D.load_strategy_kpis()
meas = D.latest_measures(D.load_measure_results()).set_index("code")
fy = common.fiscal_years()[-1]
reqs = D.with_activity_status(D.all_activities(common.requests()), D.load_activity_status())
comp = D.activity_completion(reqs[reqs["fiscal_year"] == fy]).set_index("strategy")

edit = strat[strat["lever"].isin(levers)][["code", "element", "status", "decision"]].copy()
edit["decision"] = edit["decision"].fillna("")
edit["kpis"] = edit["code"].map(lambda c: (lambda ks: f"{int((summ.reindex(ks) == 'Improving').sum())}/{len(ks)} improving"
                                           if ks else "process")(list(links.loc[links.strategy == c, "kpi_code"])))
edit["happening"] = edit["code"].map(meas["impl_rating"] if "impl_rating" in meas else {}).fillna("—")
edit["working"] = edit["code"].map(meas["eff_rating"] if "eff_rating" in meas else {}).fillna("—")
def _acts(c):
    if c not in comp.index:
        return "none funded"
    r = comp.loc[c]
    txt = f"{int(r['completed'])}/{int(r['activities'])} done"
    return txt + (f" · {int(r['met'])}/{int(r['rated'])} met expected" if r["rated"] else " · results not rated")


edit["activities"] = edit["code"].map(_acts)
edit = edit[["code", "element", "kpis", "happening", "working", "activities", "status", "decision"]]
st.caption(f"Evidence columns: linked KPI trends, latest measure ratings, and {fy} activities (completed, and how "
           "many met their expected result). "
           "Rate each strategy and record the decision and rationale.")

edited = st.data_editor(
    edit, hide_index=True, width="stretch", key="review_editor",
    disabled=["code", "element", "kpis", "happening", "working", "activities"],
    column_config={
        "code": "Code",
        "element": st.column_config.TextColumn("Strategy", width="large"),
        "kpis": "Linked KPIs", "happening": "Is it happening?", "working": "Is it working?",
        "activities": f"{fy} activities",
        "status": st.column_config.SelectboxColumn("Status", options=C.STATUSES, required=True),
        "decision": st.column_config.TextColumn("Decision & rationale", width="large"),
    },
)

changed = edited[["code", "status", "decision"]].merge(edit[["code", "status", "decision"]], on="code", suffixes=("", "_old"))
changed = changed[(changed["status"] != changed["status_old"]) | (changed["decision"] != changed["decision_old"])]
st.write(f"{len(changed)} change(s) pending.")

if st.button("Save ratings", type="primary", disabled=changed.empty or not reviewer or not meeting):
    n = D.append_reviews(changed[["code", "status", "decision"]], reviewer, meeting)
    st.success(f"Saved {n} rating(s).")
    st.rerun()
if not (reviewer and meeting):
    st.caption("Enter *Recorded by* and *Meeting* to enable saving.")

st.subheader("Decision log")
log = common.reviews()
if log.empty:
    st.info("No ratings saved yet.")
else:
    st.dataframe(log.sort_values("timestamp", ascending=False), hide_index=True, width="stretch")
    st.download_button("Download decision log (CSV)", log.to_csv(index=False), "sff_decision_log.csv", "text/csv")
