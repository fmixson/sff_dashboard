"""Forms shared by "What we're doing about it" (in pop-ups) and "Update activities" (on the page):
update an activity, continue it next school year, add a new one. Each save records the person's name and the time."""
import pandas as pd
import streamlit as st

from sff import config as C, data as D

STATUS_ICON = {"Not started": "○", "In progress": "◐", "Completed": "●", "Not funded": "–", "Cancelled": "✕"}
ROLL_FUNDING = "Ongoing (continued from the prior year)"


def txt(v) -> str:
    """Text for display; blanks (None, NaN, pandas NA) become ""."""
    try:
        if v is None or pd.isna(v):
            return ""
    except (TypeError, ValueError):   # lists and arrays are not blanks
        pass
    return str(v)


def current_fy() -> str:
    """The school year running today (it starts July 1): FY27 = 2026-27."""
    t = pd.Timestamp.today()
    return f"FY{(t.year + (1 if t.month >= 7 else 0)) % 100:02d}"


def money(r) -> str:
    if pd.notna(r["cost"]):
        return f"${r['cost']:,.0f}"
    raw = r.get("cost_raw")
    return str(raw) if isinstance(raw, str) and raw.strip() else "no cost listed"


def who(r) -> str:
    parts = [r["division"] if isinstance(r["division"], str) else r["area"]]
    dept = r.get("department")
    if isinstance(dept, str) and dept.strip() and dept.strip().lower() not in ("division", str(r["division"]).lower()):
        parts.append(dept.strip())
    return " · ".join(parts)


def _name_ok(name: str) -> bool:
    if not name.strip():
        st.error("Please type your name.")
        return False
    st.session_state["who"] = name.strip()
    return True


def edit_form(r: dict, labels: dict, fk: str = "upd"):
    """Strategy, description, status and results. Removing is offered only for activities added directly."""
    k = f"{fk}_{r['activity_key']}"
    manual = r.get("activity_type") == D.TYPE_MANUAL
    with st.form(k):
        codes = list(labels)
        cur_s = r["strategy"] if r["strategy"] in labels else None
        cur_2 = r.get("secondary") if r.get("secondary") in labels else None
        new_s = st.selectbox("Strategy it carries out (change it to move the activity)", codes, format_func=labels.get,
                             index=codes.index(cur_s) if cur_s else None, placeholder="Not tied to a strategy yet",
                             key=f"{k}_s")
        new_2 = st.selectbox("Also supports (optional)", ["", *codes], format_func=lambda c: labels.get(c, "None"),
                             index=(codes.index(cur_2) + 1) if cur_2 else 0, key=f"{k}_s2")
        new_text = st.text_area("Activity (what is being done)", value=txt(r["activity"]), height=80, key=f"{k}_t")
        if manual:
            new_cost = st.number_input("Cost ($)", min_value=0.0, step=500.0, key=f"{k}_c",
                                       value=float(r["cost"]) if pd.notna(r["cost"]) else None)
        status = st.radio("How is it going?", D.ACTIVITY_STATUSES, horizontal=True, key=f"{k}_st",
                          index=D.ACTIVITY_STATUSES.index(r["activity_status"])
                          if r["activity_status"] in D.ACTIVITY_STATUSES else 0)
        exp = st.text_area("Expected result: what should this produce? (with a number)", key=f"{k}_e",
                           value=txt(r.get("expected_result")), height=70,
                           placeholder="e.g., 200 students tutored; 75% pass the course")
        ratings = ["Not yet", *D.RESULT_RATINGS]
        rr = r.get("result_rating") if r.get("result_rating") in D.RESULT_RATINGS else "Not yet"
        rating = st.radio("Did it meet the expected result?", ratings, horizontal=True, index=ratings.index(rr),
                          key=f"{k}_r")
        outcome = st.text_area("What actually happened (with numbers)", value=txt(r.get("outcome")), height=70,
                               key=f"{k}_o")
        remove = st.checkbox("Remove this activity (it was added by mistake)", key=f"{k}_x") if manual else False
        who_ = st.text_input("Your name *", value=st.session_state.get("who", ""), key=f"{k}_w")
        if st.form_submit_button("Save", type="primary"):
            rating = None if rating == "Not yet" else rating
            if rating in D.RATED and not exp.strip():
                st.error("Write the expected result first, so the result has something to be compared with.")
            elif not remove and not new_text.strip():
                st.error("The activity description can't be empty.")
            elif _name_ok(who_):
                name = who_.strip()
                text_changed = new_text.strip() != txt(r["activity"]).strip()
                if manual:
                    D.update_manual_activities(pd.DataFrame([{"id": int(str(r["activity_key"]).split("#")[1]),
                                                              "activity": new_text.strip(), "cost": new_cost,
                                                              "removed": int(remove)}]), name)
                elif text_changed:
                    D.set_activity_text(r["activity_key"], new_text.strip(), name)
                moved = bool(not remove and new_s and (new_s != cur_s or (new_2 or None) != (cur_2 or None)))
                if moved:
                    D.set_activity_strategy(r["activity_key"], new_s, new_2, name)
                if not remove:
                    D.append_activity_status(pd.DataFrame([{"activity_key": r["activity_key"], "status": status,
                                                            "outcome": outcome, "expected_result": exp,
                                                            "result_rating": rating}]), name)
                st.session_state["flash"] = ("Activity removed." if remove else
                                             f"Update saved. Moved to {new_s}." if moved and new_s != cur_s else
                                             "Update saved.")
                st.session_state["open"] = new_s if moved else r["strategy"]
                st.rerun()


def rollover_form(r: dict, labels: dict, fk: str = "roll"):
    """Continue the activity in the next school year (a linked copy there; this year's results stay here)."""
    k = f"{fk}_{r['activity_key']}"
    nxt = D.next_fiscal_year(r["fiscal_year"])
    nxt_label = D.fy_label(nxt)
    if r["activity_key"] in D.rolled_over_keys(nxt):
        st.info(f"Already continued in {nxt_label}. Switch the school year to {nxt_label} to update it there.")
        return
    if r.get("activity_status") in ("Cancelled", "Not funded"):
        st.info(f"This activity is marked {r['activity_status']}, so it can't be continued.")
        return
    st.caption(f"Adds the same activity, under the same strategy, to {nxt_label}. This year's status and results "
               "stay with this year.")
    with st.form(k):
        c1, c2 = st.columns(2)
        ncost = c1.number_input(f"Cost in {nxt_label} ($, if any)", min_value=0.0, step=500.0, key=f"{k}_c",
                                value=float(r["cost"]) if pd.notna(r["cost"]) else None)
        nfund = c2.selectbox("Paid for by", [ROLL_FUNDING, *D.FUNDING_SOURCES], key=f"{k}_f")
        nexp = st.text_input(f"Expected result in {nxt_label}", value=txt(r.get("expected_result")), key=f"{k}_e",
                             placeholder="e.g., 200 students tutored; 75% pass the course")
        nwho = st.text_input("Your name *", value=st.session_state.get("who", ""), key=f"{k}_w")
        if st.form_submit_button(f"Continue in {nxt_label}", type="primary"):
            if r["strategy"] not in labels:
                st.error("Choose a strategy for this activity first, save it, then continue it.")
            elif _name_ok(nwho):
                D.roll_over_activity(r, ncost, nfund, nexp, nwho.strip())
                st.session_state["flash"] = f"Continued in {nxt_label}."
                st.session_state["open"] = r["strategy"]
                st.rerun()


def add_form(fy: str, labels: dict, code: str | None = None, area: str | None = None, division: str | None = None,
             fk: str = "add"):
    st.caption(f"For the {D.fy_label(fy)} school year. Use this for work that is not a funded resource request "
               "(grant-funded, existing budget, or no-cost changes).")
    with st.form(fk):
        strategy = st.selectbox("Which strategy does it carry out? *", list(labels), format_func=labels.get,
                                index=list(labels).index(code) if code in labels else None,
                                placeholder="Choose a strategy", key=f"{fk}_s")
        activity = st.text_area("What will be done? *", height=80, key=f"{fk}_t",
                                placeholder="e.g., Offer corequisite support sections for transfer-level English")
        c1, c2 = st.columns(2)
        area_ = c1.selectbox("Area *", C.AREAS, index=C.AREAS.index(area) if area in C.AREAS else 0, key=f"{fk}_a")
        division_ = c2.text_input("Division / department", value=division or "", key=f"{fk}_d")
        exp = st.text_input("Expected result (what it should produce, with a number)", key=f"{fk}_e",
                            placeholder="e.g., 12 sections; 70% of students pass transfer-level English")
        d1, d2 = st.columns(2)
        funding = d1.selectbox("Paid for by", D.FUNDING_SOURCES, key=f"{fk}_f")
        cost = d2.number_input("Cost ($, if any)", min_value=0.0, step=500.0, value=None, key=f"{fk}_c")
        who_ = st.text_input("Your name *", value=st.session_state.get("who", ""), key=f"{fk}_w")
        if st.form_submit_button("Add activity", type="primary"):
            rec = {"fiscal_year": fy, "area": area_, "division": division_.strip() or None, "strategy": strategy,
                   "activity": activity.strip(), "expected_result": exp.strip(), "funding_source": funding,
                   "cost": cost}
            errs = D.validate_manual(rec, set(labels)) + ([] if who_.strip() else ["your name is required"])
            if errs:
                st.error("Not saved: " + "; ".join(errs).replace("'", ""))
            else:
                st.session_state["who"] = who_.strip()
                D.add_manual_activities([rec], who_.strip())
                st.session_state["flash"] = f"Added to {strategy}."
                st.session_state["open"] = strategy
                st.rerun()
