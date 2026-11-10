"""Page 3: find one activity with drop-downs (school year, lever, area, division, strategy) and update it on the page."""
import pandas as pd
import streamlit as st

from sff import config as C, data as D
from simple import forms as F, theme as T
from views import common

ALL_LEVERS, ALL_AREAS, ALL_DIVS, ALL_STRATS = "All levers", "All areas", "All divisions", "All strategies"
UNTIED = "Not tied to a strategy"

T.banner("Update activities", "Pick an activity with the drop-downs, then update it, change it, or continue it next year")

if msg := st.session_state.pop("flash", None):
    st.toast(msg, icon="✅")

strat = D.strategies(common.matrix())
labels = {r.code: f"{r.code} – {r.element}" for r in strat.itertuples()}
acts = D.with_activity_status(D.all_activities(common.requests()), D.load_activity_status())
acts["_div"] = acts["division"].map(lambda v: F.txt(v).strip()).replace({"None": "", "nan": "", "NaN": ""})  # blank = ""
acts["_lever"] = acts["strategy"].where(acts["strategy"].isin(labels), None).str[0]
CURRENT_FY = F.current_fy()
years = sorted(set(acts["fiscal_year"]) | {CURRENT_FY}, reverse=True)


def pick(where, label, options, key, fmt=None, **kw):
    """A drop-down whose choices depend on the ones before it: a choice that no longer fits starts over."""
    if key in st.session_state and st.session_state[key] not in options:
        del st.session_state[key]
    return where.selectbox(label, options, key=key, format_func=fmt or (lambda x: x), **kw)


# ------------------------------------------------------------------ the drop-downs, each narrowing the next
r1 = st.columns(3)
fy = pick(r1[0], "School year", years, "m_fy", D.fy_label,
          **({} if "m_fy" in st.session_state else {"index": years.index(CURRENT_FY)}))
a = acts[acts["fiscal_year"] == fy]

lever_opts = [ALL_LEVERS, *C.LEVERS] + ([UNTIED] if a["_lever"].isna().any() else [])
lever = pick(r1[1], "Lever", lever_opts, "m_lever",
             lambda x: f"{x}. {C.LEVERS[x]}" if x in C.LEVERS else x)
if lever == UNTIED:
    a = a[a["_lever"].isna()]
elif lever != ALL_LEVERS:
    a = a[a["_lever"] == lever]

area = pick(r1[2], "Area", [ALL_AREAS, *sorted({F.txt(x).strip() for x in a["area"]} - {""})], "m_area")
if area != ALL_AREAS:
    a = a[a["area"] == area]

r2 = st.columns([1, 2])
division = pick(r2[0], "Division", [ALL_DIVS, *sorted(x for x in a["_div"].unique() if x)], "m_div")
if division != ALL_DIVS:
    a = a[a["_div"] == division]

strat_opts = [ALL_STRATS, *[c for c in labels if c in set(a["strategy"])]]
strategy = pick(r2[1], "Strategy", strat_opts, "m_strat", lambda c: labels.get(c, c))
if strategy != ALL_STRATS:
    a = a[a["strategy"] == strategy]

a = a.sort_values(["strategy", "cost"], ascending=[True, False], na_position="last").reset_index(drop=True)


def act_label(k):
    r = a.loc[a["activity_key"] == k].iloc[0]
    text = str(r["activity"])
    text = text if len(text) <= 95 else text[:92] + "…"
    return f"{r['strategy'] if r['strategy'] in labels else 'No strategy'} · {F.who(r)} · {text} · {F.money(r)}"


# a click in the table below picks the activity too (the table resets whenever the drop-downs change)
table_key = "m_table_" + str(abs(hash((fy, lever, area, division, strategy))))
rows = st.session_state.get(table_key, {}).get("selection", {}).get("rows", []) if table_key in st.session_state else []
if rows and st.session_state.get("m_table_applied") != (table_key, tuple(rows)) and rows[0] < len(a):
    st.session_state["m_act"] = a.loc[rows[0], "activity_key"]
    st.session_state["m_table_applied"] = (table_key, tuple(rows))

keys = list(a["activity_key"])
if "m_act" in st.session_state and st.session_state["m_act"] not in keys:
    del st.session_state["m_act"]
chosen = st.selectbox(f"Activity ({len(keys)} {'matches' if len(keys) == 1 else 'match'} these choices)", keys,
                      format_func=act_label, key="m_act", placeholder="Choose an activity, or click one in the list below",
                      **({} if "m_act" in st.session_state else {"index": None}))

# ------------------------------------------------------------------ the chosen activity
if chosen:
    r = a.loc[a["activity_key"] == chosen].iloc[0].to_dict()
    lv = r["strategy"][0] if r["strategy"] in labels else None
    st.write("")
    T.banner(r["activity"], labels.get(r["strategy"], "Not tied to a strategy yet"))
    nxt = D.next_fiscal_year(fy)
    linked = []
    if F.txt(r.get("rolled_from")).strip():
        linked.append(f"continued from {D.fy_label('FY%02d' % (int(fy[2:]) - 1))}")
    if chosen in D.rolled_over_keys(nxt):
        linked.append(f"continues in {D.fy_label(nxt)}")
    t1, t2, t3, t4 = st.columns(4)
    t1.markdown(T.tile("Lever", f"{lv}" if lv else "—", C.LEVERS.get(lv, "no strategy yet")), unsafe_allow_html=True)
    t2.markdown(T.tile("Who", r["area"], F.who(r)), unsafe_allow_html=True)
    t3.markdown(T.tile("Cost", F.money(r), F.txt(r.get("funding_source")) or ""), unsafe_allow_html=True)
    t4.markdown(T.tile("Status", f"{F.STATUS_ICON.get(r['activity_status'], '○')} {r['activity_status']}",
                       " · ".join(linked) or ("Added directly" if r.get("activity_type") == D.TYPE_MANUAL
                                              else "Funded resource request")), unsafe_allow_html=True)
    st.write("")
    u, rl = st.tabs(["Update or change it", f"Continue it in {D.fy_label(nxt)}"])
    with u:
        F.edit_form(r, labels, fk="m_upd")
        if r.get("activity_type") != D.TYPE_MANUAL:
            st.caption("This activity comes from a funded resource request, so its cost is the funded amount and it "
                       "can't be removed here. You can still reword it, move it to another strategy, and record "
                       "how it's going.")
    with rl:
        F.rollover_form(r, labels, fk="m_roll")

# ------------------------------------------------------------------ everything that matches the drop-downs
st.write("")
T.band(f"{len(a):,} activities · ${a['cost'].sum():,.0f}",
       "Everything that matches the drop-downs above. Click a row to pick that activity.")
if a.empty:
    st.info("Nothing matches these choices. Try “All” in one of the drop-downs.")
else:
    view = pd.DataFrame({
        "Strategy": a["strategy"].where(a["strategy"].isin(labels), "—"),
        "Activity": a["activity"],
        "Division / dept": a.apply(F.who, axis=1),
        "Cost": a["cost"],
        "Status": a["activity_status"],
        "Result": a["result_rating"].fillna(""),
    })
    st.dataframe(view, hide_index=True, width="stretch", on_select="rerun", selection_mode="single-row",
                 key=table_key, height=min(38 + 35 * len(view), 460),
                 column_config={"Cost": st.column_config.NumberColumn(format="dollar"),
                                "Activity": st.column_config.TextColumn(width="large")})

with st.expander("＋ Add a new activity"):
    F.add_form(fy, labels, strategy if strategy in labels else None, area if area in C.AREAS else None,
               division if division != ALL_DIVS else None, fk="m_add")
