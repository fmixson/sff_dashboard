"""Page 1: completers and the measures that lead to completion, in plain language."""
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from sff import config as C, data as D
from simple import theme as T
from views import common

BLUE, INK, MUTED = T.NAVY, T.INK, T.GRAY

res, is_sample = common.kpi_results()
if is_sample:
    common.sample_banner()

import re

as_of_m = re.search(r"(\d{4})-(\d{2})-(\d{2})", D.kpi_source() or "")
AS_OF = date(*map(int, as_of_m.groups())) if as_of_m else date.today()
cohorts = sorted(res.loc[res["kpi_code"] == "CMP-TD", "year"].unique())

# ---------------------------------------------------------------- top of the page (from the full dashboard's Overview)
from sff import charts


def overview_top():
    T.banner("Students First Framework – Progress Overview",
             "Cerritos College · Goal: 50% of students complete within five years by spring 2029")
    gf = int(C.GOAL_TARGET_YEAR[:4]) - 4
    gy = f"{gf}-{str(gf + 1)[2:]}"
    pick = lambda code: res[(res["kpi_code"] == code) & (res["group"] == "All students") & (res["year"] == gy)]
    t, enr, u45 = pick("CMP-TD"), pick("ENR-NOW"), pick("U45")
    c1, c2, c3, c4 = st.columns(4)
    if not t.empty:
        n_, N_, v_ = int(t["numerator"].iloc[0]), int(t["denominator"].iloc[0]), float(t["value"].iloc[0])
        c1.markdown(T.tile("5-year completion to date", f"{v_:.1%}", f"{n_:,} of {N_:,} · Fall {gf} cohort",
                           T.RED if v_ < C.GOAL_BASELINE else T.NAVY,
                           f"Students who started in Fall {gf} and have already earned a degree, a certificate or a GE "
                           f"pattern certification, or completed 60+ degree-applicable units. It keeps rising until "
                           f"spring {gf + 5}."),
                    unsafe_allow_html=True)
        c2.markdown(T.tile("More completers needed for 50%", f"{max(0, round(C.GOAL_TARGET * N_) - n_):,}",
                           f"by spring {gf + 5}"), unsafe_allow_html=True)
    if not enr.empty:
        c3.markdown(T.tile("Active this year", f"{int(enr['numerator'].iloc[0]):,}",
                           f"{enr['value'].iloc[0]:.0%} of the Fall {gf} cohort", T.NAVY,
                           f"Took classes in summer or fall {AS_OF.year}. IERPG's file has no fall enrollment flag, "
                           "so this counts students with new units this year."), unsafe_allow_html=True)
    if not u45.empty:
        c4.markdown(T.tile("Completed 45+ units", f"{int(u45['numerator'].iloc[0]):,}",
                           f"{u45['value'].iloc[0]:.0%} of the Fall {gf} cohort", T.NAVY,
                           "Completed 45 or more degree-applicable units so far, including those who have completed."),
                    unsafe_allow_html=True)
    if not t.empty:
        fig0 = charts.goal_progress(C.GOAL_BASELINE, C.GOAL_TARGET, v_, f"Fall {gf} cohort, to date")
        fig0.data[-1].marker.color = T.NAVY                     # match the KPI dashboard's navy
        for an in fig0.layout.annotations:
            if an.font and an.font.color == "#2a78d6":
                an.font.color = T.NAVY
        st.plotly_chart(fig0, width="stretch", config={"displayModeBar": False})
        st.caption(f"The 29% baseline and 50% goal are five-year rates. The Fall {gf} cohort's five-year rate is in "
                   f"progress: it counts every completer so far and will keep rising until spring {gf + 5}.")


overview_top()
T.banner("How our students are doing", "Our goal: half of our students complete within five years, for every student group")

if not cohorts or "CMP-U60" not in set(res["kpi_code"]):
    st.info("Completion results are not loaded yet. Run `python -m tools.build_db`, then restart this page.")
    st.stop()


def cohort_label(y):
    """Started Fall 2024 (2029 grads): the spring they reach five years."""
    return f"Started Fall {y[:4]} ({int(y[:4]) + 5} grads)"


cohort = st.segmented_control(
    "Which group of students?", cohorts, format_func=cohort_label, key="cohort",
    default=D.GOAL_COHORT if D.GOAL_COHORT in cohorts else cohorts[-1],
    help="Each group is the first-time students who started at Cerritos College that fall.") or D.GOAL_COHORT
fall = cohort[:4]
yrs_in = (AS_OF - date(int(fall), 8, 15)).days / 365.25
stage_txt = ("in their first term" if yrs_in < 0.5 else
             f"about {round(yrs_in)} year{'s' if round(yrs_in) != 1 else ''} into their five years")
td = res[(res["kpi_code"] == "CMP-TD") & (res["group"] == "All students") & (res["year"] == cohort)]
if td.empty:
    st.info(f"No completion results yet for students who started in Fall {fall}.")
    st.stop()

n, N, v = int(td["numerator"].iloc[0]), int(td["denominator"].iloc[0]), float(td["value"].iloc[0])
need = max(0, round(C.GOAL_TARGET * N) - n)
goal_pct = C.GOAL_TARGET * 100

# ---------------------------------------------------------------- the headline
with st.container(border=True):
    st.markdown(f"### {n:,} of the {N:,} students who started in Fall {fall} have completed so far.")
    st.caption(f"As of {AS_OF:%B} {AS_OF.day}, {AS_OF.year} these students are {stage_txt}. Their five-year mark is spring {int(fall) + 5}.")
    st.markdown(
        f"""
<div style="margin:6px 0 4px 0;font-size:15px;color:{MUTED}">That is <b style="color:{INK}">{v:.0%}</b>.
The goal is <b style="color:{INK}">{goal_pct:.0f}%</b> by spring {int(fall) + 5}.</div>
<div style="position:relative;height:30px;background:rgba(128,128,128,.16);border-radius:6px;margin:10px 0 26px 0">
  <div style="width:{v * 100:.1f}%;height:100%;background:{BLUE};border-radius:6px"></div>
  <div style="position:absolute;left:{goal_pct}%;top:-6px;height:42px;border-left:2px dashed {INK}"></div>
  <div style="position:absolute;left:{goal_pct}%;top:40px;transform:translateX(-50%);font-size:13px;color:{INK}">
    Goal {goal_pct:.0f}%</div>
  <div style="position:absolute;left:0;top:40px;font-size:13px;color:{MUTED}">0%</div>
  <div style="position:absolute;right:0;top:40px;font-size:13px;color:{MUTED}">100%</div>
</div>""", unsafe_allow_html=True)
    left = int(fall) + 5 - AS_OF.year
    st.markdown(f"To reach the goal, **{need:,} more** of these students need to complete in the next "
                f"{left} year{'s' if left != 1 else ''}.")

# ---------------------------------------------------------------- what counts
T.band(f"How the Fall {fall} group completed")
st.caption("A student counts once, by the first of these they reached.")
cur = res[(res["group"] == "All students") & (res["year"] == cohort)].set_index("kpi_code")
c1, c2, c3, c4 = st.columns(4)
for col, code, label, note in [
    (c1, "CMP-DEG", "Earned a degree", "Associate degree, including transfer degrees (AA-T / AS-T)"),
    (c2, "CMP-CERT", "Earned a certificate", "A certificate, without a degree so far"),
    (c3, "CMP-GE", "Earned a GE certification", "CSU GE, IGETC or Cal-GETC, without a degree or certificate so far"),
    (c4, "CMP-U60", "Completed 60 units", "60+ degree-applicable units, without an award so far"),
]:
    v = int(cur.loc[code, "numerator"]) if code in cur.index else 0
    col.markdown(T.tile(label, f"{v:,}", note), unsafe_allow_html=True)

# ---------------------------------------------------------------- by student group
T.band("Completion by student group")
st.caption(f"Share of each group's Fall {fall} students who have completed so far. The goal is {goal_pct:.0f}% for every group.")
g = res[(res["kpi_code"] == "CMP-TD") & (res["year"] == cohort) & (res["group"] != "All students")].copy()
g = g[pd.to_numeric(g["denominator"], errors="coerce") >= 30].sort_values("value")     # small groups swing too much
fig = go.Figure(go.Bar(
    x=g["value"], y=g["group"].replace({"Unknown": "Not reported"}), orientation="h", marker_color=BLUE, marker_line_width=0,
    text=[f"{x:.0%}" for x in g["value"]], textposition="outside", cliponaxis=False,
    customdata=g[["numerator", "denominator"]].astype(int).values,
    hovertemplate="%{y}: %{x:.1%} (%{customdata[0]:,} of %{customdata[1]:,} students)<extra></extra>"))
fig.add_vline(x=C.GOAL_TARGET, line_dash="dash", line_color=T.RED, line_width=2,
              annotation_text=f"Goal {goal_pct:.0f}%", annotation_position="top")
fig.update_layout(height=60 + 46 * len(g), margin=dict(l=10, r=40, t=30, b=30), bargap=0.35,
                  xaxis=dict(range=[0, 0.6], tickformat=".0%", showgrid=False, zeroline=False),
                  yaxis=dict(showgrid=False), plot_bgcolor="rgba(0,0,0,0)", showlegend=False)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
st.caption("Groups with fewer than 30 students are left off because their rates swing widely from year to year.")

# ---------------------------------------------------------------- the steps that lead to completion
T.banner("Key Performance Indicators (KPIs): The Steps that Lead to Completion", f"Shown for students who started in Fall {fall}")
st.markdown(f"Students who hit these early milestones are much more likely to finish. Shown for the Fall {fall} "
            "group; arrows compare it with the group that started a year earlier.")

STAGES = [
    ("Getting started", [
        ("A-K1", "Made an education plan in their first year"),
        ("A-K2", "Took a full load (15+ units) in their first fall"),
        ("A-K3", "Took 30+ units in their first year"),
        ("B-K2", "Earned 15+ units in their first year"),
    ]),
    ("Math, English and units", [
        ("B-K6", "Completed college-level math and English in their first year"),
        ("ENG-Y1", "Completed college-level English in their first year"),
        ("MATH-Y1", "Completed college-level math in their first year"),
        ("B-K4", "Completed 30+ units by the end of their second year"),
    ]),
    ("Staying enrolled", [
        ("B-K7", "Came back in spring after their first fall"),
        ("B-K8", "Came back for a second fall"),
        ("B-K9", "Still enrolled in their second spring"),
        ("B-K1", "Passed all of their first five classes"),
    ]),
    ("Completed so far (to date)", [
        ("MATH-TD", "Completed college-level math so far"),
        ("ENG-TD", "Completed college-level English so far"),
        ("EM-TD", "Completed both college-level math and English so far"),
    ]),
]
TO_DATE = {"MATH-TD", "ENG-TD", "EM-TD"}   # running totals: no "vs. the group before" (older groups had more time)
WHEN = {"A-K1": "after the first year", "A-K2": "after the first fall", "A-K3": "after the first year",
        "B-K2": "after the first year", "B-K6": "after the first year", "ENG-Y1": "after the first year",
        "MATH-Y1": "after the first year", "B-K4": "after the second year",
        "B-K7": "after the first spring", "B-K8": "in the second fall", "B-K9": "in the second spring",
        "B-K1": "after the first year"}
allst = res[res["group"] == "All students"]
GOOD, BAD = T.GREEN, T.RED
prev_cohort = cohorts[cohorts.index(cohort) - 1] if cohorts.index(cohort) > 0 else None


def value(code, y):
    d = allst[(allst["kpi_code"] == code) & (allst["year"] == y)]
    return d.iloc[0] if len(d) else None


def card(label, code):
    now = value(code, cohort)
    if now is None:
        return T.kpi_card(label, f"<div style='font-size:1.7rem;font-weight:800;color:{T.GRAY}'>Not yet</div>"
                                 f"<div style='font-size:0.85rem;color:{T.GRAY}'>Measured {WHEN[code]}. These students "
                                 "haven't reached that point.</div>", accent=T.GRAY, muted=True, min_h=220)
    before = value(code, prev_cohort) if prev_cohort and code not in TO_DATE else None
    pts = (now["value"] - before["value"]) * 100 if before is not None else None
    pill = T.trend_pill(pts, f"Fall {prev_cohort[:4]}") if pts is not None else ""
    if code in TO_DATE:
        pill = (f"<span style='font-size:0.82rem;color:{T.GRAY}'>As of {AS_OF:%B} {AS_OF.day}, {AS_OF.year}, "
                "including AP and prior credit</span>")
    body = (f"<div style='font-size:3rem;font-weight:800;line-height:1.1;color:{T.trend_color(pts)}'>{now['value']:.0%}</div>"
            f"<div style='font-size:0.85rem;color:{T.GRAY};margin:4px 0 10px 0'>{int(now['numerator']):,} of "
            f"{int(now['denominator']):,} students</div>{pill}")
    return T.kpi_card(label, body, accent=T.trend_color(pts), min_h=220)


for stage, items in STAGES:
    T.band(stage)
    cols = st.columns(4)
    for col, (code, label) in zip(cols, items):
        col.markdown(card(label, code), unsafe_allow_html=True)
    st.write("")
    st.write("")

# ---------------------------------------------------------------- all groups side by side
T.banner("All groups side by side")
st.caption("Each column is one group of students. Read across a row to see whether newer groups are doing better "
           "at the same milestone. “Not yet” means that group hasn't had enough time.")
rows = [("Completed so far", "CMP-TD")] + [(lbl, code) for _, items in STAGES for code, lbl in items]
def _cell(c, y):
    x = value(c, y)
    return f"<b style='color:{T.NAVY}'>{x['value']:.0%}</b>" if x is not None else f"<span style='color:{T.GRAY}'>Not yet</span>"


st.markdown(T.html_table([cohort_label(y) + (" ★" if y == D.GOAL_COHORT else "") for y in cohorts],
                         [[lbl] + [_cell(c, y) for y in cohorts] for lbl, c in rows], "Milestone"),
            unsafe_allow_html=True)
st.caption("★ the 2029 goal group. The “so far” rows keep rising each year, so older groups will always be "
           "higher there; the other milestones are the fair comparison.")

st.divider()
st.caption(f"Source: IERPG student cohort report ({D.kpi_source().split('(')[-1].rstrip(')') or 'latest'}). "
           f"\"Students\" are first-time students who started in the fall. Counts only; no student records are shown. "
           "More detail is in the full SFF dashboard.")
