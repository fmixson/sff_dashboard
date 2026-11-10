import io

import pandas as pd
import streamlit as st

from sff import config as C, data as D
from views import common

st.title("Add Activities")
st.caption("Record SFF activities that are happening **outside the resource allocation process** — grant- or "
           "categorically funded work, work covered by existing budgets, or no-cost practice changes. They are "
           "saved to the database, count as activities right away (no VP approval needed), and get status updates "
           "like any other activity. They are labeled **Added directly** everywhere they appear.")

m = common.current_matrix()
strat = D.strategies(m)
codes = list(strat["code"])
labels = {r.code: f"{r.code} – {r.element}" for r in strat.itertuples()}
valid = set(codes)
req = common.requests()
years = sorted(set(req["fiscal_year"]) | {"FY27", "FY28"})
divisions = sorted(req["division"].dropna().unique())

tab1, tab2, tab3 = st.tabs(["➕ Add one activity", "📤 Add many (Excel upload)", "✏️ Edit / remove added activities"])

# ------------------------------------------------------------------ add one
with tab1:
    with st.form("add_one", clear_on_submit=True):
        a1, a2, a3 = st.columns(3)
        fy = a1.selectbox("Fiscal year *", years, index=years.index("FY27") if "FY27" in years else 0)
        area = a2.selectbox("Area *", C.AREAS)
        division = a3.selectbox("Division", divisions, index=None, accept_new_options=True,
                                placeholder="Pick or type a new one")
        b1, b2 = st.columns(2)
        department = b1.text_input("Department / program")
        owner = b2.text_input("Owner / lead (person or office)")
        c1, c2 = st.columns(2)
        strategy = c1.selectbox("Primary SFF strategy *", codes, index=None, format_func=labels.get,
                                placeholder="Choose the one strategy this activity mainly advances")
        secondary = c2.selectbox("Secondary strategy (optional)", codes, index=None, format_func=labels.get)
        activity = st.text_area("Activity *", placeholder="What is being done, for whom — e.g., 'Offer corequisite "
                                "support sections for transfer-level English (funded by AB1705).'", height=90)
        expected = st.text_input("Expected result (recommended)",
                                 placeholder="What it should produce, countable — e.g., '12 sections; 70% of "
                                             "students pass transfer-level English'")
        d1, d2, d3 = st.columns(3)
        funding = d1.selectbox("Funding source", D.FUNDING_SOURCES)
        cost = d2.number_input("Estimated cost ($, optional)", min_value=0.0, step=500.0, value=None)
        who = d3.text_input("Entered by *")
        note = st.text_input("Note (optional)")
        if st.form_submit_button("Save activity", type="primary"):
            rec = {"fiscal_year": fy, "area": area, "division": division, "department": department,
                   "strategy": strategy, "secondary": secondary, "activity": activity,
                   "funding_source": funding, "cost": cost, "owner": owner, "note": note,
                   "expected_result": expected}
            errs = D.validate_manual(rec, valid) + ([] if who.strip() else ["'Entered by' is required"])
            if errs:
                st.error("Not saved: " + "; ".join(errs))
            else:
                D.add_manual_activities([rec], who)
                st.success(f"Saved: {activity[:80]} → {strategy}. It now appears on Strategy Detail and Activity Status.")
    st.caption("Fields marked \\* are required.")

# ------------------------------------------------------------------ bulk upload
TEMPLATE_COLS = ["fiscal_year", "area", "division", "department", "strategy", "secondary", "activity",
                 "expected_result", "funding_source", "cost", "owner", "note"]


def template_bytes() -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        pd.DataFrame(columns=TEMPLATE_COLS).to_excel(xw, sheet_name="Activities", index=False)
        pd.DataFrame([{"fiscal_year": "FY27", "area": "Academic Affairs", "division": "Liberal Arts",
                       "department": "English", "strategy": "B.4", "secondary": "",
                       "activity": "Offer corequisite support sections for transfer-level English.",
                       "expected_result": "12 corequisite sections; 70% of enrolled students pass transfer-level English",
                       "funding_source": "Grant / categorical", "cost": 25000, "owner": "English Dept Chair",
                       "note": "AB1705 funded"}]).to_excel(xw, sheet_name="Example (do not upload)", index=False)
        pd.DataFrame({"column": TEMPLATE_COLS, "required": ["yes", "yes", "", "", "yes", "", "yes", "recommended", "", "", "", ""],
                      "allowed values / format": [
                          "e.g., FY27", "; ".join(C.AREAS), "division name", "department or program",
                          "SFF strategy code, e.g., B.4 (see Strategies sheet)", "optional strategy code",
                          "short description of the activity",
                          "what the activity should produce, countable (e.g., '500 students contacted')",
                          "; ".join(D.FUNDING_SOURCES),
                          "number, no $ sign (optional)", "person or office", "optional"]}
                     ).to_excel(xw, sheet_name="Instructions", index=False)
        strat[["code", "element"]].rename(columns={"code": "strategy", "element": "description"}).to_excel(
            xw, sheet_name="Strategies", index=False)
        for ws in xw.sheets.values():
            for col in ws.columns:
                ws.column_dimensions[col[0].column_letter].width = 28
    return buf.getvalue()


with tab2:
    st.markdown("**Step 1.** Download the template, fill in the **Activities** sheet (one row per activity), "
                "and save it. The **Example** and **Strategies** sheets show the format and the strategy codes.")
    st.download_button("Download activity template (Excel)", template_bytes(), "SFF_activity_upload_template.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.markdown("**Step 2.** Upload the filled-in file. Rows are checked before anything is saved.")
    up = st.file_uploader("Upload Excel (.xlsx) or CSV", type=["xlsx", "csv"])
    if up is not None:
        try:
            df = pd.read_csv(up) if up.name.endswith(".csv") else pd.read_excel(up, sheet_name="Activities")
        except Exception as e:  # noqa: BLE001 - show any read problem to the user
            st.error(f"Could not read the file: {e}")
            st.stop()
        df.columns = [str(c).strip().lower() for c in df.columns]
        missing = [c for c in ["fiscal_year", "area", "strategy", "activity"] if c not in df.columns]
        if missing:
            st.error(f"Missing required column(s): {', '.join(missing)}. Use the template.")
            st.stop()
        df = df.reindex(columns=TEMPLATE_COLS).dropna(how="all")
        # accept "B.4" or "B.4 – description"; keep anything else as typed so the error message shows it
        for col in ("strategy", "secondary"):
            raw = df[col].where(df[col].notna(), "").astype(str).str.strip()
            code = raw.str.extract(r"^([A-D]\.\d)")[0]
            df[col] = code.fillna(raw).replace("", None)
        df["cost"] = pd.to_numeric(df["cost"], errors="coerce")
        df["problems"] = [", ".join(D.validate_manual(r, valid)) for r in df.to_dict("records")]
        ok = df[df["problems"] == ""]
        st.markdown(f"**{len(ok)} of {len(df)} rows are ready to import.**"
                    + (f" {len(df) - len(ok)} row(s) have problems (shown below) and will be skipped." if len(ok) < len(df) else ""))
        st.dataframe(df, hide_index=True, width="stretch",
                     column_config={"problems": st.column_config.TextColumn("Problems", width="medium")})
        who_b = st.text_input("Entered by (required to import)", key="bulk_who")
        if st.button(f"Import {len(ok)} activities", type="primary", disabled=ok.empty or not who_b):
            n = D.add_manual_activities(ok.drop(columns="problems").to_dict("records"), who_b)
            st.success(f"Imported {n} activities.")

# ------------------------------------------------------------------ edit / remove
with tab3:
    man = D.load_manual_activities()
    if man.empty:
        st.info("No activities have been added directly yet.")
    else:
        st.markdown("Edit any ✏️ column, or tick **Remove** to take an activity off the list (it is hidden, not "
                    "deleted, so the record is kept). Enter your name, then **Save**.")
        e1, e2 = st.columns(2)
        fy_f = e1.multiselect("Fiscal year", sorted(man["fiscal_year"].unique()), key="ed_fy")
        area_f = e2.multiselect("Area", sorted(man["area"].unique()), key="ed_area")
        view = man
        if fy_f:
            view = view[view["fiscal_year"].isin(fy_f)]
        if area_f:
            view = view[view["area"].isin(area_f)]
        cols = ["id", "removed", "strategy", "secondary", "activity", "funding_source", "cost", "owner", "note",
                "fiscal_year", "area", "division", "department", "entered_by", "updated"]
        edit = view[cols].copy()
        edit["removed"] = edit["removed"].astype(bool)
        edited = st.data_editor(
            edit, hide_index=True, width="stretch", key="man_editor",
            disabled=["id", "fiscal_year", "area", "division", "department", "entered_by", "updated"],
            column_config={
                "id": None,
                "removed": st.column_config.CheckboxColumn("✏️ Remove"),
                "strategy": st.column_config.SelectboxColumn("✏️ Strategy", options=codes, required=True),
                "secondary": st.column_config.SelectboxColumn("✏️ Secondary", options=codes),
                "activity": st.column_config.TextColumn("✏️ Activity", width="large", required=True),
                "funding_source": st.column_config.SelectboxColumn("✏️ Funding", options=D.FUNDING_SOURCES),
                "cost": st.column_config.NumberColumn("✏️ Cost", format="$%,.0f", min_value=0),
                "owner": st.column_config.TextColumn("✏️ Owner / lead"),
                "note": st.column_config.TextColumn("✏️ Note"),
                "fiscal_year": "FY", "area": "Area", "division": "Division", "department": "Dept",
                "entered_by": "Last edited by", "updated": "Last edited",
            },
        )
        ed_cols = ["removed", "strategy", "secondary", "activity", "funding_source", "cost", "owner", "note"]
        before = edit.set_index("id")[ed_cols]
        after = edited.set_index("id")[ed_cols]
        diff = ~((before == after) | (before.isna() & after.isna())).all(axis=1)
        chg = after[diff].reset_index()
        who_e = st.text_input("Your name (required to save)", key="ed_who")
        if st.button(f"Save {len(chg)} change(s)", type="primary", disabled=chg.empty or not who_e):
            D.update_manual_activities(chg, who_e)
            st.success(f"Saved {len(chg)} change(s).")
            st.rerun()
