"""Central configuration: file paths, labels, and colors.

Everything the dashboard needs to know about *where* data lives and *how* it is
labeled sits here, so moving to a server database later means editing this
module and sff/data.py only.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCE_DIR = DATA_DIR / "source"

DB_PATH = DATA_DIR / "sff.db"   # SQLite database built by tools/build_db.py

# Source files loaded by tools/build_db.py
MATRIX_XLSX = SOURCE_DIR / "sff_assessment_matrix.xlsx"
RANKING_FY27 = SOURCE_DIR / "fy27_all_areas_ranking.xlsx"   # institutional list with President/VP decisions
_RANKED = {"reader": "mapped", "path": RANKING_FY27, "sheet": "Resource Requests", "header_row": 6,
           "mapping": "tools.fy27_ranking_map:RANKING_FY27",
           "funded": "tools.fy27_ranking_map:FUNDED_FY27"}   # only funded rows count as approved
FY26_GRANTED = SOURCE_DIR / "fy26_approved_gf.xlsx"   # 2025-26 granted list (kept as the evidence source)
_FY26_GRANTED = {"granted_amounts": True, "approval_label": "On the 2025-26 granted list (Board-adopted budget, 9/2025)"}
REQUEST_SOURCES = [
    # one entry per area/year file; "reader" picks the parser in sff/etl.py
    # FY26 decisions: the 2025-26 granted list (data/source/fy26_approved_gf.xlsx), mapped in tools/fy26_approvals.py
    {"fy": "FY26", "area": "Academic Affairs", "reader": "fy26", "path": SOURCE_DIR / "fy26_aa_requests.xlsm",
     "mapping": "tools.fy26_strategy_map:FY26_MANUAL", **_FY26_GRANTED,
     "other_approvals": "tools.fy26_approvals:AA_FY26_ALL", "added_requests": "tools.fy26_approvals:ADDED_FY26"},
    {"fy": "FY26", "area": "Student Services", "reader": "fy26", "path": SOURCE_DIR / "fy26_ss_requests.xlsm",
     "mapping": "tools.ss_fy26_strategy_map:SS_FY26", **_FY26_GRANTED, "clear_unlisted": True,
     "other_approvals": "tools.fy26_approvals:SS_FY26_ALL"},
    # FY27 AA: requests + alignment from the AA file; decisions from the all-areas ranking (AA rows there lack names)
    {"fy": "FY27", "area": "Academic Affairs", "reader": "fy27", "path": SOURCE_DIR / "fy27_aa_requests_sff_alignment.xlsx",
     "ranking": {"path": RANKING_FY27, "crosswalk": "tools.fy27_ranking_map:AA_CROSSWALK", "area_filter": "Academic Affairs",
                 "funded": "tools.fy27_ranking_map:FUNDED_GF_FY27"},
     # approved outside the ranking (SWF, SEAP, AB1705, Vintage, ...), per the AA approved list (11/6/2026)
     "other_approvals": "tools.fy27_aa_other_approvals:AA_OTHER_APPROVALS",
     "added_requests": "tools.fy27_aa_other_approvals:AA_ADDED_REQUESTS",
     "deferred": "tools.fy27_aa_other_approvals:AA_DEFERRED"},
    # FY27 other areas: read straight from the all-areas ranking (final list, decisions included)
    {"fy": "FY27", "area": "Student Services", "area_filter": "Student Services", **_RANKED},
    {"fy": "FY27", "area": "Business Services", "area_filter": "Business Services", **_RANKED},
    {"fy": "FY27", "area": "Human Resources", "area_filter": "Human Resources", **_RANKED},
    {"fy": "FY27", "area": "President's Office", "area_filter": "President", **_RANKED},
]
AREAS = ["Academic Affairs", "Student Services", "Business Services", "Human Resources", "President's Office"]
AREA_COLORS = {"Academic Affairs": "#2a78d6", "Student Services": "#eb6834", "Business Services": "#1baf7a",
               "Human Resources": "#eda100", "President's Office": "#e87ba4"}
# IERPG student-level cohort report(s). Identifiers are dropped on read; only aggregates are stored.
COHORT_FILE_GLOB = "KPI - Student Level Report*.xls*"
MIN_CELL_SIZE = 10        # suppress any group smaller than this (privacy + stable rates)
KPI_RESULTS_CSV = SOURCE_DIR / "kpi_results.csv"         # real KPI results from IERPG (long format)
AWARD_COUNTS_CSV = SOURCE_DIR / "award_counts.csv"       # awards earned by cohort (aggregates, small counts rolled up)
KPI_SAMPLE_CSV = SOURCE_DIR / "kpi_results_SAMPLE.csv"   # synthetic placeholder until IERPG data exists

# Governance (Core Inquiry 3, topic 1): set once the college designates the accountable body
ACCOUNTABLE_BODY = None          # e.g., "Planning and Budget Committee" - None shows "not yet designated"
ACCOUNTABLE_BODY_CHARGE = None   # link or document name for the charge that assigns SFF monitoring
REVIEW_CYCLE = ("Fall: IERPG reports KPIs → Jan: lead areas report implementation → Spring: accountable body "
                "rates strategies and records decisions → PBC uses ratings in resource allocation → Board update")

GOAL_BASELINE = 0.29   # SFF p.6
GOAL_TARGET = 0.50     # SFF p.6
GOAL_YEAR = 2029
GOAL_BASELINE_YEAR = "2023-24"   # SFF adopted spring 2024 with 29% "today"
GOAL_TARGET_YEAR = "2028-29"

LEVERS = {
    "A": "Equitable Access",
    "B": "Completion",
    "C": "Career & Transfer Success",
    "D": "Institutional Health",
}

# Categorical slots 1-4 (validated palette; adjacent CVD dE >= 9.1). Aqua and
# yellow are below 3:1 contrast, so every chart pairs color with text labels.
LEVER_COLORS = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a", "D": "#eda100"}
# Fiscal years: categorical slots in fixed order (color follows the year).
YEAR_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]

STATUSES = ["Not yet assessed", "On track", "Needs adjustment", "Replace", "Retire"]
# Status colors are reserved for status only and always shown with a text label.
STATUS_COLORS = {
    "Not yet assessed": "#c3c2b7",
    "On track": "#0ca30c",
    "Needs adjustment": "#fab219",
    "Replace": "#ec835a",
    "Retire": "#8a8984",
}
STATUS_ICONS = {
    "Not yet assessed": "○",
    "On track": "●",
    "Needs adjustment": "▲",
    "Replace": "■",
    "Retire": "✕",
}

EQUITY_GROUPS = [
    "All students",
    "African American",
    "Asian",
    "Filipino",
    "Hispanic/Latino",
    "White",
    "Two or more races",
    "Pacific Islander",
    "American Indian/Alaska Native",
    "Unknown",
]
