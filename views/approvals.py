import streamlit as st

from sff import data as D
from views import common

st.title("VP Approvals")
st.caption("Record the VP/area decision on each resource request. Only **Approved** requests count as SFF "
           "activities. A decision entered here overrides the source workbook's Area Approval column; every "
           "entry is logged with the approver and time.")

with st.expander("**Take a request off the approved list**", expanded=True):
    st.markdown(
        "1. Set **Show** to *Approved* (or type part of the request name in **Search**).  \n"
        "2. In **✏️ VP decision**, pick:  \n"
        "   - **Not approved** — it was requested but not funded; it stays in the request list.  \n"
        f"   - **{D.REMOVED}** — it should not be in the dashboard at all (a duplicate or an item added by "
        "mistake); it disappears from every page, total and report.  \n"
        "3. Add a short note (why), type your name, and click **Save**.  \n"
        f"Nothing is deleted permanently: set **Show** to *{D.REMOVED}* to see removed items and change them back.")

req = common.requests(include_removed=True)

f1, f2, f3, f4, f5 = st.columns([1, 1.3, 1.3, 1.2, 1.5])
fy = f1.selectbox("Fiscal year", sorted(req["fiscal_year"].unique(), reverse=True), key="ap_fy")
r = req[req["fiscal_year"] == fy]
area = f2.selectbox("Area", ["All"] + sorted(r["area"].unique()), key="ap_area")
if area != "All":
    r = r[r["area"] == area]
div = f3.selectbox("Division", ["All"] + sorted(r["division"].dropna().unique()), key="ap_div")
if div != "All":
    r = r[r["division"] == div]
show = f4.selectbox("Show", ["Awaiting decision", "All", "Approved", "Not approved", "Denied", "Deferred", D.REMOVED],
                    key="ap_show")
if show == "Awaiting decision":
    r = r[r["vp_decision"].isna()]
elif show == "All":
    r = r[r["vp_decision"].ne(D.REMOVED)]
else:
    r = r[r["vp_decision"] == show]
q = f5.text_input("Search request or activity", key="ap_q", placeholder="e.g., SPSS")
if q:
    hit = r["request"].fillna("").str.contains(q, case=False, regex=False) | \
          r["activity"].fillna("").str.contains(q, case=False, regex=False)
    r = r[hit]

dec = req[(req["fiscal_year"] == fy) & ((req["area"] == area) if area != "All" else True)]
dec = dec[dec["vp_decision"].ne(D.REMOVED)]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Requests", len(dec))
c2.metric("Approved", int(dec["approved"].sum()), f"${dec.loc[dec['approved'], 'cost'].sum():,.0f}", delta_color="off", delta_arrow="off")
c3.metric("Not approved / denied / deferred", int(dec["vp_decision"].isin(["Not approved", "Denied", "Deferred"]).sum()))
c4.metric("Awaiting decision", int(dec["vp_decision"].isna().sum()))

if r.empty:
    st.info("No requests match these filters.")
    st.stop()

st.markdown("**How to record a decision:** 1) type your name · 2) click a cell in **✏️ VP decision** and choose "
            "one (use **Set all shown to…** for many at once) · 3) click **Save**.")
who = st.text_input("Approver name (required to save)", key="ap_who")

edit = r[["activity_key", "vp_decision", "strategy", "area", "division", "department", "request", "activity", "cost",
          "cost_raw", "dean_approval", "area_rank", "approval_source", "note"]].rename(columns={"note": "file_note"}).copy()
edit["vp_decision"] = edit["vp_decision"].fillna("")
edit["note"] = ""

b1, b2 = st.columns([1, 3])
bulk = b1.selectbox("Set all shown to…", ["—", "Approved", "Not approved", "Denied", "Deferred"], key="ap_bulk")
if bulk != "—":
    edit["vp_decision"] = bulk
    b2.caption(f"All {len(edit)} rows shown are pre-set to **{bulk}**. Review, then Save (or change the "
               "selector back to — to cancel).")

edited = st.data_editor(
    edit, hide_index=True, width="stretch", key=f"ap_editor_{fy}_{area}_{div}_{show}_{bulk}_{q}",
    disabled=[c for c in edit.columns if c not in ("vp_decision", "note")],
    column_config={
        "activity_key": None,
        "vp_decision": st.column_config.SelectboxColumn("✏️ VP decision", options=D.VP_DECISIONS, width="medium"),
        "note": st.column_config.TextColumn("✏️ Note", width="small"),
        "strategy": "Strategy", "area": "Area", "division": "Division", "department": "Dept",
        "file_note": st.column_config.TextColumn("How it was recorded", width="medium"),
        "request": st.column_config.TextColumn("Resource request", width="medium"),
        "activity": st.column_config.TextColumn("Activity", width="large"),
        "cost": st.column_config.NumberColumn("Cost", format="$%,.0f"), "cost_raw": "Cost (as entered)",
        "dean_approval": "Dean/manager approval", "area_rank": "Area rank", "approval_source": "Recorded in",
    },
)
orig = r.set_index("activity_key")["vp_decision"].fillna("")
chg = edited[(edited["vp_decision"] != edited["activity_key"].map(orig)) | (edited["note"] != "")]
if st.button(f"Save {len(chg)} decision(s)", type="primary", disabled=chg.empty or not who):
    D.append_approvals(chg.rename(columns={"vp_decision": "decision"})[["activity_key", "decision", "note"]], who)
    st.success(f"Saved {len(chg)} decision(s).")
    st.rerun()
if not chg.empty and not who:
    st.caption("⬆️ Enter the approver name to enable Save.")

with st.expander("Approval history (dashboard entries)"):
    h = D.load_approvals()
    if h.empty:
        st.info("No approvals recorded in the dashboard yet.")
    else:
        h = h.merge(req[["activity_key", "fiscal_year", "area", "request"]], on="activity_key", how="left")
        st.dataframe(h.sort_values("timestamp", ascending=False), hide_index=True, width="stretch")
