import pandas as pd
import streamlit as st

from sff import charts, config as C, data as D
from views import common

st.title("Key Performance Indicators")

m = common.current_matrix()
k = D.kpis(m)
dims = D.kpi_dimensions() or ["Race/ethnicity"]
f1, f2 = st.columns([1, 2])
with f1:
    dim = st.selectbox("Disaggregate by", dims, help="Race/ethnicity is the SFF's equity commitment; other "
                       "breakdowns help ACE and program leads see where gaps are.")
res, is_sample = common.kpi_results(dim)
common.kpi_source_note(is_sample)

with f2:
    levers = common.lever_filter("kpi_lever")
k = k[k["lever"].isin(levers)]
options = {f"{r.code} – {r.element}": r.code for r in k.itertuples()}
code = options[st.selectbox("KPI", list(options))]
row = k[k["code"] == code].iloc[0]

st.caption(f"{row['indicator_type']} indicator · Source: {row['data_source']} · "
           f"Reviewed: {row['review_timing']}")

r = res[res["kpi_code"] == code]
if r.empty:
    st.info("No results loaded for this KPI yet (financial/HR KPIs come from Fiscal Services and HR).")
    st.stop()

groups_avail = common.group_order(r["group"].unique(), dim)
groups = st.multiselect("Student groups", groups_avail, default=groups_avail[:4])
st.plotly_chart(charts.kpi_trend(r, groups, row["target"], order=groups_avail), width="stretch")
if r["year"].nunique() == 1:
    st.caption("Only one cohort has had enough time for this measure so far, so there is no trend yet.")

# Equity gap table for the latest year (table view doubles as the accessible alternative)
latest = r["year"].max()
snap = r[r["year"] == latest].set_index("group")["value"]
if "All students" in snap:
    nn = r[r["year"] == latest].set_index("group")["denominator"]
    gap = pd.DataFrame({
        "Result": snap,
        "Gap vs. all students (pts)": (snap - snap["All students"]) * 100,
        "Students (n)": pd.to_numeric(nn, errors="coerce"),
    }).reindex(groups_avail)
    st.subheader(f"Gaps by {dim}, {latest} cohort")
    st.dataframe(gap.style.format({"Result": "{:.1%}", "Gap vs. all students (pts)": "{:+.1f}",
                                   "Students (n)": "{:,.0f}"}, na_rep="—"), width="stretch")

with st.expander("Data table"):
    st.dataframe(r.pivot(index="year", columns="group", values="value").reindex(columns=groups_avail)
                 .style.format("{:.1%}"), width="stretch")
