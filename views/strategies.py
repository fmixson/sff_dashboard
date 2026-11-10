import streamlit as st

from sff import charts, config as C, data as D
from views import common

st.title("Strategy Detail")

m = common.current_matrix()
strat = D.strategies(m)
req = common.requests()

f1, f2, f3 = st.columns(3)
with f1:
    levers = common.lever_filter("strat_lever")
with f2:
    leads = st.multiselect("Lead area", sorted(strat["lead"].dropna().unique()))
with f3:
    statuses = st.multiselect("Status", C.STATUSES)

view = strat[strat["lever"].isin(levers)]
if leads:
    view = view[view["lead"].isin(leads)]
if statuses:
    view = view[view["status"].isin(statuses)]

if view.empty:
    st.info("No strategies match these filters.")
    st.stop()

options = {f"{r.code} – {r.element}": r.code for r in view.itertuples()}
code = options[st.selectbox("Strategy", list(options))]
s = view[view["code"] == code].iloc[0]

st.markdown(f"### {code} · {C.LEVERS[code[0]]}")
st.markdown(f"**{s['element']}**")
years = common.fiscal_years()
cols = st.columns(1 + len(years))
cols[0].metric("Status", common.status_badge(s["status"]))
for col, fy in zip(cols[1:], years):
    r = req[(req["fiscal_year"] == fy) & (req["strategy"] == code)]
    by_area = r.groupby("area").size()
    col.metric(f"{fy} requests (all loaded areas)", f"{len(r)} · ${r['cost'].sum():,.0f}",
               help=", ".join(f"{a}: {n}" for a, n in by_area.items()) or "None")

with st.container(border=True):
    st.markdown(f"**Assessment question:** {s['question']}")
    x, y = st.columns(2)
    x.markdown(f"**Is it happening?**  \n{s['implementation_measure']}")
    y.markdown(f"**Is it working?**  \n{s['effectiveness_measure']}")
    st.markdown(f"**Linked KPIs:** {s['linked_kpis']}  ·  **Lead:** {s['lead']}  ·  "
                f"**Disaggregate:** {s['disaggregate']}")
    st.markdown(f"**Reviewing body:** {s['reviewing_body']}  \n**Timing:** {s['review_timing']}")
    if isinstance(s["notes"], str) and s["notes"]:
        st.caption(s["notes"])

# ------------------------------------------------------------ 1. linked KPIs
st.subheader("Linked KPIs")
links = D.load_strategy_kpis()
linked = list(links.loc[links["strategy"] == code, "kpi_code"])
res, is_sample = common.kpi_results()
if not linked:
    st.info("No KPIs are linked to this strategy (it is a process strategy).")
else:
    if is_sample:
        st.caption("⚠️ KPI values are SAMPLE data until IERPG results are loaded.")
    tmap = D.load_kpi_targets(m).set_index("kpi_code")["target"]
    names = m.set_index("code")["element"]
    for i in range(0, len(linked), 3):
        row = st.columns(3)
        for col, kc in zip(row, linked[i:i + 3]):
            col.plotly_chart(charts.kpi_small(res, kc, names.get(kc, kc), tmap.get(kc)),
                             width="stretch", key=f"spark_{code}_{kc}")
    summ = D.kpi_summary(res, linked, D.load_kpi_targets(m))
    if "annual_change" in summ:
        summ[["annual_change", "largest_gap"]] = summ[["annual_change", "largest_gap"]] * 100
    if not summ.empty and "latest" in summ:
        st.dataframe(summ[["kpi_code", "latest_year", "latest", "annual_change", "trend", "target", "vs_target",
                           "largest_gap", "largest_gap_group"]],
                     hide_index=True, width="stretch",
                     column_config={"kpi_code": "KPI", "latest_year": "Latest year",
                                    "latest": st.column_config.NumberColumn("Latest (all)", format="percent"),
                                    "annual_change": st.column_config.NumberColumn("Change / yr (pts)", format="%+.1f"),
                                    "trend": "Trend", "target": st.column_config.NumberColumn("Target", format="percent"),
                                    "vs_target": "vs. target",
                                    "largest_gap": st.column_config.NumberColumn("Largest gap (pts)", format="%+.1f"),
                                    "largest_gap_group": "Group"})

# ------------------------------------------------------------ 2. measure results
st.subheader("Measure results")
mr = D.load_measure_results()
mine = mr[mr["code"] == code]
if mine.empty:
    st.info("No measure results recorded yet.")
else:
    st.dataframe(mine.sort_values("timestamp", ascending=False).drop(columns="code"), hide_index=True,
                 width="stretch",
                 column_config={"timestamp": "Recorded", "period": "Period", "measure_type": "Measure",
                                "result": st.column_config.TextColumn("Result", width="large"),
                                "rating": "Rating", "entered_by": "Entered by"})
with st.expander("Record measure results for this strategy"):
    with st.form(f"measures_{code}", clear_on_submit=True):
        p1, p2 = st.columns(2)
        period = p1.text_input("Period", placeholder="e.g., 2026-27 or Spring 2027")
        who = p2.text_input("Entered by")
        i1, i2 = st.columns([3, 1])
        impl = i1.text_area(f"Is it happening? — {s['implementation_measure']}", height=80)
        impl_r = i2.selectbox("Rating", D.MEASURE_RATINGS, index=3, key=f"ir_{code}")
        e1, e2 = st.columns([3, 1])
        eff = e1.text_area(f"Is it working? — {s['effectiveness_measure']}", height=80)
        eff_r = e2.selectbox("Rating", D.MEASURE_RATINGS, index=3, key=f"er_{code}")
        if st.form_submit_button("Save measure results", type="primary"):
            if not (period and who):
                st.error("Enter the period and your name.")
            else:
                D.append_measure_results(code, period, [("Implementation", impl, impl_r),
                                                        ("Effectiveness", eff, eff_r)], who)
                st.success("Saved.")
                st.rerun()

# ------------------------------------------------------------ 3. activities + status
st.subheader("Activities")
common.approved_note()
st.caption("Activities that aren't part of resource allocation can be added on the **Add Activities** page.")
g1, g2 = st.columns(2)
with g1:
    fys = common.fy_filter("strat_fy")
with g2:
    areas = common.area_filter("strat_area")
allacts = D.with_activity_status(D.all_activities(req), D.load_activity_status())
acts = allacts[(allacts["strategy"] == code) & allacts["fiscal_year"].isin(fys) & allacts["area"].isin(areas)]
acts = acts.sort_values(["activity_type", "fiscal_year", "area", "division"])
mine = req[(req["strategy"] == code) & req["fiscal_year"].isin(fys) & req["area"].isin(areas)]
pending = mine[~mine["approved"]]
common.activity_status_editor(acts, key=f"acts_{code}")
if not pending.empty:
    st.caption(f"{len(pending)} more request(s) mapped to {code} are awaiting VP/area approval "
               f"(${pending['cost'].sum():,.0f}); they appear here once approved on the **VP Approvals** page.")
sec = req[req["secondary"] == code]
if not sec.empty:
    st.caption(f"{len(sec)} more request(s) list {code} as a secondary strategy.")
