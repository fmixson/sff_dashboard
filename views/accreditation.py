import streamlit as st

from sff import config as C, data as D
from sff.report import build_report
from views import common

st.title("Core Inquiry 3 – Accreditation Evidence")
st.caption("ACCJC Standards 1.2 and 1.5. The peer review team asked which body monitors the Students First "
           "Framework and how that body decides when a strategy needs to change. This page answers each interview "
           "topic from live dashboard data and produces the evidence the team requested.")

# ------------------------------------------------------------------ live facts
m = common.current_matrix()
strat = D.strategies(m)
res, is_sample = common.kpi_results()
links = D.load_strategy_kpis()
reviews = D.load_reviews()
mr = D.load_measure_results()
astat = D.load_activity_status()
req = common.requests()
fy = common.fiscal_years()[-1]
targets = D.load_kpi_targets(m)
pace = D.goal_pace(res)

n_strat = len(strat)
n_linked = links["strategy"].nunique()
n_rated = int((strat["status"] != "Not yet assessed").sum())
n_changed = int(strat["status"].isin(["Needs adjustment", "Replace", "Retire"]).sum())
meetings = reviews["meeting"].nunique() if not reviews.empty else 0
n_targets = int(targets.loc[targets["kpi_code"] != "GOAL", "target"].notna().sum())
n_kpis = int((targets["kpi_code"] != "GOAL").sum())
areas_loaded = sorted(req.loc[req["fiscal_year"] == fy, "area"].unique())
all_areas = C.AREAS


def progress(n: int, total: int):
    """True = complete, None = partial (warning), False = not started."""
    return True if total and n >= total else (None if n > 0 else False)


def item(ok: bool | None, text: str):
    icon = "✅" if ok else ("⚠️" if ok is None else "❌")
    st.markdown(f"{icon} {text}")


# ------------------------------------------------------------------ readiness
st.subheader("Readiness at a glance")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Accountable body", "Designated" if C.ACCOUNTABLE_BODY else "Not yet")
r2.metric("Strategies with KPIs linked", f"{n_linked} of {n_strat}")
r3.metric("Strategies rated", f"{n_rated} of {n_strat}", help=f"{meetings} review meeting(s) logged")
r4.metric(f"{fy} areas loaded", f"{len(areas_loaded)} of {len(all_areas)}")

# ------------------------------------------------------------------ five topics
st.subheader("The team's five interview topics")

with st.container(border=True):
    st.markdown("**1. Ownership.** *Which body is ultimately responsible for monitoring progress on the SFF, "
                "and how is that responsibility documented?*")
    item(bool(C.ACCOUNTABLE_BODY), f"Accountable body: **{C.ACCOUNTABLE_BODY or 'not yet designated'}** "
         "(set `ACCOUNTABLE_BODY` in `sff/config.py`).")
    item(bool(C.ACCOUNTABLE_BODY_CHARGE), f"Charge / terms of reference: **{C.ACCOUNTABLE_BODY_CHARGE or 'not yet adopted'}**.")
    item(True, "Every strategy has a proposed lead area and reviewing path (Strategy Detail page).")

with st.container(border=True):
    st.markdown("**2. Strategies vs. indicators.** *How does the College know whether a strategy is being carried "
                "out and having its intended effect, especially strategies with no assigned indicator?*")
    process = sorted(set(strat["code"]) - set(links["strategy"]))
    item(True, f"{n_linked} of {n_strat} strategies are linked to KPIs"
         + (f"; {', '.join(process)} is a process strategy assessed by its measures." if process else "."))
    item(True, "Every strategy has an implementation measure (*is it happening?*) and an effectiveness measure "
         "(*is it working?*).")
    n_meas = mr["code"].nunique() if not mr.empty else 0
    item(progress(n_meas, n_strat), f"Measure results recorded for {n_meas} of {n_strat} strategies.")
    acts_all = D.all_activities(req)
    fy_keys = set(acts_all.loc[acts_all["fiscal_year"] == fy, "activity_key"])
    n_act = len(set(astat["activity_key"]) & fy_keys) if not astat.empty else 0
    item(progress(n_act, len(fy_keys)), f"Activity status recorded for {n_act} of {len(fy_keys)} {fy} activities "
         f"({int(((acts_all['fiscal_year'] == fy) & (acts_all['activity_type'] == D.TYPE_MANUAL)).sum())} added directly).")
    a_cur = D.with_activity_status(acts_all[acts_all["fiscal_year"] == fy], astat)
    n_exp = int(a_cur["expected_result"].fillna("").astype(str).str.strip().ne("").sum())
    n_res_rated = int(a_cur["result_rating"].isin(D.RATED).sum())
    n_met = int((a_cur["result_rating"] == "Met").sum())
    item(progress(n_exp, len(a_cur)), f"Expected result written for {n_exp} of {len(a_cur)} {fy} activities; "
         f"{n_res_rated} rated against it ({n_met} Met).")
    n_pend = int((~req.loc[req["fiscal_year"] == fy, "approved"]).sum())
    n_appr = len(D.activities(req[req["fiscal_year"] == fy]))
    item(progress(n_appr, n_appr + n_pend),
         f"{n_appr} of {n_appr + n_pend} {fy} requests have VP/area approval (activities); "
         f"{n_pend} await a decision on the VP Approvals page.")

with st.container(border=True):
    st.markdown("**3. From data to decisions.** *When indicator results are reported, what happens next? Who decides "
                "whether to continue, adjust, or replace a strategy?*")
    item(True, "Review & Decisions page puts KPI trends, measure ratings, and activity completion beside each "
         "strategy; the accountable body records On track / Needs adjustment / Replace / Retire with a rationale.")
    item(progress(n_rated, n_strat), f"{n_rated} of {n_strat} strategies rated across {meetings} logged meeting(s); "
         f"{n_changed} rated for change (adjust/replace/retire).")
    item(True, "Resource Alignment compares funding with each strategy's rating, the link to PBC resource allocation.")

with st.container(border=True):
    st.markdown("**4. Coordination across bodies.** *How does the work of IERPG, PBC, ACE, and the Board fit "
                "together? Where do their findings meet?*")
    st.markdown(f"Annual cycle: {C.REVIEW_CYCLE}")
    st.markdown("Where findings meet: this dashboard and the Strategy Progress Report — IERPG supplies KPI results, "
                "lead areas supply measures and activity status, ACE reviews equity gaps (KPIs and Goal pages show "
                "every KPI by race/ethnicity), PBC sees funding vs. status, and the Board receives the report.")
    item(None if not C.ACCOUNTABLE_BODY else True, "Cycle becomes official once the accountable body's charge is adopted.")

with st.container(border=True):
    st.markdown("**5. Interim progress.** *How will the College judge whether it is on track for the 2029 goal "
                "before the fall 2024 cohort results are available?*")
    if not pace.empty:
        allst = pace[pace["group"] == "All students"].iloc[0]
        behind = (pace["on_pace"] == "Behind pace").sum()
        item(None, f"Goal page: all students at {allst['latest']:.1%} ({allst['latest_year']}), needing "
             f"{allst['needed_per_year'] * 100:+.1f} pts/yr; {behind} of {len(pace)} groups behind pace"
             f"{' (SAMPLE data)' if is_sample else ''}.")
    item(True, "Lever Scorecard tracks leading KPIs (first-term units, first-year math/English, persistence) "
         "that move years before five-year completion.")
    item(progress(n_targets, n_kpis), f"Interim targets set for {n_targets} of {n_kpis} KPIs.")
    item(not is_sample or None, "KPI results are " + ("SAMPLE placeholders – load IERPG data." if is_sample else "IERPG data."))

# ------------------------------------------------------------------ evidence
st.subheader("Evidence the team requested")
e = [
    ("Charge, terms of reference, or planning document assigning SFF monitoring",
     C.ACCOUNTABLE_BODY_CHARGE or "Pending – draft and adopt the charge for the accountable body"),
    ("Minutes from the most recent meeting reviewing strategies and KPIs",
     f"Decision Log ({len(reviews)} entries, {meetings} meeting(s)) – export below and attach to minutes"
     if len(reviews) else "Pending – hold the first SFF review and record ratings on Review & Decisions"),
    ("Report tracking SFF strategies and the activities mapped to them",
     "Strategy Progress Report – download below"),
]
for need, status in e:
    st.markdown(f"- **{need}:** {status}")

st.download_button("Download Strategy Progress Report (Excel)", build_report(),
                   file_name=f"SFF_Strategy_Progress_Report_{fy}.xlsx",
                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", type="primary")
st.caption("Sheets: Cover, Goal Pace, Lever Scorecard, Strategy Progress, Activities, Decision Log, Measure Results. "
           "ACCJC asks for evidence as separate PDFs: open in Excel and save each needed sheet as PDF.")

# ------------------------------------------------------------------ gaps
st.subheader("Open items before the March 2027 visit")
gaps = []
if not C.ACCOUNTABLE_BODY:
    gaps.append("Designate the accountable body and adopt its charge.")
if is_sample:
    gaps.append("Load IERPG KPI results (replace sample data), including five-year completion by group.")
if n_targets < n_kpis:
    gaps.append(f"Set interim targets for the remaining {n_kpis - n_targets} KPIs.")
missing = [a for a in all_areas if a not in areas_loaded]
if missing:
    gaps.append(f"Load {fy} resource requests for: {', '.join(missing)}.")
n_pend_all = int((~req.loc[req["fiscal_year"] == fy, "approved"]).sum())
if n_pend_all:
    gaps.append(f"Record VP/area decisions for {n_pend_all} {fy} requests (VP Approvals page).")
if n_rated == 0:
    gaps.append("Hold the first SFF review meeting and record ratings and decisions.")
gaps.append("Have each area confirm the proposed primary strategy for its requests.")
for g in gaps:
    st.markdown(f"- {g}")
