import pandas as pd
import streamlit as st

from sff import charts, config as C, data as D
from views import common

st.title("Goal: 50% Five-Year Completion by 2029")
st.caption("The SFF sets the completion goal for every racial/ethnic group, so progress is shown by group. "
           "The dotted line is the straight-line path from the 29% baseline (2023-24) to 50% (2028-29).")

res, is_sample = common.kpi_results()
common.kpi_source_note(is_sample)

# ---------------------------------------------------------- the goal cohort's early signals
_gf = int(C.GOAL_TARGET_YEAR[:4]) - 4            # 2028-29 window closes -> entered Fall 2024
GOAL_COHORT = f"{_gf}-{str(_gf + 1)[2:]}"
SIGNALS = [("CMP-TD", "5-yr completion to date"), ("B-K7", "Persisted fall→spring"), ("B-K8", "Retained to 2nd fall"), ("B-K9", "Retained to 2nd spring"),
           ("B-K6", "Transfer-level math & English, yr 1"), ("B-K2", "15+ units completed, yr 1"),
           ("B-K4", "30+ units completed, yr 2"), ("B-K10", "Completed within 2 years")]


def goal_cohort_signals():
    st.subheader(f"The goal cohort: students who entered Fall {GOAL_COHORT[:4]}")
    st.caption(f"The 2029 goal is about this cohort — it reaches five years in spring 2029. Until then, these "
               "early measures show whether it is on track. Each is the share of the whole entering cohort.")
    g = res[(res["year"] == GOAL_COHORT) & res["kpi_code"].isin([c for c, _ in SIGNALS])]
    if g.empty:
        st.info(f"No results yet for the Fall {GOAL_COHORT[:4]} cohort.")
        return
    td = g[(g["kpi_code"] == "CMP-TD") & (g["group"] == "All students")]
    if not td.empty:
        n, N, v = int(td["numerator"].iloc[0]), int(td["denominator"].iloc[0]), float(td["value"].iloc[0])
        need = max(0, int(round(C.GOAL_TARGET * N)) - n)
        k1, k2, k3 = st.columns(3)
        k1.metric("5-year completion to date", f"{v:.1%}", f"{n:,} of {N:,} students", delta_color="off", delta_arrow="off",
                  help=f"Completers so far: students who earned a degree or a certificate, or completed 60+ degree-applicable "
                       f"units. All of them did it inside the five-year window, so this is the cohort's five-year rate so far; it rises until "
                       f"spring {int(GOAL_COHORT[:4]) + 5}.")
        k2.metric("Goal at five years", f"{C.GOAL_TARGET:.0%}", f"{int(round(C.GOAL_TARGET * N)):,} students", delta_color="off", delta_arrow="off")
        k3.metric(f"Still needed by spring {int(GOAL_COHORT[:4]) + 5}", f"{need:,}", "more completers", delta_color="off", delta_arrow="off")
        st.plotly_chart(charts.goal_progress(C.GOAL_BASELINE, C.GOAL_TARGET, v, f"Fall {GOAL_COHORT[:4]} cohort, to date"),
                        width="stretch")
    tbl = g.pivot(index="group", columns="kpi_code", values="value")
    tbl = tbl.reindex(index=common.group_order(tbl.index), columns=[c for c, _ in SIGNALS if c in tbl.columns])
    n = g[g["kpi_code"] == "CMP-TD"].set_index("group")["denominator"]
    tbl.insert(0, "Students", pd.to_numeric(n, errors="coerce").reindex(tbl.index))
    tbl = tbl.rename(columns=dict(SIGNALS))
    st.dataframe(tbl.style.format({c: "{:.1%}" for c in tbl.columns if c != "Students"} | {"Students": "{:,.0f}"},
                                  na_rep="—"), width="stretch")
    st.caption("Race/ethnicity groups shown; other breakdowns (Pell, Cerritos Complete, gender, age, HS GPA) are on "
               "the **KPIs** page.")


pace = D.goal_pace(res)
if pace.empty:
    goal_cohort_signals()
    st.info("**The Fall 2024 cohort's five-year completion is in progress: 2 of its 5 years have passed.** "
               "The rate above counts every completer so far and is final in spring 2029. To compare with the "
               "29% baseline and show the trend toward 50%, ask "
               "IERPG for five-year completion rates (overall and by race/ethnicity) for the **Fall 2015 – Fall 2021** "
               "cohorts. Aggregated rates are enough — no student records needed. Save them as "
               "`data/source/kpi_results.csv` rows with `kpi_code = GOAL`.")
    st.stop()

allst = pace[pace["group"] == "All students"].iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"All students ({allst['latest_year']})", f"{allst['latest']:.1%}",
          f"{(allst['latest'] - C.GOAL_BASELINE) * 100:+.1f} pts vs. 29% baseline")
c2.metric("Gap to 50%", f"{allst['gap_to_goal'] * 100:.1f} pts")
c3.metric("Needed per year", f"{allst['needed_per_year'] * 100:+.1f} pts",
          help=f"{allst['years_left']} reporting year(s) left before {C.GOAL_TARGET_YEAR}.")
c4.metric("Observed per year", f"{allst['observed_per_year'] * 100:+.1f} pts",
          help="Average annual change across the years loaded.")

groups_avail = list(pace["group"])
groups = st.multiselect("Student groups", groups_avail,
                        default=[g for g in ["All students", "African American", "Hispanic/Latino"] if g in groups_avail])
st.plotly_chart(charts.goal_by_group(res, groups), width="stretch")

st.subheader("Pace by student group")
PACE_ICON = {"Goal met": "● Goal met", "On pace": "● On pace", "Behind pace": "▲ Behind pace"}
tbl = pace.assign(on_pace=pace["on_pace"].map(PACE_ICON))
st.dataframe(
    tbl[["group", "latest_year", "latest", "gap_to_goal", "needed_per_year", "observed_per_year", "on_pace"]],
    hide_index=True, width="stretch",
    column_config={
        "group": "Student group", "latest_year": "Latest year",
        "latest": st.column_config.NumberColumn("5-yr completion", format="percent"),
        "gap_to_goal": st.column_config.NumberColumn("Gap to 50%", format="percent"),
        "needed_per_year": st.column_config.NumberColumn("Needed / yr", format="percent"),
        "observed_per_year": st.column_config.NumberColumn("Observed / yr", format="percent"),
        "on_pace": "Pace",
    },
)
goal_cohort_signals()
st.caption("Pace compares the average annual change so far with the annual gain needed to reach 50% by the "
           f"{C.GOAL_TARGET_YEAR} reporting year. Because the fall 2024 cohort's five-year result arrives only in 2029, "
           "the leading KPIs on the **Lever Scorecard** are the earlier signal of whether the college is on track.")
