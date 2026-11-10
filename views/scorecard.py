import pandas as pd
import streamlit as st

from sff import config as C, data as D
from views import common

st.title("Lever Scorecard")
st.caption("Each lever is judged by its KPIs (are they moving?) and its strategies (are they rated on track, and "
           "is the funded work getting done?).")

m = common.current_matrix()
k = D.kpis(m)
strat = D.strategies(m)
res, is_sample = common.kpi_results()
if is_sample:
    common.sample_banner()

targets = D.load_kpi_targets(m)
summ = D.kpi_summary(res, list(k["code"]), targets).merge(
    k[["code", "element", "indicator_type", "lever"]], left_on="kpi_code", right_on="code", how="left")

req = D.with_activity_status(D.all_activities(common.requests()), D.load_activity_status())
latest_fy = common.fiscal_years()[-1]
comp = D.activity_completion(req[req["fiscal_year"] == latest_fy]).set_index("strategy")
meas = D.latest_measures(D.load_measure_results()).set_index("code")

TREND = {"Improving": "● Improving", "Flat": "▲ Flat", "Declining": "■ Declining", "No data": "○ No data"}

# ---------------------------------------------------------------- lever tiles
cols = st.columns(4)
for col, (L, name) in zip(cols, C.LEVERS.items()):
    ks = summ[summ["lever"] == L]
    ss = strat[strat["lever"] == L]
    with col.container(border=True):
        st.markdown(f"**{L}. {name}**")
        n_data = int((ks["trend"] != "No data").sum())
        st.metric("KPIs improving", f"{int((ks['trend'] == 'Improving').sum())} of {n_data}" if n_data else "No data")
        st.metric("Strategies rated on track", f"{int((ss['status'] == 'On track').sum())} of {len(ss)}")
        acts = comp.reindex(ss["code"]).fillna(0)
        total = int(acts["activities"].sum())
        st.metric(f"{latest_fy} activities completed", f"{int(acts['completed'].sum())} of {total}" if total else "None funded")
        n_rated = int(acts["rated"].sum())
        st.metric("Activities that met expected result", f"{int(acts['met'].sum())} of {n_rated} rated" if n_rated else "None yet")

st.caption(f"KPI trend rule: average annual change of at least +{D.TREND_THRESHOLD * 100:.1f} pts = Improving; "
           f"at or below -{D.TREND_THRESHOLD * 100:.1f} pts = Declining; otherwise Flat. "
           "Once targets are set, 'vs. target' shows whether the latest result meets it.")

# ---------------------------------------------------------------- KPI detail
st.subheader("KPIs by lever")
levers = common.lever_filter("sc_lever")
view = summ[summ["lever"].isin(levers)].copy()
view["trend"] = view["trend"].map(TREND)
view[["annual_change", "largest_gap"]] = view[["annual_change", "largest_gap"]] * 100
view["lever_name"] = view["lever"].map(lambda x: f"{x}. {C.LEVERS[x]}")
st.dataframe(
    view[["lever_name", "kpi_code", "element", "indicator_type", "latest_year", "latest", "annual_change",
          "trend", "target", "vs_target", "largest_gap", "largest_gap_group"]],
    hide_index=True, width="stretch",
    column_config={
        "lever_name": "Lever", "kpi_code": "KPI", "element": st.column_config.TextColumn("Indicator", width="large"),
        "indicator_type": "Type", "latest_year": "Latest year",
        "latest": st.column_config.NumberColumn("Latest (all)", format="percent"),
        "annual_change": st.column_config.NumberColumn("Change / yr (pts)", format="%+.1f"),
        "trend": "Trend",
        "target": st.column_config.NumberColumn("Target", format="percent"),
        "vs_target": "vs. target",
        "largest_gap": st.column_config.NumberColumn("Largest gap (pts)", format="%+.1f"),
        "largest_gap_group": "Group with largest gap",
    },
)

# ---------------------------------------------------------------- strategy roll-up
st.subheader("Strategies by lever")
s = strat[strat["lever"].isin(levers)][["code", "element", "lever", "status"]].copy()
s = s.join(comp, on="code").join(meas, on="code")
s["status"] = s["status"].map(common.status_badge)
links = D.load_strategy_kpis()
trend_by_kpi = summ.set_index("kpi_code")["trend"]
s["linked_kpis_improving"] = s["code"].map(
    lambda c: (lambda ks: f"{int((trend_by_kpi.reindex(ks) == 'Improving').sum())} of {len(ks)}" if ks else "—")(
        list(links.loc[links["strategy"] == c, "kpi_code"])))
st.dataframe(
    s.reindex(columns=["code", "element", "status", "linked_kpis_improving", "impl_rating", "eff_rating",
                       "activities", "completed", "pct_completed", "with_expected", "rated", "pct_met"]),
    hide_index=True, width="stretch",
    column_config={
        "code": "Code", "element": st.column_config.TextColumn("Strategy", width="large"), "status": "Status",
        "linked_kpis_improving": "Linked KPIs improving",
        "impl_rating": "Is it happening?", "eff_rating": "Is it working?",
        "activities": st.column_config.NumberColumn(f"{latest_fy} activities", format="%d"),
        "completed": st.column_config.NumberColumn("Completed", format="%d"),
        "pct_completed": st.column_config.ProgressColumn("% complete", format="percent", min_value=0, max_value=1),
        "with_expected": st.column_config.NumberColumn("With expected result", format="%d"),
        "rated": st.column_config.NumberColumn("Results rated", format="%d"),
        "pct_met": st.column_config.ProgressColumn("% met expected", format="percent", min_value=0, max_value=1,
                                                   help="Activities rated Met ÷ activities rated Met, Partially met or Not met."),
    },
)

# ---------------------------------------------------------------- targets
with st.expander("Set or update a KPI target"):
    st.caption("Targets entered here are logged with who set them and when; the latest one is used.")
    t1, t2, t3, t4 = st.columns([3, 1, 1, 2])
    opts = {f"{r.code} – {r.element}": r.code for r in k.itertuples()}
    kc = opts[t1.selectbox("KPI", list(opts), key="tgt_kpi")]
    tv = t2.number_input("Target (%)", min_value=0.0, max_value=100.0, step=0.5, key="tgt_val")
    ty = t3.text_input("By year", value=C.GOAL_TARGET_YEAR, key="tgt_year")
    who = t4.text_input("Set by", key="tgt_who")
    if st.button("Save target", disabled=not who):
        D.save_kpi_target(kc, tv / 100, ty, who)
        st.success(f"Target for {kc} set to {tv:.1f}%.")
        st.rerun()
