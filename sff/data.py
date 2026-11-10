"""Data access layer: reads/writes data/sff.db (SQLite). No Streamlit imports.

The pages only call these functions. Moving to a server database later
(PostgreSQL, SQL Server) means changing `_connect()` and nothing else.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime

import pandas as pd

from . import config as C


# Tables people write to from the app. Created if missing; NEVER dropped by build_db.
PERSISTENT_SCHEMA = """
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, code TEXT NOT NULL,
    status TEXT NOT NULL, decision TEXT, reviewer TEXT, meeting TEXT);
CREATE TABLE IF NOT EXISTS measure_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, code TEXT NOT NULL,
    period TEXT NOT NULL, measure_type TEXT NOT NULL,        -- 'Implementation' | 'Effectiveness'
    result TEXT, rating TEXT NOT NULL, entered_by TEXT);
CREATE TABLE IF NOT EXISTS activity_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
    activity_key TEXT NOT NULL,                              -- source_file#source_row (stable across rebuilds)
    status TEXT NOT NULL, outcome TEXT, entered_by TEXT,
    expected_result TEXT,                                    -- what the activity should produce (set at the start)
    result_rating TEXT);                                     -- Met | Partially met | Not met | Too early to tell
CREATE TABLE IF NOT EXISTS request_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
    activity_key TEXT NOT NULL,                              -- source_file#source_row
    decision TEXT NOT NULL,                                  -- Approved | Denied | Deferred | (blank = clear)
    approver TEXT, note TEXT);
CREATE TABLE IF NOT EXISTS manual_activities (           -- activities NOT tied to a resource request
    id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT NOT NULL, updated TEXT NOT NULL,
    fiscal_year TEXT NOT NULL, area TEXT NOT NULL, division TEXT, department TEXT,
    strategy TEXT NOT NULL, secondary TEXT, activity TEXT NOT NULL,
    funding_source TEXT, cost REAL, owner TEXT, note TEXT, entered_by TEXT,
    removed INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS activity_strategy (            -- strategy chosen in the app; the latest row per activity wins
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
    activity_key TEXT NOT NULL,                              -- source_file#source_row, or manual#id
    strategy TEXT NOT NULL, secondary TEXT, entered_by TEXT);
CREATE TABLE IF NOT EXISTS activity_text (                -- description rewritten in the app; the latest row per activity wins
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL,
    activity_key TEXT NOT NULL, activity TEXT NOT NULL, entered_by TEXT);
CREATE TABLE IF NOT EXISTS kpi_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, kpi_code TEXT NOT NULL,
    target REAL NOT NULL, target_year TEXT, set_by TEXT);
"""


def _connect():
    if not C.DB_PATH.exists():
        raise FileNotFoundError("data/sff.db not found. Run:  python -m tools.build_db")
    con = sqlite3.connect(C.DB_PATH)
    con.executescript(PERSISTENT_SCHEMA)
    _add_missing_columns(con)
    return con


# columns added after a table was first created: (table, column, type). Existing rows keep NULL.
_ADDED_COLUMNS = [("activity_status", "expected_result", "TEXT"), ("activity_status", "result_rating", "TEXT"),
                  ("manual_activities", "rolled_from", "TEXT")]   # activity_key of the prior-year activity it continues


def _add_missing_columns(con):
    for table, col, typ in _ADDED_COLUMNS:
        have = {r[1] for r in con.execute(f"PRAGMA table_info({table})")}
        if col not in have:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _insert(table: str, cols: list[str], recs: list[tuple]) -> int:
    with _connect() as con:
        con.executemany(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", recs)
    return len(recs)


def _q(sql: str, params=()) -> pd.DataFrame:
    with _connect() as con:
        return pd.read_sql_query(sql, con, params=params)


# ---------------------------------------------------------------- elements
def load_matrix() -> pd.DataFrame:
    df = _q("SELECT * FROM elements")
    df["status"] = df["status"].fillna("Not yet assessed")
    return df


def strategies(m: pd.DataFrame) -> pd.DataFrame:
    return m[m["element_type"] == "Strategy"].copy()


def kpis(m: pd.DataFrame) -> pd.DataFrame:
    return m[m["element_type"] == "KPI"].copy()


# ---------------------------------------------------------------- requests
# An ACTIVITY is a resource request with VP/area approval (decision 11/2026: strict rule).
# Approval comes from the dashboard's VP Approvals page if recorded there (latest entry wins),
# otherwise from the Area Approval (P/VP) column of the source workbook.
REMOVED = "Removed (entered in error)"   # hides the request everywhere except VP Approvals (reversible)
VP_DECISIONS = ["Approved", "Not approved", "Denied", "Deferred", REMOVED, ""]


def load_requests_raw() -> pd.DataFrame:
    df = _q("SELECT * FROM requests")
    df["cost_is_text"] = df["cost"].isna()
    df["lever"] = df["strategy"].str[0].where(df["strategy"] != "None")
    df["activity_key"] = df["source_file"].astype(str) + "#" + df["source_row"].astype(str)
    return df


def load_approvals() -> pd.DataFrame:
    return _q("SELECT timestamp, activity_key, decision, approver, note FROM request_approvals ORDER BY id")


def apply_approvals(req: pd.DataFrame, approvals: pd.DataFrame) -> pd.DataFrame:
    """Add vp_decision, approval_source, approved (bool) using dashboard decisions over file values."""
    req = req.copy()
    latest = approvals.groupby("activity_key").tail(1).set_index("activity_key") if not approvals.empty \
        else pd.DataFrame(columns=["decision", "approver", "timestamp"])
    app = req["activity_key"].map(latest["decision"]) if not latest.empty else pd.Series(None, index=req.index)
    has_app = app.notna()
    req["vp_decision"] = app.where(has_app, req["area_approval"]).replace("", None)
    req["approval_source"] = None
    req.loc[has_app & app.ne(""), "approval_source"] = "Dashboard"
    req.loc[~has_app & req["area_approval"].notna(), "approval_source"] = "Source file"
    req["approved_by"] = req["activity_key"].map(latest["approver"]) if not latest.empty else None
    req["approved"] = req["vp_decision"].eq("Approved")
    return req


def drop_removed(req: pd.DataFrame) -> pd.DataFrame:
    """Requests marked 'Removed (entered in error)' disappear from every page, total and report."""
    return req[req["vp_decision"].ne(REMOVED)] if "vp_decision" in req else req


def load_requests(include_removed: bool = False) -> pd.DataFrame:
    req = apply_approvals(load_requests_raw(), load_approvals())
    return req if include_removed else drop_removed(req)


def append_approvals(rows: pd.DataFrame, approver: str) -> int:
    """rows: activity_key, decision, note"""
    return _insert("request_approvals", ["timestamp", "activity_key", "decision", "approver", "note"],
                   [(_now(), r.activity_key, r.decision or "", approver, r.note) for r in rows.itertuples()])


def fiscal_years() -> list[str]:
    return _q("SELECT DISTINCT fiscal_year FROM requests ORDER BY fiscal_year")["fiscal_year"].tolist()


def dollars_by_strategy(req: pd.DataFrame, strategy_codes: list[str]) -> pd.DataFrame:
    """Requests, requested $, text-cost count, approved $ per strategy (all FYs in `req`)."""
    req = req.assign(approved_cost=req["cost"].where(req["approved"], 0))
    g = req.groupby("strategy").agg(
        requests=("request", "size"), requested=("cost", "sum"),
        text_cost=("cost_is_text", "sum"), approved=("approved_cost", "sum"))
    return g.reindex(strategy_codes + ["None"], fill_value=0).reset_index(names="strategy")


def dollars_by_strategy_and(req: pd.DataFrame, strategy_codes: list[str], by: str) -> pd.DataFrame:
    """dollars_by_strategy split by another column (e.g., 'fiscal_year' or 'area')."""
    out = []
    for key, d in req.groupby(by):
        out.append(dollars_by_strategy(d, strategy_codes).assign(**{by: key}))
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def dollars_by_strategy_year(req: pd.DataFrame, strategy_codes: list[str]) -> pd.DataFrame:
    return dollars_by_strategy_and(req, strategy_codes, "fiscal_year")


# -------------------------------------------------------------------- KPIs
def load_kpi_results(dimension: str = "Race/ethnicity") -> tuple[pd.DataFrame, bool]:
    """KPI results for 'All students' plus the groups of one dimension (default race/ethnicity).
    Columns: kpi_code, year, group, value, numerator, denominator."""
    df = _q("SELECT * FROM kpi_results WHERE dimension IN ('All', ?)", (dimension,))
    for c in ("numerator", "denominator"):
        if c not in df:
            df[c] = None
    return df[["kpi_code", "year", "group", "value", "numerator", "denominator"]], bool(df["is_sample"].any())


def kpi_dimensions() -> list[str]:
    d = _q("SELECT DISTINCT dimension FROM kpi_results WHERE dimension != 'All'")["dimension"].tolist()
    return (["Race/ethnicity"] if "Race/ethnicity" in d else []) + sorted(x for x in d if x != "Race/ethnicity")


def kpi_source() -> str:
    try:
        return _q("SELECT DISTINCT source FROM kpi_results")["source"].iloc[0]
    except Exception:  # noqa: BLE001 - older databases have no source column
        return ""


def load_award_counts() -> pd.DataFrame:
    """Awards earned by entering cohort (aggregates; awards held by under MIN_CELL_SIZE students rolled up)."""
    try:
        return _q("SELECT year, award_type, award, students FROM award_counts")
    except Exception:  # noqa: BLE001 - database built before award counts existed
        return pd.DataFrame(columns=["year", "award_type", "award", "students"])


GAP_MIN_N = 30   # ignore very small groups when naming the "largest gap" group


# ------------------------------------------------------------------ reviews
def load_reviews() -> pd.DataFrame:
    return _q("SELECT timestamp, code, status, decision, reviewer, meeting FROM reviews ORDER BY id")


def append_reviews(rows: pd.DataFrame, reviewer: str, meeting: str) -> int:
    """Append ratings to the decisions log (history is never overwritten)."""
    ts = _now()
    return _insert("reviews", ["timestamp", "code", "status", "decision", "reviewer", "meeting"],
                   [(ts, r.code, r.status, r.decision, reviewer, meeting) for r in rows.itertuples()])


def latest_status(reviews: pd.DataFrame) -> pd.DataFrame:
    if reviews.empty:
        return pd.DataFrame(columns=["code", "status", "decision", "timestamp"])
    return reviews.groupby("code").tail(1)[["code", "status", "decision", "timestamp"]]


def with_current_status(m: pd.DataFrame, reviews: pd.DataFrame) -> pd.DataFrame:
    """Overlay the latest logged rating on the matrix Status column."""
    latest = latest_status(reviews).rename(columns={"status": "logged_status", "decision": "logged_decision"})
    out = m.merge(latest, on="code", how="left")
    out["status"] = out["logged_status"].fillna(out["status"])
    out["decision"] = out["logged_decision"].fillna(out["decision"])
    return out.drop(columns=["logged_status", "logged_decision"])


# ======================================================== strategy <-> KPI links
def load_strategy_kpis() -> pd.DataFrame:
    """One row per (strategy, kpi_code) link, built from the matrix's Linked KPI(s) column."""
    return _q("SELECT strategy, kpi_code FROM strategy_kpis")


# ================================================================ KPI targets
def load_kpi_targets(matrix: pd.DataFrame) -> pd.DataFrame:
    """Latest target per KPI: an app-entered target wins; else the matrix Target column."""
    logged = _q("SELECT kpi_code, target, target_year, set_by, timestamp FROM kpi_targets ORDER BY id")
    logged = logged.groupby("kpi_code").tail(1)
    base = matrix.loc[matrix["element_type"].isin(["KPI", "Goal"]), ["code", "target"]].rename(columns={"code": "kpi_code"})
    out = base.merge(logged, on="kpi_code", how="left", suffixes=("_matrix", ""))
    out["target"] = out["target"].fillna(out["target_matrix"])
    return out[["kpi_code", "target", "target_year", "set_by", "timestamp"]]


def save_kpi_target(kpi_code: str, target: float, target_year: str, set_by: str) -> int:
    return _insert("kpi_targets", ["timestamp", "kpi_code", "target", "target_year", "set_by"],
                   [(_now(), kpi_code, float(target), target_year, set_by)])


# ============================================================ measure results
MEASURE_RATINGS = ["Met", "Partially met", "Not met", "No data yet"]


def load_measure_results() -> pd.DataFrame:
    return _q("SELECT timestamp, code, period, measure_type, result, rating, entered_by "
              "FROM measure_results ORDER BY id")


def append_measure_results(code: str, period: str, entries: list[tuple[str, str, str]], entered_by: str) -> int:
    """entries: [(measure_type, result_text, rating), ...]"""
    return _insert("measure_results", ["timestamp", "code", "period", "measure_type", "result", "rating", "entered_by"],
                   [(_now(), code, period, t, r, g, entered_by) for t, r, g in entries])


def latest_measures(mr: pd.DataFrame) -> pd.DataFrame:
    """Wide table: code -> latest implementation/effectiveness rating and period."""
    if mr.empty:
        return pd.DataFrame(columns=["code", "impl_rating", "eff_rating", "measure_period"])
    last = mr.groupby(["code", "measure_type"]).tail(1)
    w = last.pivot(index="code", columns="measure_type", values="rating")
    w = w.rename(columns={"Implementation": "impl_rating", "Effectiveness": "eff_rating"})
    w["measure_period"] = last.groupby("code")["period"].last()
    return w.reset_index()


# ============================================================ activity status
ACTIVITY_STATUSES = ["Not started", "In progress", "Completed", "Not funded", "Cancelled"]
RESULT_RATINGS = ["Met", "Partially met", "Not met", "Too early to tell"]   # result vs. expected result
RATED = ["Met", "Partially met", "Not met"]


def activity_key(req: pd.DataFrame) -> pd.Series:
    return req["source_file"].astype(str) + "#" + req["source_row"].astype(str)


def activities(req: pd.DataFrame) -> pd.DataFrame:
    """Approved requests only (use all_activities() to include activities added directly)."""
    return req[req["approved"]]


# ------------------------------------------- activities added directly (not resource requests)
FUNDING_SOURCES = ["Existing budget", "Grant / categorical", "No additional cost", "Other"]
MANUAL_COLS = ["fiscal_year", "area", "division", "department", "strategy", "secondary", "activity",
               "funding_source", "cost", "owner", "note"]
TYPE_REQUEST = "Approved resource request"
TYPE_MANUAL = "Added directly"


def load_manual_activities(include_removed: bool = False) -> pd.DataFrame:
    df = _q("SELECT * FROM manual_activities" + ("" if include_removed else " WHERE removed = 0") + " ORDER BY id")
    df["activity_key"] = "manual#" + df["id"].astype(str)
    return df


def _blank(v) -> bool:
    return v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() in ("", "nan", "None")


def validate_manual(rec: dict, valid_strategies: set[str]) -> list[str]:
    errs = [f"'{f}' is required" for f in ("fiscal_year", "area", "strategy", "activity") if _blank(rec.get(f))]
    if not _blank(rec.get("strategy")) and str(rec["strategy"]).strip() not in valid_strategies:
        errs.append(f"strategy '{rec['strategy']}' is not an SFF strategy code (e.g., B.4)")
    if not _blank(rec.get("secondary")) and str(rec["secondary"]).strip() not in valid_strategies:
        errs.append(f"secondary '{rec['secondary']}' is not an SFF strategy code")
    return errs


def add_manual_activities(recs: list[dict], entered_by: str) -> int:
    """Insert activities added directly. A rec may also carry 'expected_result', which is saved as the
    activity's first status entry (Not started) so it shows on Activity Status right away."""
    ts = _now()
    cols = ["created", "updated", *MANUAL_COLS, "entered_by"]
    sql = f"INSERT INTO manual_activities ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})"
    with _connect() as con:
        for r in recs:
            cost = r.get("cost")
            cost = None if cost in (None, "") or pd.isna(cost) else float(cost)
            vals = [None if _blank(v := r.get(c)) else (cost if c == "cost" else str(v).strip()) for c in MANUAL_COLS]
            new_id = con.execute(sql, (ts, ts, *vals, entered_by)).lastrowid
            if not _blank(exp := r.get("expected_result")):
                con.execute("INSERT INTO activity_status (timestamp, activity_key, status, expected_result, entered_by) "
                            "VALUES (?, ?, 'Not started', ?, ?)", (ts, f"manual#{new_id}", str(exp).strip(), entered_by))
    return len(recs)


def update_manual_activities(rows: pd.DataFrame, entered_by: str) -> int:
    """rows: id plus any of MANUAL_COLS and 'removed'. Updates in place (updated timestamp + editor recorded)."""
    ts = _now()
    editable = [c for c in MANUAL_COLS + ["removed"] if c in rows.columns]
    with _connect() as con:
        for r in rows.to_dict("records"):
            vals = [None if pd.isna(r[c]) or r[c] == "" else (int(r[c]) if c == "removed" else r[c]) for c in editable]
            con.execute(f"UPDATE manual_activities SET {', '.join(f'{c} = ?' for c in editable)}, "
                        f"updated = ?, entered_by = ? WHERE id = ?", (*vals, ts, entered_by, int(r["id"])))
    return len(rows)


def _apply_activity_edits(a: pd.DataFrame) -> pd.DataFrame:
    """Reword activities and split cells that list several activities (see sff/activity_edits.py)."""
    from .activity_edits import ACTIVITY_SPLITS, ACTIVITY_TEXT
    if a.empty:
        return a
    if "activity_key" not in a:
        a = a.assign(activity_key=activity_key(a))
    for key, text in ACTIVITY_TEXT.items():
        a.loc[a["activity_key"] == key, "activity"] = text
    parts = []
    for key, items in ACTIVITY_SPLITS.items():
        src = a[a["activity_key"] == key]
        if src.empty:
            continue
        row = src.iloc[0]
        for i, (text, strategy) in enumerate(items, start=1):
            r = row.copy()
            r["activity"], r["strategy"], r["lever"] = text, strategy, strategy[0]
            r["activity_key"] = f"{key}/{i}"
            if i > 1:
                r["cost"] = None
                r["cost_raw"] = f"Included in the request total (${row['cost']:,.0f})" if pd.notna(row["cost"]) else None
            r["note"] = "; ".join(x for x in [str(row["note"]) if pd.notna(row["note"]) else "",
                                              f"Activity {i} of {len(items)} from one request"] if x)
            parts.append(r)
        a = a[a["activity_key"] != key]
    if parts:
        a = pd.concat([a, pd.DataFrame(parts)], ignore_index=True)
    return a


def all_activities(req: pd.DataFrame) -> pd.DataFrame:
    """Unified activity list: approved resource requests + activities added directly.
    Columns are aligned so status, completion, and reports treat both the same way."""
    a = _apply_activity_edits(activities(req).copy())
    a["activity_type"] = TYPE_REQUEST
    a["funding_source"] = ("Resource request – " + a["funding"]).where(a["funding"].notna(), "Resource request") \
        if "funding" in a else "Resource request"
    a["owner"] = None
    m = load_manual_activities()
    if not m.empty:
        m = m.assign(activity_type=TYPE_MANUAL, approved=True, approval_source="Added directly",
                     request=None, cost_raw=None, cost_is_text=False, vp_decision=None,
                     strategy_source="Entered by " + m["entered_by"].fillna("unknown"),
                     lever=m["strategy"].str[0])
        a = pd.concat([a, m[[c for c in m.columns
                             if c in set(a.columns) | {"activity_type", "funding_source", "owner", "rolled_from"}]]],
                      ignore_index=True)
    return _apply_strategy_changes(_apply_text_changes(a))


def _apply_text_changes(a: pd.DataFrame) -> pd.DataFrame:
    """Descriptions rewritten in the app (resource-request activities; activities added directly are edited in place)."""
    df = _q("SELECT activity_key, activity FROM activity_text ORDER BY id")
    if df.empty or a.empty:
        return a
    latest = df.groupby("activity_key").tail(1).set_index("activity_key")["activity"]
    hit = a["activity_key"].isin(latest.index) & a["activity_type"].ne(TYPE_MANUAL)
    if hit.any():
        a = a.copy()
        a.loc[hit, "activity"] = a.loc[hit, "activity_key"].map(latest).values
    return a


def set_activity_text(key: str, text: str, entered_by: str) -> int:
    return _insert("activity_text", ["timestamp", "activity_key", "activity", "entered_by"],
                   [(_now(), key, str(text).strip(), entered_by)])


# ------------------------------------------- rolling an activity over to the next school year
def next_fiscal_year(fy: str) -> str:
    return f"FY{int(str(fy)[2:]) + 1:02d}"


def fy_label(fy: str) -> str:
    """FY27 -> 2026-27."""
    n = int(str(fy)[2:])
    return f"20{n - 1:02d}-{n:02d}"


def rolled_over_keys(fy: str) -> set[str]:
    """Activities that already continue into school year fy (keys of the prior-year activities)."""
    df = _q("SELECT rolled_from FROM manual_activities WHERE removed = 0 AND fiscal_year = ? AND rolled_from IS NOT NULL",
            (fy,))
    return set(df["rolled_from"])


def roll_over_activity(r: dict, cost, funding_source: str, expected_result: str, entered_by: str) -> int:
    """Continue an activity in the next school year: a new activity there with the same area, division, strategy
    and description, linked back to the original. The original keeps its own status and results."""
    to_fy = next_fiscal_year(r["fiscal_year"])
    if r["activity_key"] in rolled_over_keys(to_fy):
        return 0
    ts = _now()
    clean = lambda v: None if _blank(v) else str(v).strip()
    vals = {"fiscal_year": to_fy, "area": clean(r.get("area")) or "Unknown", "division": clean(r.get("division")),
            "department": clean(r.get("department")), "strategy": clean(r.get("strategy")) or "",
            "secondary": clean(r.get("secondary")), "activity": clean(r.get("activity")),
            "funding_source": funding_source, "cost": None if cost in (None, "") or pd.isna(cost) else float(cost),
            "owner": clean(r.get("owner")),
            "note": f"Continued from {fy_label(r['fiscal_year'])}", "rolled_from": r["activity_key"]}
    cols = ["created", "updated", *vals, "entered_by"]
    with _connect() as con:
        new_id = con.execute(f"INSERT INTO manual_activities ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                             (ts, ts, *vals.values(), entered_by)).lastrowid
        if not _blank(expected_result):
            con.execute("INSERT INTO activity_status (timestamp, activity_key, status, expected_result, entered_by) "
                        "VALUES (?, ?, 'Not started', ?, ?)", (ts, f"manual#{new_id}", str(expected_result).strip(),
                                                              entered_by))
    return 1


# ------------------------------------------- strategy assignments made in the app
def load_strategy_changes() -> pd.DataFrame:
    """Latest strategy chosen in the app for each activity."""
    df = _q("SELECT id, timestamp, activity_key, strategy, secondary, entered_by FROM activity_strategy ORDER BY id")
    return df.groupby("activity_key").tail(1).set_index("activity_key") if not df.empty else df


def _apply_strategy_changes(a: pd.DataFrame) -> pd.DataFrame:
    ch = load_strategy_changes()
    if ch.empty or a.empty:
        return a
    hit = a["activity_key"].isin(ch.index)
    if hit.any():
        a = a.copy()
        keys = a.loc[hit, "activity_key"]
        a.loc[hit, "strategy"] = keys.map(ch["strategy"]).values
        a.loc[hit, "secondary"] = keys.map(ch["secondary"]).values
        a.loc[hit, "lever"] = a.loc[hit, "strategy"].str[0]
        a.loc[hit, "strategy_source"] = ("Assigned in the dashboard by " + keys.map(ch["entered_by"]).fillna("unknown")
                                         + " on " + keys.map(ch["timestamp"]).str[:10]).values
    return a


def set_activity_strategy(key: str, strategy: str, secondary: str | None, entered_by: str) -> int:
    """Assign an activity to a strategy (and optionally a second one it also supports)."""
    secondary = None if _blank(secondary) or secondary == strategy else str(secondary).strip()
    return _insert("activity_strategy", ["timestamp", "activity_key", "strategy", "secondary", "entered_by"],
                   [(_now(), key, str(strategy).strip(), secondary, entered_by)])


STATUS_FIELDS = ["status", "outcome", "expected_result", "result_rating"]


def load_activity_status() -> pd.DataFrame:
    return _q("SELECT timestamp, activity_key, status, outcome, expected_result, result_rating, entered_by "
              "FROM activity_status ORDER BY id")


def append_activity_status(rows: pd.DataFrame, entered_by: str) -> int:
    """rows: activity_key, status, outcome, expected_result, result_rating (each save stores all four, so the
    latest row per activity is its current state)."""
    clean = lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == "" else str(v).strip()
    return _insert("activity_status", ["timestamp", "activity_key", *STATUS_FIELDS, "entered_by"],
                   [(_now(), r["activity_key"], *[clean(r.get(f)) for f in STATUS_FIELDS], entered_by)
                    for r in rows.to_dict("records")])


def with_activity_status(req: pd.DataFrame, status: pd.DataFrame) -> pd.DataFrame:
    if "activity_key" not in req:
        req = req.assign(activity_key=activity_key(req))
    cols = ["activity_key", *STATUS_FIELDS]
    latest = status.groupby("activity_key").tail(1)[cols] if not status.empty else pd.DataFrame(columns=cols)
    out = req.merge(latest.rename(columns={"status": "activity_status"}), on="activity_key", how="left")
    out["activity_status"] = out["activity_status"].fillna("Not started")
    return out


def activity_completion(req_with_status: pd.DataFrame) -> pd.DataFrame:
    """Per strategy, activities only (approved requests + activities added directly), excluding ones marked
    Not funded / Cancelled:
      activities, completed, in_progress, pct_completed       -- is it happening?
      with_expected   activities that have an expected result written
      rated, met, partly_met, not_met, pct_met                -- did activities produce what was expected?
                      (pct_met = Met / rated; Too early to tell and blanks are not rated)
    Pass the output of with_activity_status(all_activities(req), ...)."""
    d = req_with_status[(req_with_status["strategy"] != "None") & req_with_status["approved"]].copy()
    d = d[~d["activity_status"].isin(["Not funded", "Cancelled"])]
    for c in ("expected_result", "result_rating"):
        if c not in d:
            d[c] = None
    d["_has_exp"] = d["expected_result"].fillna("").astype(str).str.strip().ne("")
    g = d.groupby("strategy").agg(
        activities=("activity_status", "size"),
        completed=("activity_status", lambda s: (s == "Completed").sum()),
        in_progress=("activity_status", lambda s: (s == "In progress").sum()),
        with_expected=("_has_exp", "sum"),
        rated=("result_rating", lambda s: s.isin(RATED).sum()),
        met=("result_rating", lambda s: (s == "Met").sum()),
        partly_met=("result_rating", lambda s: (s == "Partially met").sum()),
        not_met=("result_rating", lambda s: (s == "Not met").sum()))
    g["pct_completed"] = g["completed"] / g["activities"]
    g["pct_met"] = (g["met"] / g["rated"]).where(g["rated"] > 0)
    return g.reset_index()


# ================================================================ KPI summaries
TREND_THRESHOLD = 0.005   # +/-0.5 percentage points per year


def kpi_summary(results: pd.DataFrame, kpi_codes: list[str], targets: pd.DataFrame) -> pd.DataFrame:
    """One row per KPI: latest (All students), average annual change, trend, target status, largest equity gap."""
    rows = []
    tmap = targets.set_index("kpi_code")["target"].to_dict()
    for k in kpi_codes:
        r = results[results["kpi_code"] == k]
        allst = r[r["group"] == "All students"].sort_values("year")
        tgt = tmap.get(k)
        if allst.empty:
            rows.append({"kpi_code": k, "trend": "No data", "target": tgt})
            continue
        first, latest = allst.iloc[0], allst.iloc[-1]
        n = max(len(allst) - 1, 1)
        annual = (latest["value"] - first["value"]) / n
        trend = "Improving" if annual >= TREND_THRESHOLD else "Declining" if annual <= -TREND_THRESHOLD else "Flat"
        snap = r[(r["year"] == latest["year"]) & (r["group"] != "All students") & (r["group"] != "Unknown")]
        if "denominator" in snap and snap["denominator"].notna().any():
            snap = snap[pd.to_numeric(snap["denominator"], errors="coerce").fillna(0) >= GAP_MIN_N]
        gap_row = snap.loc[snap["value"].idxmin()] if not snap.empty else None
        rows.append({
            "kpi_code": k, "latest_year": latest["year"], "latest": latest["value"],
            "first_year": first["year"], "first": first["value"], "annual_change": annual, "trend": trend,
            "target": tgt,
            "vs_target": None if pd.isna(tgt) or tgt is None else ("Met" if latest["value"] >= tgt else "Below"),
            "largest_gap": None if gap_row is None else gap_row["value"] - latest["value"],
            "largest_gap_group": None if gap_row is None else gap_row["group"],
        })
    return pd.DataFrame(rows)


GOAL_COHORT_FALL = int(C.GOAL_TARGET_YEAR[:4]) - 4          # 2028-29 window closes -> entered Fall 2024
GOAL_COHORT = f"{GOAL_COHORT_FALL}-{str(GOAL_COHORT_FALL + 1)[2:]}"


def goal_to_date(results: pd.DataFrame, cohort: str = GOAL_COHORT) -> pd.DataFrame:
    """Five-year completion TO DATE for a cohort still inside its five-year window: everyone who has already
    earned a degree or certificate or completed 60+ degree-applicable units (all within five years). Rises until the window closes."""
    g = results[(results["kpi_code"] == "CMP-TD") & (results["year"] == cohort)]
    if g.empty:
        return pd.DataFrame()
    out = g[["group", "numerator", "denominator", "value"]].copy()
    out["numerator"] = pd.to_numeric(out["numerator"], errors="coerce")
    out["denominator"] = pd.to_numeric(out["denominator"], errors="coerce")
    out["gap_to_goal"] = C.GOAL_TARGET - out["value"]
    out["still_needed"] = (C.GOAL_TARGET * out["denominator"]).round() - out["numerator"]
    out["still_needed"] = out["still_needed"].clip(lower=0)
    order = {g: i for i, g in enumerate(C.EQUITY_GROUPS)}
    return out.sort_values("group", key=lambda s: s.map(order)).reset_index(drop=True)


def goal_pace(results: pd.DataFrame) -> pd.DataFrame:
    """Per student group: latest 5-year completion, gap to goal, pace needed vs. observed pace."""
    g = results[results["kpi_code"] == "GOAL"]
    if g.empty:
        return pd.DataFrame()
    out = []
    for grp, d in g.groupby("group"):
        d = d.sort_values("year")
        latest = d.iloc[-1]
        end_year = int(str(latest["year"])[:4]) + 1           # "2025-26" -> 2026
        years_left = max(C.GOAL_YEAR - end_year, 1)
        observed = (latest["value"] - d.iloc[0]["value"]) / max(len(d) - 1, 1)
        needed = max(C.GOAL_TARGET - latest["value"], 0) / years_left
        out.append({"group": grp, "latest_year": latest["year"], "latest": latest["value"],
                    "gap_to_goal": C.GOAL_TARGET - latest["value"], "years_left": years_left,
                    "needed_per_year": needed, "observed_per_year": observed,
                    "on_pace": "Goal met" if latest["value"] >= C.GOAL_TARGET
                    else ("On pace" if observed >= needed else "Behind pace")})
    df = pd.DataFrame(out)
    order = {g: i for i, g in enumerate(C.EQUITY_GROUPS)}
    return df.sort_values("group", key=lambda s: s.map(order)).reset_index(drop=True)
