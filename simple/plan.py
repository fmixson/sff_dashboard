"""Page 2: the SFF strategies and the funded activities under each, as a plain list."""
import pandas as pd
import streamlit as st

from sff import config as C, data as D
from simple import forms as F, theme as T
from views import common

MUTED = T.GRAY
LEVER_PLAIN = {
    "A": "Helping more students enroll and get off to a strong start",
    "B": "Helping students stay on track and finish",
    "C": "Connecting students to good jobs and four-year universities",
    "D": "Keeping the college strong so it can serve students",
}
FY_LABEL = {"FY26": "2025-26", "FY27": "2026-27", "FY28": "2027-28"}
STATUS_ICON = F.STATUS_ICON

T.banner("What we're doing about it", "Cerritos College · Students First Framework levers, strategies and activities")
st.markdown("The Students First Framework has **4 big goals (levers)** and **25 strategies**. Each year the college "
            "funds **activities** that carry out the strategies. Open a strategy to see its activities or **update** "
            "how one is going. To add an activity, use **Update activities** in the menu.")

strat = D.strategies(common.matrix())
labels = {r.code: f"{r.code} – {r.element}" for r in strat.itertuples()}
acts = D.with_activity_status(D.all_activities(common.requests()), D.load_activity_status())
CURRENT_FY = F.current_fy()
years = sorted(set(acts["fiscal_year"]) | {CURRENT_FY}, reverse=True)
FY_LABEL.update({y: D.fy_label(y) for y in years})

f1, f2, f4 = st.columns([1.2, 2.6, 1.2])
fy = f1.radio("School year", years, format_func=lambda y: FY_LABEL.get(y, y), horizontal=True,
              index=years.index(CURRENT_FY), key="fy")
rolled_next = D.rolled_over_keys(D.next_fiscal_year(fy))
q = f2.text_input("Search activities", placeholder="e.g., tutoring, dual enrollment, nursing")
name = f4.text_input("Your name", key="who", placeholder="Needed to save changes",
                     help="Every change is saved with your name and the time; earlier entries are kept.")


_txt, money, who = F.txt, F.money, F.who


# ------------------------------------------------------------------ pop-up forms (shared with "Update activities")
@st.dialog("Update activity", width="large")
def update_dialog(r: dict):
    st.markdown(f"**{r['activity']}**")
    st.caption(f"{labels.get(r['strategy'], 'Not tied to a strategy yet')}  \n{who(r)} · {money(r)}")
    F.edit_form(r, labels)
    st.markdown(f"**Continue this activity in {D.fy_label(D.next_fiscal_year(r['fiscal_year']))}**")
    F.rollover_form(r, labels)


if msg := st.session_state.pop("flash", None):
    st.toast(msg, icon="✅")

a = acts[acts["fiscal_year"] == fy].copy()
_scope = ""   # area/division filters removed 11/10 at F. Mixson's request (they live on "Update activities")
if q.strip():
    hay = (a["activity"].fillna("") + " " + a["request"].fillna("") + " " + a["division"].fillna("") + " "
           + a["department"].fillna("").astype(str))
    a = a[hay.str.contains(q.strip(), case=False, regex=False)]

n_with = a.loc[a["strategy"].isin(strat["code"]), "strategy"].nunique()
if q.strip():
    st.markdown(f"**{len(a):,} {FY_LABEL.get(fy, fy)} activities** match “{q.strip()}” "
                f"(${a['cost'].sum():,.0f}), under **{n_with} strategies**. Clear the search box to see everything.")
else:
    st.markdown(f"In **{FY_LABEL.get(fy, fy)}**{(' for **' + _scope + '**') if _scope else ''} there are **{len(a):,} activities** "
                f"(**${a['cost'].sum() / 1e6:,.1f} million**) across **{n_with} of {len(strat)} strategies**.")


def activity_row(r, key):
    c1, c2 = st.columns([9, 1.3], vertical_alignment="center")
    extra = []
    if _txt(r.get("expected_result")).strip():
        extra.append(f"Expected: {_txt(r['expected_result'])}")
    if r.get("result_rating") in D.RESULT_RATINGS:
        extra.append(f"Result: {r['result_rating']}")
    if _txt(r.get("rolled_from")).strip():
        added = f" · continued from {D.fy_label('FY%02d' % (int(fy[2:]) - 1))}"
    elif r.get("activity_type") == D.TYPE_MANUAL:
        added = " · added directly"
    else:
        added = ""
    if r["activity_key"] in rolled_next:
        added += f" · continues in {D.fy_label(D.next_fiscal_year(fy))}"
    c1.markdown(f"{r['activity']}  \n<span style='color:{MUTED};font-size:14px'>{who(r)} · {money(r)}{added} · "
                f"<b>{STATUS_ICON.get(r['activity_status'], '○')} {r['activity_status']}</b></span>"
                + (f"  \n<span style='color:{MUTED};font-size:13px'>{' · '.join(extra)}</span>" if extra else ""),
                unsafe_allow_html=True)
    if c2.button("Update", key=key, width="stretch"):
        update_dialog(r.to_dict())


# ------------------------------------------------------------------ lever KPI cards (one value per student group)
KPI_PLAIN = {
    "A-K1": "Made an education plan in their first year", "A-K2": "Took a full load (15+ units) in their first fall",
    "A-K3": "Took 30+ units in their first year", "B-K1": "Passed all of their first five classes",
    "B-K2": "Earned 15+ units in their first year", "B-K3": "CTE students who earned CTE units in their first year",
    "B-K4": "Earned 30+ units by the end of their second year", "B-K5": "Earned 45+ units by the end of their third year",
    "B-K6": "Passed college-level math and English in their first year", "B-K7": "Came back in spring after their first fall",
    "B-K8": "Came back for a second fall", "B-K9": "Still enrolled in their second spring",
    "B-K10": "Graduated within two years", "C-K1": "CTE students satisfied and employed / earning more",
    "C-K2": "Enrolled at a four-year university within two years of completing",
    "D-K1": "College reserves and revenues", "D-K2": "Pay compared with similar colleges",
    "D-K3": "Salaries as a share of the overall budget",
}
NO_DATA = {"C": "Not loaded yet. These come from the CTE outcomes survey and transfer data.",
           "D": "Not loaded yet. These come from Fiscal Services and Human Resources."}
kres, _ = common.kpi_results()
kall = kres[kres["group"] == "All students"]
cohorts = sorted(kres.loc[kres["kpi_code"] == "CMP-TD", "year"].unique()) or sorted(kall["year"].unique())
kmeta = D.kpis(common.matrix())
GOOD, BAD = T.GREEN, T.RED


def kpi_card(code, label):
    vals = {}
    for y in cohorts:
        d = kall[(kall["kpi_code"] == code) & (kall["year"] == y)]
        vals[y] = None if d.empty else float(d["value"].iloc[0])
    have = [y for y in cohorts if vals[y] is not None]
    pts = (vals[have[-1]] - vals[have[-2]]) * 100 if len(have) >= 2 else None
    rows = ""
    for y in cohorts:
        v = vals[y]
        if v is None:
            rows += (f"<div style='display:flex;justify-content:space-between;align-items:baseline;padding:4px 0;"
                     f"color:{T.GRAY};font-style:italic'><span>Started Fall {y[:4]}</span><span>not yet</span></div>")
        else:
            col = T.trend_color(pts) if have and y == have[-1] else T.NAVY
            rows += (f"<div style='display:flex;justify-content:space-between;align-items:baseline;padding:4px 0;"
                     f"border-bottom:1px solid #F0F0F0'><span style='font-size:0.95rem'>Started Fall {y[:4]}</span>"
                     f"<span style='font-size:1.9rem;font-weight:800;color:{col}'>{v:.0%}</span></div>")
    pill = T.trend_pill(pts, "the group before") if pts is not None else ""
    return T.kpi_card(label, rows + (f"<div style='margin-top:10px'>{pill}</div>" if pill else ""),
                      accent=T.trend_color(pts), muted=not have)


def lever_kpis(lever):
    codes = [c for c in kmeta.loc[kmeta["lever"] == lever, "code"]]
    if not codes:
        return
    T.band("How students are doing on this lever")
    if lever in NO_DATA and kall[kall["kpi_code"].isin(codes)].empty:
        st.caption(" · ".join(KPI_PLAIN.get(c, c) for c in codes) + ". " + NO_DATA[lever])
        return
    for i in range(0, len(codes), 3):
        cols = st.columns(3)
        for col, c in zip(cols, codes[i:i + 3]):
            col.markdown(kpi_card(c, KPI_PLAIN.get(c, c)), unsafe_allow_html=True)
        st.write("")
    st.caption("Each card shows the share of each starting group who reached the milestone. “Not yet” means that "
               "group hasn't had enough time.")
    st.write("")


def strategy_list(ls, la):
    for s in ls.itertuples():
        sa = la[la["strategy"] == s.code].sort_values("cost", ascending=False)
        count = f"{len(sa)} {'activity' if len(sa) == 1 else 'activities'} · ${sa['cost'].sum():,.0f}" if len(sa) \
            else "no activities yet this year"
        with st.expander(f"**{s.code}** {s.element} — {count}", expanded=(bool(q.strip()) and not sa.empty)
                         or st.session_state.get("open") == s.code):
            st.caption(f"Led by: {s.lead or 'to be assigned'}")
            if sa.empty:
                st.markdown("No activities yet for this strategy this year.")
            for i, (_, r) in enumerate(sa.iterrows()):
                activity_row(r, f"u_{r['activity_key']}_{i}")


# ------------------------------------------------------------------ one tab per lever
other = a[~a["strategy"].isin(strat["code"])]
tab_names = [f"{lv}. {nm}" for lv, nm in C.LEVERS.items()]   # fixed labels keep the open tab after a save
if not other.empty:
    tab_names.append("Not tied to a strategy")
tabs = st.tabs(tab_names)
for tab, (lever, lever_name) in zip(tabs, C.LEVERS.items()):
    with tab:
        ls = strat[strat["lever"] == lever]
        la = a[a["strategy"].str[0] == lever]
        T.banner(f"{lever}. {lever_name}", LEVER_PLAIN[lever])
        n_s = la.loc[la["strategy"].isin(ls["code"]), "strategy"].nunique()
        done = int((la["activity_status"] == "Completed").sum())
        t1, t2, t3, t4 = st.columns(4)
        t1.markdown(T.tile("Strategies with activities", f"{n_s} of {len(ls)}",
                           f"{FY_LABEL.get(fy, fy)}{(' · ' + _scope) if _scope else ''}",
                           T.NAVY if n_s == len(ls) else T.RED if n_s == 0 else T.NAVY), unsafe_allow_html=True)
        t2.markdown(T.tile("Activities", f"{len(la):,}", "funded or added directly"), unsafe_allow_html=True)
        t3.markdown(T.tile("Funding", f"${la['cost'].sum():,.0f}", "where an amount is recorded"),
                    unsafe_allow_html=True)
        t4.markdown(T.tile("Completed", f"{done} of {len(la)}", "activities marked Completed",
                           T.GREEN if la.shape[0] and done == len(la) else T.NAVY), unsafe_allow_html=True)
        st.write("")
        if not q.strip():
            lever_kpis(lever)
        T.band("Strategies and activities", "Open a strategy to see its activities or update one.")
        strategy_list(ls, la)
if not other.empty:
    with tabs[-1]:
        T.banner("Not tied to a strategy", "Funded work that isn't assigned to an SFF strategy")
        for i, (_, r) in enumerate(other.iterrows()):
            activity_row(r, f"o_{r['activity_key']}_{i}")

st.divider()
st.caption("Activities are funded resource requests plus work added directly by areas. Status: ○ not started · "
           "◐ in progress · ● completed. Every update is saved with the person's name and the time.")
