"""Streamlit-only helpers: cached loaders and small UI pieces shared by pages."""
import pandas as pd
import streamlit as st

from sff import config as C
from sff import data as D


def _db_stamp() -> float:
    """The database file's modified time. Passing it to the cached loaders means a rebuilt database
    (python -m tools.build_db) is picked up on the next page load, without restarting Streamlit."""
    try:
        return C.DB_PATH.stat().st_mtime
    except OSError:
        return 0.0


@st.cache_data
def _matrix(db_stamp: float) -> pd.DataFrame:
    return D.load_matrix()


def matrix() -> pd.DataFrame:
    return _matrix(_db_stamp())


@st.cache_data
def _requests_raw_cached(db_stamp: float) -> pd.DataFrame:
    return D.load_requests_raw()


def _requests_raw() -> pd.DataFrame:
    return _requests_raw_cached(_db_stamp())


def requests(include_removed: bool = False) -> pd.DataFrame:
    """All requests with current VP decisions (approvals are re-read every run, not cached).
    Requests marked 'Removed (entered in error)' are left out unless include_removed (VP Approvals page)."""
    req = D.apply_approvals(_requests_raw(), D.load_approvals())
    return req if include_removed else D.drop_removed(req)


@st.cache_data
def _kpi_results(dimension: str, db_stamp: float):
    return D.load_kpi_results(dimension)


def kpi_results(dimension: str = "Race/ethnicity"):
    return _kpi_results(dimension, _db_stamp())


def group_order(groups, dimension: str = "Race/ethnicity") -> list[str]:
    """All students first; race groups in the standard order; other dimensions alphabetical."""
    gs = set(groups) - {"All students"}
    rest = [g for g in C.EQUITY_GROUPS if g in gs] if dimension == "Race/ethnicity" else sorted(gs)
    return ["All students"] * ("All students" in set(groups)) + rest + sorted(gs - set(rest))


def kpi_source_note(is_sample: bool):
    if is_sample:
        sample_banner()
    else:
        st.caption(f"KPI source: {D.kpi_source()}. Year = entering fall cohort (e.g., 2024-25 = Fall 2024); a cohort "
                   f"appears only after enough time has passed for the measure. Groups under {C.MIN_CELL_SIZE} "
                   "students are suppressed.")


def reviews() -> pd.DataFrame:  # not cached: changes when ratings are saved
    return D.load_reviews()


def current_matrix() -> pd.DataFrame:
    return D.with_current_status(matrix(), reviews())


def fiscal_years() -> list[str]:
    return sorted(requests()["fiscal_year"].unique())


def fy_filter(key: str, multi: bool = True):
    years = fiscal_years()
    if multi:
        return st.multiselect("Fiscal year", years, default=years, key=key)
    return st.selectbox("Fiscal year", years, index=len(years) - 1, key=key)


def areas() -> list[str]:
    loaded = set(requests()["area"])
    return [a for a in C.AREAS if a in loaded] + sorted(loaded - set(C.AREAS))


def area_filter(key: str) -> list[str]:
    a = areas()
    return st.multiselect("Area", a, default=a, key=key)


def approved_note():
    st.caption("Activities = resource requests with **VP/area approval** (source file or **VP Approvals** page) "
               "**plus** activities added directly on the **Add Activities** page (grant-funded, existing budget, "
               "no-cost work). Requests awaiting approval are not counted.")


def status_badge(status: str) -> str:
    return f"{C.STATUS_ICONS.get(status, '')} {status}"


def sample_banner():
    st.warning("**Sample data.** KPI values shown are synthetic placeholders. To load real results, put IERPG's "
               "student-level file (name containing *KPI - Student Level Report*) or `kpi_results.csv` in "
               "`data/source`, then rerun `python -m tools.build_db` — its output says which KPI source it used.",
               icon="⚠️")


def lever_filter(key: str) -> list[str]:
    opts = [f"{k}. {v}" for k, v in C.LEVERS.items()]
    chosen = st.multiselect("Lever", opts, default=opts, key=key)
    return [c[0] for c in chosen]


RESULTS_HELP = ("**Expected result** – what this activity should produce, written as a countable target "
                "(e.g., *“500 flagged students contacted; 60% re-enroll next term”*). Set it at the start of the year.  \n"
                "**Result vs. expected** – at mid-year or year-end, compare what happened with the expected result: "
                "Met, Partially met, Not met, or Too early to tell. Put the actual numbers in **Outcome / evidence**.")
EDIT_COLS = ["expected_result", "activity_status", "result_rating", "outcome"]


def activity_status_editor(acts: pd.DataFrame, key: str, show_strategy: bool = False):
    """Editable table: Activity (pinned, read-only) then the four editable columns — Expected result, Status,
    Result vs. expected, Outcome; everything else is read-only. `acts` must come from D.with_activity_status(D.all_activities(...))."""
    if acts.empty:
        st.info("No approved activities match these filters.")
        return
    done = int((acts["activity_status"] == "Completed").sum())
    n_man = int((acts["activity_type"] == D.TYPE_MANUAL).sum()) if "activity_type" in acts else 0
    has_exp = acts["expected_result"].fillna("").astype(str).str.strip().ne("")
    rating = acts["result_rating"].fillna("")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Activities", len(acts), help=(f"{n_man} added directly, {len(acts) - n_man} approved requests"
                                              if n_man else None))
    c2.metric("Completed", f"{done} of {len(acts)}")
    c3.metric("Have an expected result", f"{int(has_exp.sum())} of {len(acts)}")
    rated = rating.isin(D.RATED)
    c4.metric("Met expected result", f"{int((rating == 'Met').sum())} of {int(rated.sum())} rated" if rated.any() else "None yet")
    with st.expander("What goes in Expected result and Result vs. expected?"):
        st.markdown(RESULTS_HELP)
    who = st.text_input("Your name (required to save)", key=f"{key}_who",
                        help="Each save is logged with your name and the time; earlier entries are kept.")
    one, many = st.tabs(["✏️ Update one activity", "▦ Update several in a table"])
    with one:
        _activity_form(acts, key, who)
    with many:
        _activity_table(acts, key, who, show_strategy)


def _activity_form(acts: pd.DataFrame, key: str, who: str):
    """Pick one activity, see it in full, and update its four fields with ordinary inputs."""
    acts = acts.reset_index(drop=True)
    icon = {"Completed": "✔", "In progress": "◐", "Not started": "○", "Not funded": "–", "Cancelled": "✕"}
    txt = lambda v: "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v)
    label = {r.activity_key: f"{icon.get(r.activity_status, '○')} {txt(r.strategy) or '—'} · "
                             f"{txt(r.division) or r.area} · {txt(r.activity)[:110]}{'…' if len(txt(r.activity)) > 110 else ''}"
             for r in acts.itertuples()}
    k = st.selectbox("Activity (type to search)", list(label), format_func=label.get, key=f"{key}_pick")
    r = acts[acts["activity_key"] == k].iloc[0]
    with st.container(border=True):
        st.markdown(f"**{r['activity']}**")
        cost = (f"${r['cost']:,.0f}" if pd.notna(r["cost"]) else txt(r.get("cost_raw")) or "—")
        st.caption(f"Strategy {txt(r['strategy']) or '—'} · {r['fiscal_year']} · {r['area']} · {txt(r['division'])} "
                   f"{('· ' + txt(r.get('department'))) if txt(r.get('department')) else ''}  \n"
                   f"Resource request: {txt(r['request']) or '(added directly)'} · Cost: {cost} · {txt(r['funding_source'])}")
    with st.form(f"{key}_form_{k}", border=False):
        exp = st.text_area("Expected result (what this activity should produce, with a number)",
                           value=txt(r["expected_result"]), height=80,
                           placeholder="e.g., 30 departments complete program review in CIM by June 2026")
        c1, c2 = st.columns(2)
        cur = r["activity_status"] if r["activity_status"] in D.ACTIVITY_STATUSES else D.ACTIVITY_STATUSES[0]
        status = c1.selectbox("Status", D.ACTIVITY_STATUSES, index=D.ACTIVITY_STATUSES.index(cur))
        ratings = ["(not rated yet)", *D.RESULT_RATINGS]
        rr = r["result_rating"] if r["result_rating"] in D.RESULT_RATINGS else ratings[0]
        rating = c2.selectbox("Result vs. expected", ratings, index=ratings.index(rr))
        outcome = st.text_area("Outcome / evidence (what actually happened, with numbers)",
                               value=txt(r["outcome"]), height=80)
        saved = st.form_submit_button("Save this activity", type="primary")
    if saved:
        rating = None if rating == ratings[0] else rating
        if not who.strip():
            st.error("Type your name in **Your name** above, then click Save again.")
        elif rating in D.RATED and not exp.strip():
            st.error("Write the **Expected result** before rating the result against it.")
        else:
            D.append_activity_status(pd.DataFrame([{"activity_key": k, "status": status, "outcome": outcome,
                                                    "expected_result": exp, "result_rating": rating}]), who)
            st.success("Saved.")
            st.rerun()


def _activity_table(acts: pd.DataFrame, key: str, who: str, show_strategy: bool):
    st.caption("Click a ✏️ cell to type or pick from its list, scroll right for all four ✏️ columns, then click **Save** "
               "below the table.")
    cols = ["activity_key", "activity", *EDIT_COLS] + (["strategy"] if show_strategy else []) + \
           ["activity_type", "funding_source", "fiscal_year", "area", "division", "department", "request", "cost"]
    edit = acts[cols].copy()
    for c in ("expected_result", "outcome"):
        edit[c] = edit[c].fillna("")
    edit["result_rating"] = edit["result_rating"].where(edit["result_rating"].isin(D.RESULT_RATINGS), None)
    edited = st.data_editor(
        edit, hide_index=True, width="stretch", key=f"{key}_editor",
        disabled=[c for c in cols if c not in EDIT_COLS],
        column_config={
            "activity_key": None,
            "expected_result": st.column_config.TextColumn("✏️ Expected result", width="medium",
                                                           help="What the activity should produce (countable)."),
            "activity_status": st.column_config.SelectboxColumn("✏️ Status", options=D.ACTIVITY_STATUSES,
                                                                required=True, width="medium"),
            "result_rating": st.column_config.SelectboxColumn("✏️ Result vs. expected", options=D.RESULT_RATINGS,
                                                              width="medium"),
            "outcome": st.column_config.TextColumn("✏️ Outcome / evidence", width="medium",
                                                   help="What actually happened, with numbers."),
            "activity": st.column_config.TextColumn("Activity", width="medium", pinned=True,
                                                    help="Hover or widen the column to read the full activity."),
            "strategy": "Strategy", "fiscal_year": "FY", "area": "Area", "division": "Division",
            "department": "Dept", "request": st.column_config.TextColumn("Resource request", width="medium"),
            "cost": st.column_config.NumberColumn("Cost", format="$%,.0f"),
            "activity_type": "Type", "funding_source": "Funding",
        },
    )
    norm = lambda s: s.fillna("").astype(str).str.strip()
    chg = edited.merge(edit, on="activity_key", suffixes=("", "_old"))
    changed = pd.Series(False, index=chg.index)
    for c in EDIT_COLS:
        changed |= norm(chg[c]) != norm(chg[f"{c}_old"])
    chg = chg[changed]
    bad = chg[chg["result_rating"].isin(D.RATED) & norm(chg["expected_result"]).eq("")]
    if not bad.empty:
        st.error(f"{len(bad)} row(s) rate the result but have no **Expected result**. Write the expected result "
                 "first so the rating has something to be compared with.")
    if st.button(f"Save {len(chg)} change(s)", type="primary", disabled=chg.empty or not who or not bad.empty,
                 key=f"{key}_save"):
        D.append_activity_status(chg.rename(columns={"activity_status": "status"})[
            ["activity_key", "status", "outcome", "expected_result", "result_rating"]], who)
        st.success(f"Saved {len(chg)} update(s).")
        st.rerun()
    if not chg.empty and not who:
        st.caption("⬆️ Enter your name to enable Save.")
