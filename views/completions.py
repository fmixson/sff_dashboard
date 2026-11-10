"""Students who have already completed: degrees and certificates by entering cohort (aggregates only)."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sff import config as C, data as D
from views import common

st.title("Completers")
st.caption("A **completer** earned a degree, a certificate or a GE pattern certification (CSU GE, IGETC or Cal-GETC), "
           "or completed 60+ degree-applicable units. Counts are "
           "students in each entering fall cohort who have done so, as of the IERPG file date. Counts only: no student "
           "names or records are stored in the dashboard.")

res, is_sample = common.kpi_results()
common.kpi_source_note(is_sample)
CODES = {"CMP-TD": "Completers", "CMP-DEG": "Degree", "CMP-CERT": "Certificate (no degree)",
         "CMP-GE": "GE certification only", "CMP-U60": "60+ units (no award)", "CMP-ADT": "Earned an ADT (AA-T/AS-T)"}
CATS = [("CMP-DEG", "Degree", "#2a78d6"), ("CMP-CERT", "Certificate (no degree)", "#eb6834"),
        ("CMP-GE", "GE certification only", "#8a5cd1"), ("CMP-U60", "60+ units, no award", "#1baf7a")]

allst = res[res["kpi_code"].isin(CODES) & (res["group"] == "All students")]
if allst.empty or "CMP-U60" not in set(allst["kpi_code"]):
    st.info("Completer details are not loaded yet. Rerun `python -m tools.build_db`, then restart the dashboard.")
    st.stop()

years = sorted(allst["year"].unique())
label = lambda y: f"Fall {y[:4]}" + (" (goal cohort)" if y == D.GOAL_COHORT else "")
year = st.selectbox("Entering cohort", years, index=years.index(D.GOAL_COHORT) if D.GOAL_COHORT in years else 0,
                    format_func=label)
cur = allst[allst["year"] == year].set_index("kpi_code")


def _m(code):
    r = cur.loc[code]
    return int(r["numerator"]), int(r["denominator"]), float(r["value"])


n, N, v = _m("CMP-TD")
k1, k2, k3, k5, k4 = st.columns(5)
k1.metric("Completers", f"{n:,}", f"{v:.1%} of {N:,} entering students", delta_color="off", delta_arrow="off")
dn, _, dv = _m("CMP-DEG")
an, _, av = _m("CMP-ADT")
k2.metric("Earned a degree", f"{dn:,}", f"{an:,} earned an ADT", delta_color="off", delta_arrow="off",
          help="AA, AS, AA-T or AS-T. Many degree earners also earned certificates.")
cn, _, cv = _m("CMP-CERT")
k3.metric("Certificate, no degree (yet)", f"{cn:,}", f"{cv:.1%} of cohort", delta_color="off", delta_arrow="off")
gn, _, gv = (_m("CMP-GE") if "CMP-GE" in cur.index else (0, 0, 0.0))
k5.metric("GE certification only", f"{gn:,}", f"{gv:.1%} of cohort", delta_color="off", delta_arrow="off",
          help="CSU GE, IGETC or Cal-GETC certification, without a degree or certificate.")
un, _, uv = _m("CMP-U60")
k4.metric("60+ units, no award", f"{un:,}", f"{uv:.1%} of cohort", delta_color="off", delta_arrow="off",
          help="Completed 60 or more degree-applicable units but has not (yet) earned any award.")

# ------------------------------------------------------------ completers by cohort (stacked: the parts add to the total)
fig = go.Figure()
for code, name, color in CATS:
    d = allst[allst["kpi_code"] == code].set_index("year").reindex(years)
    fig.add_bar(y=[label(y) for y in years], x=d["numerator"], name=name, orientation="h", marker_color=color,
                text=d["numerator"].map(lambda x: f"{int(x):,}" if pd.notna(x) and x >= 10 else ""),
                textposition="inside", hovertemplate="%{y}: %{x:,} students<extra>" + name + "</extra>")
fig.update_layout(barmode="stack", height=90 + 60 * len(years), margin=dict(l=10, r=10, t=30, b=10),
                  legend=dict(orientation="h", y=1.15, x=0), xaxis_title="Students who have completed",
                  yaxis=dict(autorange="reversed"))
st.subheader("Completers by entering cohort")
st.plotly_chart(fig, width="stretch")
st.caption("Each student is counted once: degree first, then certificate, then GE certification, then 60+ units. "
           "Younger cohorts have had less time.")

# ------------------------------------------------------------ awards earned
aw = D.load_award_counts()
aw = aw[aw["year"] == year]
if not aw.empty:
    st.subheader(f"Awards earned by the {label(year)} cohort")
    left, right = st.columns([2, 3])
    with left:
        t = aw.groupby("award_type", as_index=False)["students"].sum().sort_values("students", ascending=False)
        st.dataframe(t.rename(columns={"award_type": "Award type", "students": "Awards earned"}), hide_index=True,
                     width="stretch")
        st.caption("A student who earned several awards counts once in each.")
    with right:
        p = aw.sort_values(["students"], ascending=False)
        st.dataframe(p.rename(columns={"award": "Award (program code)", "award_type": "Type", "students": "Students"})
                     [["Award (program code)", "Type", "Students"]], hide_index=True, width="stretch", height=320)
        st.caption(f"Awards earned by fewer than {C.MIN_CELL_SIZE} students in the cohort are combined.")

# ------------------------------------------------------------ by student group
st.subheader("By student group")
dims = D.kpi_dimensions() or ["Race/ethnicity"]
dim = st.selectbox("Disaggregate by", dims)
g, _ = common.kpi_results(dim)
g = g[g["kpi_code"].isin(CODES) & (g["year"] == year)]
if g.empty:
    st.info("No group results for this cohort.")
else:
    tbl = g.pivot(index="group", columns="kpi_code", values="value")
    tbl = tbl.reindex(index=common.group_order(tbl.index, dim), columns=[c for c in CODES if c in tbl.columns])
    nn = g[g["kpi_code"] == "CMP-TD"].set_index("group")
    tbl.insert(0, "Completed (n)", pd.to_numeric(nn["numerator"], errors="coerce").reindex(tbl.index))
    tbl.insert(0, "Students", pd.to_numeric(nn["denominator"], errors="coerce").reindex(tbl.index))
    tbl = tbl.rename(columns=CODES)
    st.dataframe(tbl.style.format({c: "{:.1%}" for c in CODES.values()} | {"Students": "{:,.0f}", "Completed (n)": "{:,.0f}"},
                                  na_rep="—"), width="stretch")
    st.caption(f"Shares of each group's entering students. Groups under {C.MIN_CELL_SIZE} students are suppressed.")
