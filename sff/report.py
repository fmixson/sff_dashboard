"""SFF Strategy Progress Report (Excel) - the 'report that tracks Framework strategies
and the activities mapped to them' requested in Core Inquiry 3. Pure pandas/openpyxl,
so it can be generated from the app, a script, or a scheduled job.

    python -c "from sff.report import build_report; open('report.xlsx','wb').write(build_report())"
"""
from __future__ import annotations

import io
from datetime import datetime

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill

from . import config as C
from . import data as D


def report_frames() -> dict[str, pd.DataFrame]:
    m = D.with_current_status(D.load_matrix(), D.load_reviews())
    strat = D.strategies(m)
    res, is_sample = D.load_kpi_results()
    targets = D.load_kpi_targets(m)
    kpi_meta = D.kpis(m)[["code", "element", "lever", "indicator_type"]]
    summ = D.kpi_summary(res, list(kpi_meta["code"]), targets)
    links = D.load_strategy_kpis()
    mr = D.load_measure_results()
    req = D.with_activity_status(D.load_requests(), D.load_activity_status())
    acts_u = D.with_activity_status(D.all_activities(D.load_requests()), D.load_activity_status())
    fy = sorted(req["fiscal_year"].unique())[-1]
    comp = D.activity_completion(acts_u[acts_u["fiscal_year"] == fy]).set_index("strategy")
    reviews = D.load_reviews()

    # ---- cover
    cov = req.groupby(["fiscal_year", "area"]).size()
    cover = pd.DataFrame({"Item": [
        "Report", "Generated", "Accountable body", "Reviewing cycle", "Data coverage (requests)",
        "KPI data", "Activities (VP/area-approved requests)", "Strategies rated", "Decisions recorded", "Measure results recorded", "Activity updates recorded"],
        "Value": [
        "Students First Framework – Strategy Progress Report",
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        C.ACCOUNTABLE_BODY or "NOT YET DESIGNATED",
        C.REVIEW_CYCLE,
        "; ".join(f"{a} {f}: {n}" for (f, a), n in cov.items()),
        "SAMPLE (synthetic) – replace with IERPG results" if is_sample else "IERPG results",
        f"{int(req['approved'].sum())} of {len(req)} requests approved; "
        f"{int((acts_u['activity_type'] == D.TYPE_MANUAL).sum())} activities added directly",
        f"{int((strat['status'] != 'Not yet assessed').sum())} of {len(strat)}",
        str(len(reviews)), str(len(mr)), str(len(D.load_activity_status())),
    ]})

    # ---- goal
    goal = D.goal_pace(res).rename(columns={
        "group": "Student group", "latest_year": "Latest year", "latest": "5-yr completion",
        "gap_to_goal": "Gap to 50%", "years_left": "Years left", "needed_per_year": "Needed / yr",
        "observed_per_year": "Observed / yr", "on_pace": "Pace"})
    if goal.empty:   # no finished five-year cohort yet: report the goal cohort's rate to date
        goal = D.goal_to_date(res).rename(columns={
            "group": "Student group", "numerator": "Completed so far", "denominator": "Cohort size",
            "value": f"5-yr completion to date (Fall {D.GOAL_COHORT_FALL} cohort, in progress)",
            "gap_to_goal": "Gap to 50%", "still_needed": "More completers needed by 2029"})

    # ---- lever scorecard
    sc = summ.merge(kpi_meta, left_on="kpi_code", right_on="code", how="left")
    sc["lever"] = sc["lever"].map(lambda L: f"{L}. {C.LEVERS.get(L, '')}")
    sc = sc[["lever", "kpi_code", "element", "indicator_type", "latest_year", "latest", "annual_change",
             "trend", "target", "vs_target", "largest_gap", "largest_gap_group"]].rename(columns={
        "lever": "Lever", "kpi_code": "KPI", "element": "Indicator", "indicator_type": "Type",
        "latest_year": "Latest year", "latest": "Latest (all students)", "annual_change": "Change / yr",
        "trend": "Trend", "target": "Target", "vs_target": "vs. target", "largest_gap": "Largest equity gap",
        "largest_gap_group": "Group"})

    # ---- strategy progress
    trend = summ.set_index("kpi_code")["trend"]
    last_m = mr.groupby(["code", "measure_type"]).tail(1) if not mr.empty else mr
    def m_get(code, t, col):
        r = last_m[(last_m["code"] == code) & (last_m["measure_type"] == t)] if not last_m.empty else last_m
        return r[col].iloc[0] if len(r) else None
    by_area = req[req["fiscal_year"] == fy].groupby(["strategy", "area"])["cost"].sum().unstack(fill_value=0)
    rows = []
    for s in strat.itertuples():
        ks = list(links.loc[links["strategy"] == s.code, "kpi_code"])
        c = comp.loc[s.code] if s.code in comp.index else None
        row = {
            "Code": s.code, "Lever": f"{s.lever}. {C.LEVERS[s.lever]}", "Strategy": s.element, "Lead": s.lead,
            "Status": s.status, "Decision & rationale": s.decision,
            "Linked KPIs": ", ".join(ks) or "process",
            "Linked KPIs improving": f"{int((trend.reindex(ks) == 'Improving').sum())} of {len(ks)}" if ks else "—",
            "Is it happening? (measure)": s.implementation_measure,
            "Happening – latest result": m_get(s.code, "Implementation", "result"),
            "Happening – rating": m_get(s.code, "Implementation", "rating"),
            "Is it working? (measure)": s.effectiveness_measure,
            "Working – latest result": m_get(s.code, "Effectiveness", "result"),
            "Working – rating": m_get(s.code, "Effectiveness", "rating"),
            f"{fy} activities": int(c["activities"]) if c is not None else 0,
            f"{fy} completed": int(c["completed"]) if c is not None else 0,
            f"{fy} with expected result": int(c["with_expected"]) if c is not None else 0,
            f"{fy} results rated": int(c["rated"]) if c is not None else 0,
            f"{fy} met expected": int(c["met"]) if c is not None else 0,
            f"{fy} partially met": int(c["partly_met"]) if c is not None else 0,
            f"{fy} not met": int(c["not_met"]) if c is not None else 0,
        }
        for a in by_area.columns:
            row[f"{fy} $ – {a}"] = float(by_area.loc[s.code, a]) if s.code in by_area.index else 0.0
        rows.append(row)
    progress = pd.DataFrame(rows)

    # ---- activities
    cols = ["fiscal_year", "area", "division", "department", "strategy", "secondary", "activity", "request",
            "cost", "cost_raw", "vp_decision", "approval_source", "activity_status", "outcome", "strategy_source", "note"]
    all_req = req[cols].sort_values(["fiscal_year", "area", "strategy"]).rename(columns={
        "fiscal_year": "FY", "area": "Area", "division": "Division", "department": "Department",
        "strategy": "Primary strategy", "secondary": "Secondary", "activity": "Activity", "request": "Resource request",
        "cost": "Cost", "cost_raw": "Cost (as entered)", "vp_decision": "VP/area decision",
        "approval_source": "Decision recorded in", "activity_status": "Activity status",
        "outcome": "Outcome / evidence", "strategy_source": "Strategy assigned by", "note": "Note"})
    acts = acts_u[["activity_type", "funding_source", "owner"] + cols[:7] + ["expected_result", "result_rating"] + cols[7:]]
    acts = acts.sort_values(["strategy", "fiscal_year", "area"]).rename(columns={
        "fiscal_year": "FY", "area": "Area", "division": "Division", "department": "Department",
        "strategy": "Primary strategy", "secondary": "Secondary", "activity": "Activity", "request": "Resource request",
        "cost": "Cost", "cost_raw": "Cost (as entered)", "vp_decision": "VP/area decision",
        "approval_source": "Decision recorded in", "activity_status": "Activity status", "outcome": "Outcome / evidence",
        "expected_result": "Expected result", "result_rating": "Result vs. expected", "activity_type": "Type", "funding_source": "Funding", "owner": "Owner / lead",
        "strategy_source": "Strategy assigned by", "note": "Note"})

    log = reviews.rename(columns={"timestamp": "Timestamp", "code": "Code", "status": "Status",
                                  "decision": "Decision & rationale", "reviewer": "Recorded by", "meeting": "Meeting"})
    return {"Cover": cover, "Goal Pace": goal, "Lever Scorecard": sc, "Strategy Progress": progress,
            "Activities (approved)": acts,
            "All Requests": all_req, "Decision Log": log, "Measure Results": mr}


PCT_COLS = {"5-yr completion", "Gap to 50%", "Needed / yr", "Observed / yr", "Latest (all students)",
            "Change / yr", "Target", "Largest equity gap"}


def build_report() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        for name, df in report_frames().items():
            df.to_excel(xw, sheet_name=name, index=False)
            ws = xw.sheets[name]
            for cell in ws[1]:
                cell.font = Font(name="Arial", bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="1F3864")
                cell.alignment = Alignment(wrap_text=True, vertical="center")
            for j, col in enumerate(df.columns, 1):
                letter = ws.cell(1, j).column_letter
                width = min(max(len(str(col)), *(len(str(v)) for v in df[col].head(50))) + 2, 60) if len(df) else 18
                ws.column_dimensions[letter].width = max(width, 10)
                for i in range(2, len(df) + 2):
                    c = ws.cell(i, j)
                    c.font = Font(name="Arial", size=10)
                    c.alignment = Alignment(wrap_text=True, vertical="top")
                    if col in PCT_COLS or str(col).startswith("5-yr completion"):
                        c.number_format = "0.0%"
                    elif col == "Cost" or str(col).startswith(tuple(f"{f} $" for f in ("FY26", "FY27", "FY28"))):
                        c.number_format = '$#,##0'
            ws.freeze_panes = "A2"
    return buf.getvalue()
