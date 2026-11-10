"""Extract/transform: read source workbooks into tidy DataFrames.

One reader per source *layout*. Area request workbooks changed layout between
FY26 and FY27, so each has its own reader; both return the same REQUEST_COLS.
Add a new reader (or reuse one) when another year or area is added.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REQUEST_COLS = [
    "fiscal_year", "area", "division", "department", "request", "cost", "cost_raw",
    "resource_type", "strategy", "secondary", "activity", "strategy_source",
    "dean_approval", "area_approval", "area_rank", "note", "source_file", "source_row",
    "funding",            # funding source when approved outside the general-fund ranking (SWF, SEAP, AB1705, ...)
]

DIVISION_ALIASES = {
    "Educational Partnership and Programs": "Educational Partnerships and Programs",
    "HSS": "Humanities and Social Sciences",
}

MATRIX_COLS = {
    "Element Type": "element_type", "Code": "code", "Element": "element",
    "Assessment Question": "question",
    "Implementation Measure (Is it happening?)": "implementation_measure",
    "Effectiveness Measure (Is it working?)": "effectiveness_measure",
    "Linked KPI(s)": "linked_kpis", "Indicator Type": "indicator_type",
    "Disaggregate by Race/Ethnicity?": "disaggregate", "Data Source": "data_source",
    "Lead / Data Owner (proposed)": "lead", "Reviewing Body": "reviewing_body",
    "Review Timing": "review_timing", "Baseline": "baseline", "Target": "target",
    "Current Result": "current_result", "Status": "status",
    "Decision & Rationale": "decision", "Notes": "notes",
}

_CODE = re.compile(r"\b([A-D])\.\s?(\d)")
KPI_CODE = re.compile(r"\b([A-D]-K\d+)\b")


def strategy_codes(text) -> list[str]:
    return list(dict.fromkeys(f"{a}.{b}" for a, b in _CODE.findall(str(text or ""))))


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def parse_cost(v):
    """Numbers stay numbers; '$10K', '80k', '150,000.00/year' become numbers; anything else -> None."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    m = re.fullmatch(r"\s*\$?\s*([\d,]+(?:\.\d+)?)\s*([kK])?\s*(?:/\s*year)?\s*", str(v or ""))
    if not m:
        return None
    n = float(m.group(1).replace(",", ""))
    return n * 1000 if m.group(2) else n


def _clean(s):
    return " ".join(str(s).split()) if pd.notna(s) and s is not None else None


# ----------------------------------------------------------------- matrix
def read_matrix(path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Assessment Matrix", header=3)
    df = df.rename(columns=MATRIX_COLS)[list(MATRIX_COLS.values())].dropna(subset=["code"])
    df["lever"] = df["code"].astype(str).str[0].where(df["element_type"].isin(["Strategy", "Lever", "KPI"]))
    return df.reset_index(drop=True)


# ------------------------------------------------------ FY27 layout (reviewed)
def read_requests_fy27(path, fiscal_year="FY27", area="Academic Affairs") -> pd.DataFrame:
    """FY27 area workbook after the 11/2026 SFF alignment review (columns X-AA added)."""
    raw = pd.read_excel(path, sheet_name=area, header=1)
    df = pd.DataFrame({
        "fiscal_year": fiscal_year, "area": raw["Area"], "division": raw["Division"],
        "department": raw["Dept"], "request": raw["Resource Request"],
        "cost_raw": raw["Estimated Cost"], "resource_type": raw["Resource Type"],
        "strategy": raw["Primary SFF Strategy (proposed)"].astype(str).str.extract(r"^([A-D]\.\d)")[0],
        "secondary": raw["Secondary SFF Strategy (proposed)"].astype(str).str.extract(r"^([A-D]\.\d)")[0],
        "activity": raw["SFF Activity (what this request funds)"],
        "strategy_source": "Proposed 11/2026 (area alignment review)",
        "dean_approval": raw["Dean/Manager Approval"], "area_approval": raw["Area Approval (P/VP)"],
        "area_rank": raw["Area Rank"], "note": raw["Alignment Note"],
        "source_file": Path(path).name, "source_row": raw.index + 3,
    })
    df = df.dropna(subset=["request"])
    df["strategy"] = df["strategy"].fillna("None")
    return _finish(df)


# --------------------------------------------------------------- FY26 layout
def read_requests_fy26(path, carry_over: dict[str, str], manual: dict[int, str],
                       fiscal_year="FY26", area="Academic Affairs") -> pd.DataFrame:
    """FY26 area workbook (.xlsm; columns A-F goals, G-T requests, R = area approval).

    Primary strategy precedence:
      1. manual: proposed primary for multi-strategy / blank rows (keyed by sheet row)
      2. carry_over: same request name was reviewed in FY27 -> reuse that strategy
      3. department listed exactly one strategy -> use it (not independently reviewed)
    """
    raw = pd.read_excel(path, sheet_name=area, header=1)
    rows = []
    for i, r in raw.iterrows():
        sheet_row = i + 3
        req = r.get("Resource Request")
        if pd.isna(req):
            continue
        dept_codes = strategy_codes(r.get("Student First Framework Lever Strategy"))
        if sheet_row in manual:
            strat, src = manual[sheet_row], "Proposed 11/2026 (dept listed several)"
        elif norm(req) in carry_over:
            strat, src = carry_over[norm(req)], "Carried from FY27 alignment"
        elif len(dept_codes) == 1:
            strat, src = dept_codes[0], "Dept-selected (single)"
        else:
            strat, src = "None", "Unassigned"
        rows.append({
            "fiscal_year": fiscal_year, "area": area, "division": r.get("Division"),
            "department": r.get("Dept"), "request": req, "cost_raw": r.get("Estimated Cost"),
            "resource_type": r.get("Resource Type"), "strategy": strat, "secondary": None,
            "activity": r.get("Activities "), "strategy_source": src,
            "dean_approval": r.get("Dean/Manager Approval"), "area_approval": r.get("Area Approval (P/VP)"),
            "area_rank": r.get("Rank.1"), "note": None,
            "source_file": Path(path).name, "source_row": sheet_row,
        })
    return _finish(pd.DataFrame(rows))


# ------------------------------------------------- area template + mapping file
def _vp_comment(r) -> str:
    c = r.get("Comments.1")              # second "Comments" column = Area (P/VP) comments
    return f"VP comment: {' '.join(str(c).split())}" if pd.notna(c) and str(c).strip() else ""


def _join(*parts) -> str | None:
    out = "; ".join(p for p in parts if p)
    return out or None


UNFUNDED_NOTE = "Ranked and area-approved, but below the $1M general-fund line (F. Lopez 8/17/2026); not funded"


def read_requests_mapped(path, sheet: str, mapping: dict, fiscal_year: str, area: str,
                         header_row: int = 1, area_filter: str | None = None,
                         funded_rows: set[int] | dict[int, str] | None = None) -> pd.DataFrame:
    """Workbook in the FY27 area template whose SFF alignment lives in a mapping file
    {sheet_row: (primary, secondary, activity, note)}; a value of None excludes the row.
    header_row = 0-based row of the column headers (1 in area files, 6 in the all-areas ranking);
    area_filter keeps only rows whose Area column equals it (all-areas ranking)."""
    raw = pd.read_excel(path, sheet_name=sheet, header=header_row)
    rows = []
    for i, r in raw.iterrows():
        sheet_row = i + header_row + 2
        if pd.isna(r.get("Resource Request")):
            continue
        if area_filter and str(r.get("Area", "")).strip() != area_filter:
            continue
        if sheet_row in mapping and mapping[sheet_row] is None:   # excluded (e.g., duplicate entry)
            continue
        prim, sec, act, note = mapping.get(sheet_row, ("None", "", r.get("Objectives/Activities "), "Not in mapping file"))
        decision, funding = r.get("Area Approval (P/VP)"), None
        if funded_rows is not None and str(decision).strip() == "Approved":
            if "cat" in str(r.get("Area Rank", "")).lower():          # "Cat Fun" = categorical funding
                funding = "Categorical funding"
            elif sheet_row not in funded_rows:
                decision, note = "Not approved", _join(note, UNFUNDED_NOTE)
            else:
                funding = funded_rows[sheet_row] if isinstance(funded_rows, dict) else "General fund (2026-27 allocation)"
        rows.append({
            "fiscal_year": fiscal_year, "area": area, "division": r.get("Division"),
            "department": r.get("Dept"), "request": r.get("Resource Request"),
            "cost_raw": r.get("Estimated Cost"), "resource_type": r.get("Resource Type"),
            "strategy": prim, "secondary": sec or None, "activity": act,
            "strategy_source": "Proposed 11/2026 (area alignment review)",
            "dean_approval": r.get("Dean/Manager Approval"), "area_approval": decision,
            "area_rank": r.get("Area Rank"), "note": _join(note, _vp_comment(r)),
            "source_file": Path(path).name, "source_row": sheet_row, "funding": funding,
        })
    return _finish(pd.DataFrame(rows))


def apply_ranking(df: pd.DataFrame, path, crosswalk: dict[int, int], area_filter: str,
                  header_row: int = 6, funded_rows: set[int] | None = None) -> pd.DataFrame:
    """Copy the President/VP decision, area rank and VP comment from the all-areas ranking file onto
    requests read from an area file. crosswalk: ranking sheet row -> area-file source_row.
    Notes when the ranked amount differs from the area file's cost."""
    raw = pd.read_excel(path, sheet_name="Resource Requests", header=header_row)
    raw.index = raw.index + header_row + 2
    df = df.copy()
    for c in ("funding", "note", "area_approval"):
        df[c] = df[c].astype(object)
    pos = {r: i for i, r in zip(df.index, df["source_row"])}
    for rank_row, src_row in crosswalk.items():
        if rank_row not in raw.index or src_row not in pos:
            raise ValueError(f"Ranking crosswalk {rank_row} -> {src_row} not found")
        r, i = raw.loc[rank_row], pos[src_row]
        if str(r.get("Area", "")).strip() != area_filter:
            raise ValueError(f"Ranking row {rank_row} is not {area_filter}")
        ranked = parse_cost(r.get("Estimated Cost"))
        diff = (f"Ranked at ${ranked:,.0f} (area file: {df.at[i, 'cost_raw']})"
                if ranked is not None and (df.at[i, "cost"] is None or pd.isna(df.at[i, "cost"])
                                           or abs(ranked - df.at[i, "cost"]) > 1) else "")
        if ranked is not None and pd.isna(df.at[i, "cost"]):   # area file had no numeric cost: use the ranked amount
            df.at[i, "cost"] = ranked
        decision, unfunded = _clean(r.get("Area Approval (P/VP)")), ""
        if funded_rows is not None and decision == "Approved":
            if rank_row in funded_rows:
                df.at[i, "funding"] = "General fund (2026-27 allocation)"
                if ranked is not None:                # funded at the ranked amount
                    df.at[i, "cost"] = ranked
            else:
                decision, unfunded = "Not approved", UNFUNDED_NOTE
        df.at[i, "area_approval"] = decision
        df.at[i, "area_rank"] = None if pd.isna(r.get("Area Rank")) else str(r.get("Area Rank")).removesuffix(".0")
        df.at[i, "note"] = _join(df.at[i, "note"], f"All-areas ranking row {rank_row}", diff, unfunded, _vp_comment(r))
    return df


def apply_other_approvals(df: pd.DataFrame, approvals: dict[int, tuple], added: list[dict],
                          fiscal_year: str, area: str, label: str, deferred: list[int] | None = None,
                          granted_amounts: bool = False, clear_unlisted: bool = False,
                          approval_label: str = "Approved outside the all-areas ranking (11/2026 AA approved list)") -> pd.DataFrame:
    """Mark requests approved from an approved/granted list, mark `deferred` rows Deferred, and append approved
    requests that are not in the area file.
    approvals: source_row -> (funding/comment, amount or None[, note[, approval label for this row]]).
    granted_amounts: the amount replaces the cost (the list shows what was funded); the request stays in the note.
    clear_unlisted: rows the area file marks Approved but that are not on the list lose that approval (noted)."""
    df = df.copy()
    for c in ("funding", "note", "area_approval"):
        df[c] = df[c].astype(object)
    pos = {r: i for i, r in zip(df.index, df["source_row"])}
    for src_row, spec in approvals.items():
        funding, amount, extra, own_label = (tuple(spec) + ("", None))[:4]   # optional 4th item: its own approval label
        if src_row not in pos:
            raise ValueError(f"{label}: row {src_row} not found")
        i = pos[src_row]
        diff = ""
        if amount is not None:
            if pd.isna(df.at[i, "cost"]):
                df.at[i, "cost"] = float(amount)
            elif abs(float(amount) - df.at[i, "cost"]) > 1:
                if granted_amounts:
                    diff = f"Granted ${float(amount):,.0f} of ${df.at[i, 'cost']:,.0f} requested"
                    df.at[i, "cost"] = float(amount)
                else:
                    diff = f"Approved list shows ${float(amount):,.0f} (area file: {df.at[i, 'cost_raw']})"
        df.at[i, "area_approval"] = "Approved"
        df.at[i, "funding"] = funding or None
        df.at[i, "note"] = _join(df.at[i, "note"], (own_label or approval_label) + (f"; funding: {funding}" if funding else ""),
                                 diff, extra)
    if clear_unlisted:
        listed = set(approvals)
        for src_row, i in pos.items():
            if src_row not in listed and df.at[i, "area_approval"] == "Approved":
                df.at[i, "area_approval"] = None
                df.at[i, "note"] = _join(df.at[i, "note"], "Area file marked Approved, but not on the granted "
                                         "general-fund list; confirm whether it was funded another way")
    for src_row in deferred or []:
        if src_row not in pos:
            raise ValueError(f"{label}: deferred row {src_row} not found")
        i = pos[src_row]
        df.at[i, "area_approval"] = "Deferred"
        df.at[i, "note"] = _join(df.at[i, "note"], "Deferred (not in the all-areas ranking or the AA approved list; 11/2026)")
    if added:
        extra = pd.DataFrame([{
            "fiscal_year": fiscal_year, "area": a.get("area", area), "division": a["division"], "department": a.get("department"),
            "request": a["request"], "cost_raw": a.get("cost"), "resource_type": a.get("resource_type"),
            "strategy": a.get("strategy") or "None", "secondary": a.get("secondary"), "activity": a.get("activity"),
            "strategy_source": "Proposed 11/2026 (area alignment review)", "dean_approval": None,
            "area_approval": "Approved", "area_rank": None, "note": a.get("note"),
            "source_file": label, "source_row": int(a["id"]), "funding": a.get("funding") or None,
        } for a in added])
        df = pd.concat([df, _finish(extra)], ignore_index=True)
    return df


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    df["division"] = df["division"].replace(DIVISION_ALIASES)
    df["cost"] = df["cost_raw"].map(parse_cost)
    df["area_rank"] = df["area_rank"].map(lambda v: None if pd.isna(v) else str(v).removesuffix(".0"))
    for c in ["request", "activity", "cost_raw", "dean_approval", "area_approval", "note"]:
        df[c] = df[c].map(_clean)
    df["dean_approval"] = df["dean_approval"].str.strip()
    df["area_approval"] = df["area_approval"].str.strip()
    return df.reindex(columns=REQUEST_COLS).reset_index(drop=True)
