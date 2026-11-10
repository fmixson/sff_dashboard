import streamlit as st

from sff import charts, data as D
from views import common

st.title("Resource Alignment")
st.caption("Area resource requests by primary SFF strategy. Add another area or year by placing its file in "
           "`data/source/`, registering it in `sff/config.py`, and rerunning `python -m tools.build_db`.")

m = common.current_matrix()
strat = D.strategies(m)
codes = list(strat["code"])
req_all = common.requests()

f1, f2 = st.columns(2)
with f1:
    areas = common.area_filter("res_area")
with f2:
    years = common.fy_filter("res_fy")
req = req_all[req_all["fiscal_year"].isin(years) & req_all["area"].isin(areas)]
if req.empty:
    st.info("No requests for the selected area(s) and year(s).")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Requests", len(req))
c2.metric("Requested $ (numeric)", f"${req['cost'].sum():,.0f}")
c3.metric("Requests with text costs", int(req["cost_is_text"].sum()),
          help="E.g., 'TBD', 'Unknown', ranges, shared estimates, or salary grades. Not included in $ totals.")
c4.metric("Area-approved $", f"${req.loc[req['approved'], 'cost'].sum():,.0f}",
          help="Requests marked Approved by the area VP/President in the source workbook.")

coverage = req.groupby(["fiscal_year", "area"]).size().rename("requests").reset_index()
st.caption("Loaded: " + " · ".join(f"{r.area} {r.fiscal_year} ({r.requests})" for r in coverage.itertuples()))

tab1, tab2, tab3, tab4 = st.tabs(["By strategy", "By area", "Year over year", "How strategies were assigned"])
with tab1:
    metric = st.radio("Show", ["requested", "approved"], horizontal=True,
                      format_func=lambda x: "Requested $" if x == "requested" else "Approved $")
    by = D.dollars_by_strategy(req, codes)
    st.plotly_chart(charts.dollars_by_strategy(by, metric), width="stretch")
    j = by.merge(strat[["code", "element", "lead", "status"]], left_on="strategy", right_on="code", how="left")
    j = j[j["strategy"] != "None"]
    j["status"] = j["status"].map(common.status_badge)
    st.subheader("Funding vs. strategy status")
    st.dataframe(
        j[["strategy", "element", "lead", "status", "requests", "requested", "approved", "text_cost"]],
        hide_index=True, width="stretch",
        column_config={
            "strategy": "Code", "element": st.column_config.TextColumn("Strategy", width="large"),
            "lead": "Lead (proposed)", "status": "Status", "requests": "Requests",
            "requested": st.column_config.NumberColumn("Requested $", format="$%,.0f"),
            "approved": st.column_config.NumberColumn("Approved $", format="$%,.0f"),
            "text_cost": "Text-cost requests",
        },
    )
with tab2:
    fy_cmp = st.selectbox("Compare areas within", sorted(years, reverse=True), key="area_cmp_fy")
    req_fy = req[req["fiscal_year"] == fy_cmp]
    sel_areas = [a for a in common.areas() if a in set(req_fy["area"])]
    if len(sel_areas) < 2:
        st.info(f"Only one area is loaded for {fy_cmp}. Select a year with two or more areas.")
    else:
        ya = D.dollars_by_strategy_and(req_fy, codes, "area")
        st.plotly_chart(charts.dollars_by_area(ya, sel_areas), width="stretch")
        pivot = ya[ya["strategy"] != "None"].pivot(index="strategy", columns="area", values="requested")[sel_areas]
        pivot["Total"] = pivot.sum(axis=1)
        st.dataframe(pivot.style.format("${:,.0f}"), width="stretch")
        st.caption("Strategies with no requests from any selected area: " +
                   (", ".join(pivot.index[pivot["Total"] == 0]) or "none"))
with tab3:
    if len(years) < 2:
        st.info("Select two or more fiscal years to compare.")
    else:
        st.caption("Only areas loaded for every selected year give a like-for-like comparison.")
        yy = D.dollars_by_strategy_year(req, codes)
        st.plotly_chart(charts.dollars_by_year(yy, years), width="stretch")
        pivot = yy[yy["strategy"] != "None"].pivot(index="strategy", columns="fiscal_year", values="requested")
        pivot["Change $"] = pivot[years[-1]] - pivot[years[0]]
        st.dataframe(pivot.style.format("${:,.0f}"), width="stretch")
with tab4:
    st.markdown("Each request has one **primary** strategy. The source of that assignment is tracked so "
                "unreviewed assignments can be checked.")
    src = req.groupby(["fiscal_year", "area", "strategy_source"]).size().rename("requests").reset_index()
    st.dataframe(src, hide_index=True, width="stretch")
    st.caption("'Proposed' assignments came from the 11/2026 alignment review and await confirmation by each area. "
               "FY26 'Dept-selected (single)' assignments were not reviewed; in the FY27 review about a third "
               "of department selections changed.")
