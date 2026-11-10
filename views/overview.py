import streamlit as st

from sff import charts, config as C, data as D
from views import common

st.title("Students First Framework – Progress Overview")
st.caption("Prototype for the SFF accountable body. Goal: graduate 50% of students within five years by spring 2029.")

m = common.current_matrix()
strat = D.strategies(m)
codes = list(strat["code"])
kres, is_sample = common.kpi_results()
req = common.requests()
years = common.fiscal_years()
latest_fy = years[-1]

# --- headline tiles
grad = kres[(kres["kpi_code"] == "GOAL") & (kres["group"] == "All students")].sort_values("year")
current = float(grad["value"].iloc[-1]) if not grad.empty else None
# until a 5-year rate exists, track the goal cohort (entered Fall 2024) by its completions so far
_gf = int(C.GOAL_TARGET_YEAR[:4]) - 4
td = kres[(kres["kpi_code"] == "CMP-TD") & (kres["group"] == "All students") & (kres["year"] == f"{_gf}-{str(_gf + 1)[2:]}")]
so_far = None if td.empty else td.iloc[0]
rated = int((strat["status"] != "Not yet assessed").sum())
acts_all = D.all_activities(req)
by_latest = D.dollars_by_strategy(acts_all[acts_all["fiscal_year"] == latest_fy], codes)
no_acts = by_latest[(by_latest["strategy"] != "None") & (by_latest["requests"] == 0)]

c1, c2, c3, c4 = st.columns(4)
if current is not None:
    c1.metric("5-year completion (latest)", f"{current:.0%}", f"{(current - C.GOAL_BASELINE) * 100:+.0f} pts vs. baseline",
              help="SAMPLE value until IERPG data is loaded." if is_sample else None)
    c2.metric("Gap to 2029 goal", f"{(C.GOAL_TARGET - current) * 100:.0f} pts")
elif so_far is not None:
    n, N = int(so_far["numerator"]), int(so_far["denominator"])
    c1.metric("5-year completion to date", f"{so_far['value']:.1%}", f"{n:,} of {N:,} · Fall {_gf} cohort",
              delta_color="off", delta_arrow="off",
              help=f"Students in the goal cohort (entered Fall {_gf}) who have already earned a degree or certificate or completed 60+ degree-applicable units, "
                   f"as of {D.kpi_source().split('as of ')[-1].rstrip(')')}. This number keeps rising until the "
                   f"five-year window closes in spring {_gf + 5}; the goal is 50% of the cohort by then.")
    need = max(0, int(round(C.GOAL_TARGET * N)) - n)
    c2.metric("More completers needed for 50%", f"{need:,}", f"by spring {_gf + 5}", delta_color="off", delta_arrow="off")
else:
    c1.metric("5-year completion (latest)", "—")
    c2.metric("Gap to 2029 goal", "—")
c3.metric("Strategies rated", f"{rated} of {len(strat)}")
c4.metric(f"Strategies with no approved {latest_fy} activities", len(no_acts),
          help="Across all areas loaded for " + latest_fy + ": " + ", ".join(sorted(req.loc[req['fiscal_year'] == latest_fy, 'area'].unique())))
if is_sample:
    common.sample_banner()

if current is not None:
    st.plotly_chart(charts.goal_progress(C.GOAL_BASELINE, C.GOAL_TARGET, current), width="stretch")
elif so_far is not None:
    st.plotly_chart(charts.goal_progress(C.GOAL_BASELINE, C.GOAL_TARGET, float(so_far["value"]),
                                         f"Fall {_gf} cohort, to date"), width="stretch")
    st.caption(f"The 29% baseline and 50% goal are five-year rates. The Fall {_gf} cohort's five-year rate is in "
               f"progress: it counts every completer so far and will keep rising until the window closes in spring {_gf + 5}.")

left, right = st.columns([3, 2])
with left:
    st.subheader("Strategy status by lever")
    st.plotly_chart(charts.status_by_lever(strat), width="stretch")
with right:
    st.subheader("Needs attention")
    flagged = strat[strat["status"].isin(["Needs adjustment", "Replace"])]
    if flagged.empty:
        st.info("No strategies rated *Needs adjustment* or *Replace* yet. Ratings are entered on the **Review & Decisions** page.")
    else:
        st.dataframe(flagged[["code", "status", "decision"]], hide_index=True, width="stretch")
    if not no_acts.empty:
        st.markdown(f"**No approved {latest_fy} activities (any loaded area):** " + ", ".join(no_acts["strategy"]))

# --- all strategies, with requests per fiscal year (table view = accessible alternative)
st.subheader("All strategies")
tbl = strat[["code", "element", "lead", "status"]].copy()
tbl["status"] = tbl["status"].map(common.status_badge)
cfg = {"code": "Code", "element": st.column_config.TextColumn("Strategy", width="large"),
       "lead": "Lead (proposed)", "status": "Status"}
for fy in years:
    b = D.dollars_by_strategy(req[req["fiscal_year"] == fy], codes).set_index("strategy")
    tbl[f"{fy} #"] = tbl["code"].map(b["requests"])
    tbl[f"{fy} $"] = tbl["code"].map(b["requested"])
    cfg[f"{fy} $"] = st.column_config.NumberColumn(f"{fy} $", format="$%,.0f")
st.dataframe(tbl, hide_index=True, width="stretch", column_config=cfg)
loaded = req.groupby("fiscal_year")["area"].unique()
st.caption("Requests from loaded areas — " + "; ".join(f"{fy}: {', '.join(sorted(a))}" for fy, a in loaded.items())
           + ". $ includes numeric costs only.")
