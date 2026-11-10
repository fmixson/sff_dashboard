"""Compute SFF student KPIs from IERPG's student-level cohort report
("KPI - Student Level Report - <cohorts> - <YYYYMMDD>.xlsx", one row per first-time student).

PRIVACY: direct identifiers (EMPLID, names, phone, email, city, ZIP, high school) are dropped the
moment the file is read. Only AGGREGATES leave this module - counts and rates by cohort x group,
with groups smaller than config.MIN_CELL_SIZE suppressed. No student rows are written to sff.db.
Keep the student file itself only on a secured college computer (data/source/ is git-ignored).
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

import pandas as pd

from . import config as C

IDENTIFIERS = ["EMPLID", "FIRST_NAME", "LAST_NAME", "PHONE", "CER_CALW_EMAIL", "CITY",
               "Service_Area_ZIP", "CER_AD_HIGH_NAME"]

RACE_MAP = {
    "Black or African American": "African American", "Hispanic/Latino": "Hispanic/Latino", "Asian": "Asian",
    "Filipino": "Filipino", "White": "White", "Two or More Races": "Two or more races",
    "Native Hawaiian or Other Pacific Islander": "Pacific Islander",
    "American Indian or Alaska Native": "American Indian/Alaska Native",
    "Race/Ethnicity Unknown": "Unknown",
}

# Disaggregation dimensions: (label, source column, value cleaner). Race/ethnicity is the SFF default.
# EOPS and Umoja are omitted: in the 10/30/2026 file EOPS is "Not EOPS" for everyone and the Umoja
# column contains Puente values - restore once IERPG corrects them.
DIMENSIONS = {
    "Race/ethnicity": ("Ethnicity", lambda v: RACE_MAP.get(v, "Unknown") if isinstance(v, str) else "Unknown"),
    "Gender": ("Gender", lambda v: v if isinstance(v, str) else "Unknown"),
    "Pell (first year)": ("pell_recipient", lambda v: "Pell recipient" if str(v).startswith("Pell") else "Not Pell"),
    "Cerritos Complete": ("CCPP", lambda v: "Cerritos Complete" if str(v).startswith("Cerritos") else "Not Cerritos Complete"),
    "Puente": ("Puente", lambda v: "Puente" if str(v).startswith("Puente") else "Not Puente"),
    "Age at entry": ("Age", lambda v: v if isinstance(v, str) else "Unknown"),
    "High school GPA": ("HS_GPA_BUCKET", lambda v: v if isinstance(v, str) else "Unknown"),
}


def as_of_from_filename(path) -> date | None:
    m = re.search(r"(20\d{2})(\d{2})(\d{2})", Path(path).name)
    return date(int(m[1]), int(m[2]), int(m[3])) if m else None


def read_student_report(path) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=0)
    df = df.drop(columns=[c for c in IDENTIFIERS if c in df.columns])   # identifiers never kept
    df = df.dropna(subset=["FTFS_Cohort_Academic_Year"])
    df["fall_year"] = df["FTFS_Cohort_Academic_Year"].astype(int) - 1     # AY 2025 -> Fall 2024 cohort
    return df


# ---- awards (degrees and certificates). IERPG's Awards_all lists award codes, e.g. "BA 2.0-AST,CSUGE-CT".
GE_PATTERNS = {"CSUGE", "IGETC", "CALGETC"}          # GE pattern certifications, not certificates of achievement
AWARD_TYPES = {"AA": "Associate degree (AA/AS)", "AS": "Associate degree (AA/AS)",
               "AAT": "Associate degree for transfer (AA-T/AS-T)", "AST": "Associate degree for transfer (AA-T/AS-T)"}
# SFF completer (F. Mixson, 11/6/2026; GE certifications added 11/10/2026): earned a degree, OR earned a certificate,
# OR earned a GE pattern certification (CSU GE / IGETC / Cal-GETC), OR completed 60+ degree-applicable units.
# Categories are mutually exclusive, counted in that order. Matches IERPG's "Graduated" column plus the 60-unit completers.
COMPLETION_CATEGORIES = ["Degree", "Certificate (no degree)", "GE certification only", "60+ units (no award)"]


def _award_tokens(v) -> list[str]:
    return [t.strip() for t in str(v).split(",") if t.strip()] if isinstance(v, str) else []


def award_type(token: str) -> str:
    program, _, suffix = token.rpartition("-")
    if suffix in AWARD_TYPES:
        return AWARD_TYPES[suffix]
    if suffix == "CT":
        return "GE certification (CSU GE / IGETC / Cal-GETC)" if program in GE_PATTERNS else "Certificate"
    return "Other award"


def completion_category(v) -> str | None:
    types = {award_type(t) for t in _award_tokens(v)}
    if not types:
        return None
    if types & set(AWARD_TYPES.values()):
        return "Degree"
    if "Certificate" in types:
        return "Certificate (no degree)"
    return "GE certification only"


def award_counts(df: pd.DataFrame, min_cell: int | None = None) -> pd.DataFrame:
    """Aggregates only: per entering cohort, students earning each award type and each award (program).
    Awards earned by fewer than min_cell students are rolled into 'Other awards (each under N)'."""
    min_cell = C.MIN_CELL_SIZE if min_cell is None else min_cell
    rows = []
    for fy, v in zip(df["fall_year"], df.get("Awards_all", pd.Series(index=df.index, dtype=object))):
        for t in dict.fromkeys(_award_tokens(v)):
            rows.append((_label(int(fy)), award_type(t), t))
    cols = ["year", "award_type", "award", "students"]
    if not rows:
        return pd.DataFrame(columns=cols)
    a = pd.DataFrame(rows, columns=["year", "award_type", "award"])
    by_award = a.groupby(["year", "award_type", "award"]).size().rename("students").reset_index()
    small = by_award["students"] < min_cell
    by_award.loc[small, "award"] = f"Other awards (each under {min_cell} students)"
    out = by_award.groupby(["year", "award_type", "award"], as_index=False)["students"].sum()[cols]
    return out[out["students"] >= min_cell].reset_index(drop=True)   # a combined line under min_cell is left out too


def _enrolled_now(df: pd.DataFrame) -> pd.Series:
    """Attempted degree-applicable units in the academic year now under way. IERPG's file has no current-term
    enrollment flag, so this compares cumulative attempted units at the end of the current year with the end of
    the year before (the current year includes the summer before the fall). df["_ay_now"] = 1-5."""
    k = df.get("_ay_now", pd.Series(1, index=df.index)).clip(1, 5).astype(int)
    out = pd.Series(False, index=df.index)
    for y in range(1, 6):
        m = k == y
        cur = _num(df.loc[m, f"AttemptedUnits_DA_end_of_ay{y}"]) if f"AttemptedUnits_DA_end_of_ay{y}" in df else 0
        prev = _num(df.loc[m, f"AttemptedUnits_DA_end_of_ay{y - 1}"]) if y > 1 and f"AttemptedUnits_DA_end_of_ay{y - 1}" in df else 0
        out[m] = (cur - prev) > 0
    return out


def _num(s):
    return pd.to_numeric(s, errors="coerce").fillna(0)


def _starts(s, prefix):
    return s.astype(str).str.startswith(prefix)


def _passed_ever(df, col):
    """IERPG's *_Term_firstpassed holds the term first passed ("0000" = AP/prior credit), or "Did not pass" /
    "N/A because no attempt"."""
    if col not in df:
        return pd.Series(False, index=df.index)
    v = df[col]
    return v.notna() & ~v.astype(str).isin(["Did not pass", "N/A because no attempt", "", "nan"])


def kpi_rules(df: pd.DataFrame) -> dict[str, tuple[float, pd.Series, pd.Series]]:
    """code -> (years after cohort's fall start before final, numerator mask, denominator mask).
    Definitions follow IERPG's report fields; see README 'KPI definitions'."""
    allrows = pd.Series(True, index=df.index)
    cte = df["CompletedUnits_CTE_ay1_cteall"].notna()
    awards = df["Awards_all"] if "Awards_all" in df else pd.Series(None, index=df.index, dtype=object)
    cat = awards.map(completion_category)
    completed_award = cat.isin(["Degree", "Certificate (no degree)", "GE certification only"])
    u60 = _starts(df["CompletedUnits_DA60_current"], "Passed") if "CompletedUnits_DA60_current" in df \
        else _num(df.get("CompletedUnits_DA_end_of_ay5", 0)) >= 60
    completer = completed_award | u60
    return {
        "A-K1": (1.0, _starts(df["EdPlan_ay1"], "Has CSEP"), allrows),
        "A-K2": (0.2, _num(df["AttemptedUnits_DA_in_f1"]) >= 15, allrows),
        "A-K3": (1.0, _num(df["AttemptedUnits_DA_end_of_ay1"]) >= 30, allrows),
        "B-K1": (1.0, df["Passed_of_5_da_courses"].eq("Passed 5/5 courses"), allrows),
        "B-K2": (1.0, _num(df["CompletedUnits_DA_end_of_ay1"]) >= 15, allrows),
        "B-K3": (1.0, _num(df["CompletedUnits_CTE_ay1_cteall"]) >= 1, cte),     # flag among CTE students
        "B-K4": (2.0, _num(df["CompletedUnits_DA_end_of_ay2"]) >= 30, allrows),
        "B-K5": (3.0, _num(df["CompletedUnits_DA_end_of_ay3"]) >= 45, allrows),
        "B-K6": (1.0, _starts(df["pass_both_ay1"], "Passed"), allrows),
        # the two halves of B-K6, shown separately on SFF at a Glance (not SFF matrix KPIs)
        "ENG-Y1": (1.0, _starts(df["pass_engl_ay1"], "Passed"), allrows),
        "MATH-Y1": (1.0, _starts(df["pass_math_ay1"], "Passed"), allrows),
        # passed college-level English / math at any point so far (as of the file date; every cohort, no waiting)
        "ENG-TD": (0.0, _passed_ever(df, "English_Term_firstpassed"), allrows),
        "MATH-TD": (0.0, _passed_ever(df, "Math_Term_firstpassed"), allrows),
        "EM-TD": (0.0, _passed_ever(df, "English_Term_firstpassed") & _passed_ever(df, "Math_Term_firstpassed"), allrows),
        "B-K7": (0.6, _starts(df["Persisted_f1_sp1"], "Persisted"), allrows),
        "B-K8": (1.1, _starts(df["Retained_f1_f2"], "Retained"), allrows),
        "B-K9": (1.6, _starts(df["Retained_f1_sp2"], "Retained"), allrows),
        "B-K10": (2.0, _starts(df["Graduated"], "Graduated") & (_num(df["time_grad"]).between(0.5, 2)), allrows),
        "GOAL": (5.0, completer & _num(df["time_grad_or_c60_daunits"]).between(0.5, 5), allrows),
        # completed so far, as of the file date (every cohort, no waiting period); the goal cohort's running total
        # completers so far: degree OR certificate OR GE certification OR 60+ DA units (see COMPLETION_CATEGORIES)
        "CMP-TD": (0.0, completer, allrows),
        # how they completed (mutually exclusive; they add up to CMP-TD) + ADT earners
        "CMP-DEG": (0.0, cat.eq("Degree"), allrows),
        "CMP-CERT": (0.0, cat.eq("Certificate (no degree)"), allrows),
        "CMP-U60": (0.0, u60 & ~completed_award, allrows),
        "CMP-GE": (0.0, cat.eq("GE certification only"), allrows),
        "CMP-ADT": (0.0, awards.map(lambda v: any(award_type(t).endswith("(AA-T/AS-T)") for t in _award_tokens(v))), allrows),
        # taking classes in the academic year now under way (summer/fall onward), as of the file date
        "ENR-NOW": (0.0, _enrolled_now(df), allrows),
        # completed 45+ degree-applicable units so far
        "U45": (0.0, _starts(df["CompletedUnits_DA45_current"], "Passed") if "CompletedUnits_DA45_current" in df
                else _num(df.get("CompletedUnits_DA_end_of_ay5", 0)) >= 45, allrows),
    }


def _label(fall_year: int) -> str:
    return f"{fall_year}-{str(fall_year + 1)[2:]}"


def compute_kpis(df: pd.DataFrame, as_of: date, min_cell: int | None = None) -> pd.DataFrame:
    """Long format: kpi_code, year (entering cohort; GOAL = year the 5-yr window closes), dimension,
    group, value, numerator, denominator. A cohort is reported for a KPI only after its window has passed."""
    min_cell = C.MIN_CELL_SIZE if min_cell is None else min_cell
    as_of = pd.Timestamp(as_of)
    start = pd.to_datetime(df["fall_year"].astype(str) + "-08-15")
    out = []
    df = df.assign(_ay_now=((as_of - start).dt.days // 365.25 + 1).clip(1, 5))   # academic year under way now
    for code, (window, hit, base) in kpi_rules(df).items():
        mature = start + pd.to_timedelta(window * 365.25, unit="D") <= as_of
        d = df[mature & base].assign(hit=hit[mature & base])
        if d.empty:
            continue
        d = d.assign(year=(d["fall_year"] + (4 if code == "GOAL" else 0)).map(_label))
        tot = d.groupby("year")["hit"].agg(numerator="sum", denominator="size").reset_index()
        out.append(tot.assign(kpi_code=code, dimension="All", group="All students"))
        for dim, (col, clean) in DIMENSIONS.items():
            g = d.assign(group=d[col].map(clean)).groupby(["year", "group"])["hit"] \
                 .agg(numerator="sum", denominator="size").reset_index()
            out.append(g.assign(kpi_code=code, dimension=dim))
    cols = ["kpi_code", "year", "dimension", "group", "value", "numerator", "denominator"]
    if not out:
        return pd.DataFrame(columns=cols)
    res = pd.concat(out, ignore_index=True)
    res = res[res["denominator"] >= min_cell]            # small-cell suppression
    res["value"] = res["numerator"] / res["denominator"]
    return res[cols].reset_index(drop=True)


def find_student_reports() -> list[Path]:
    """IERPG student-level files in data/source. Tolerant of how the file was saved: spaces, underscores or
    dashes ("KPI_-_Student_Level_Report..."), any letter case, .xlsx or .xls. Excel lock files (~$...) are skipped."""
    key = lambda name: re.sub(r"[^a-z0-9]", "", name.lower())
    return sorted(p for p in C.SOURCE_DIR.iterdir()
                  if p.is_file() and p.suffix.lower() in (".xlsx", ".xls", ".xlsm") and not p.name.startswith("~$")
                  and "kpistudentlevelreport" in key(p.stem))
