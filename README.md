# SFF Dashboard (prototype)

Streamlit prototype for monitoring the Cerritos College **Students First Framework (SFF)**,
built for the SFF accountable body (Core Inquiry 3).

## Run it

```bash
pip install -r requirements.txt
python -m tools.build_db        # builds data/sff.db from data/source/
streamlit run app.py
```

## Pages

| Page | What it shows | Core Inquiry 3 topic |
|---|---|---|
| Overview | Goal progress, strategy status by lever, strategies with no funded activities, requests per year | — |
| Goal by Student Group | 5-year completion by race/ethnicity, path from 29% (2023-24) to 50% (2028-29), pace needed vs. observed | 5 Interim progress |
| Lever Scorecard | Per lever: KPIs improving, strategies on track, activities completed; KPI trend/target/equity gap table; set KPI targets | 2, 5 |
| Strategy Detail | The chain for one strategy: linked KPI trends → measure results (record "is it happening / is it working") → activities with status (update) | 2 Strategies vs. indicators |
| KPIs | Any KPI by student group with target and equity gaps | 4 (ACE equity review) |
| Resource Alignment | $ by strategy, by area, year over year; funding vs. status; how strategies were assigned | 3 Data → decisions (PBC) |
| VP Approvals | VP/area decision per request (Approved, Not approved, Denied, Deferred, Removed (entered in error)); overrides the source file; search; bulk-set | 3 |
| Add Activities | Record activities outside resource allocation (grant/categorical, existing budget, no cost): form, Excel template upload, edit/remove | 2 |
| Activity Status | Deans/managers record each activity's expected result, then status, result vs. expected, and outcome/evidence | 2 |
| Review & Decisions | Accountable body rates each strategy with evidence columns beside it; append-only decision log | 3 Data → decisions |
| Core Inquiry 3 Evidence | Live answer to each of the team's five interview topics, requested-evidence status, Strategy Progress Report download, open items | All |

## Structure

```
app.py                  entry point / navigation
views/                  one file per page (Streamlit UI only)
sff/config.py           paths, labels, colors (edit here first)
sff/etl.py              readers for each source-file layout -> tidy DataFrames
sff/data.py             all database reads/writes (pandas + sqlite3; no Streamlit)
sff/charts.py           Plotly figure builders (reusable outside Streamlit)
sff/report.py           Strategy Progress Report (Excel) for accreditation evidence
tools/build_db.py       loads data/source/* into data/sff.db (never drops `reviews`)
tools/fy26_strategy_map.py  proposed primary strategy for FY26 AA multi-strategy requests
tools/ss_fy26_strategy_map.py  same, for FY26 Student Services
tools/fy27_aa_other_approvals.py  AA FY27 requests approved outside the ranking (other funding)
tools/fy27_ranking_map.py   FY27 all-areas ranking: strategy + activity per request (SS, BS, HR, President's Office),
                            AA crosswalk (ranking row -> AA file row), and activity-key migrations
tools/make_sample_kpis.py   generates SYNTHETIC KPI data (placeholder only)
data/source/            source workbooks and CSVs
data/sff.db             SQLite database (tables: elements, requests, kpi_results, reviews, meta)
```

## Database tables

Rebuilt from `data/source/` by `python -m tools.build_db`:
- **elements** – the SFF Assessment Matrix (goal, levers, KPIs, strategies, functional plans).
- **requests** – one row per area resource request: `fiscal_year, area, division, department, request, cost, cost_raw,
  resource_type, strategy, secondary, activity, strategy_source, dean_approval, area_approval, area_rank, note, source_file, source_row`.
- **strategy_kpis** – strategy ↔ KPI links (parsed from the matrix "Linked KPI(s)" column).
- **kpi_results** – long format: `kpi_code, year, group, value, is_sample`. `kpi_code = GOAL` is five-year completion.

Written from the app; created if missing and **never dropped** (append-only, latest entry wins):
- **reviews** – strategy status + decision: `timestamp, code, status, decision, reviewer, meeting`.
- **measure_results** – `timestamp, code, period, measure_type (Implementation|Effectiveness), result, rating, entered_by`.
- **activity_status** – `timestamp, activity_key (source_file#source_row), status, outcome, expected_result,
  result_rating, entered_by`. Columns added later are created automatically on older databases.
- **request_approvals** – VP/area decisions entered in the app: `timestamp, activity_key, decision, approver, note`.
  **Activities = approved requests only** (latest dashboard decision, else the file's Area Approval column).
  `Removed (entered in error)` hides a request from every page, total and report (reversible on VP Approvals).
- **manual_activities** – activities added directly (not resource requests). They count as activities without VP
  approval and are labeled "Added directly"; 'removed' hides a row without deleting it.
- **kpi_targets** – `timestamp, kpi_code, target, target_year, set_by`.

## How activities are assessed

Each activity (approved request or activity added directly) has four fields on **Activity Status** and **Strategy Detail**:

1. **Expected result** – set at the start of the year: what the activity should produce, in countable terms
   ("500 flagged students contacted; 60% re-enroll next term"). Activities added directly can include it when added.
2. **Status** – Not started, In progress, Completed, Not funded, Cancelled.
3. **Result vs. expected** – at mid-year/year-end: Met, Partially met, Not met, Too early to tell. A rating can't be
   saved without an expected result.
4. **Outcome / evidence** – what actually happened, with numbers.

Roll-up per strategy (`data.activity_completion`): activities, % completed, how many have an expected result, and
% met (Met ÷ rated). These appear on the Lever Scorecard, Review & Decisions, the Core Inquiry 3 Evidence page, and
the Strategy Progress Report, beside the strategy's implementation and effectiveness ratings.

## Governance settings (sff/config.py)

`ACCOUNTABLE_BODY`, `ACCOUNTABLE_BODY_CHARGE`, and `REVIEW_CYCLE` drive the Core Inquiry 3 Evidence page and the report
cover. Set them once the college designates the body that owns SFF monitoring.

## Student-level KPI data (IERPG cohort report)

Put IERPG's file in `data/source/`. Its name must contain `KPI - Student Level Report`; spaces, underscores or
dashes and any letter case all work (for example `KPI_-_Student_Level_Report_-_F24-F26_-_20261030.xlsx`). Then run
`python -m tools.build_db`; its output says which KPI source it used. Each run also saves the de-identified
aggregates to `data/source/kpi_results.csv` (counts and rates only, groups under 10 suppressed), which is used
whenever the student file is not present.

- **Privacy:** `sff/cohort.py` drops EMPLID, names, phone, email, city, ZIP and high school as soon as the file
  is read. Only counts and rates by cohort and group are stored in `sff.db`, and groups under `MIN_CELL_SIZE` (10)
  are suppressed. Keep the student file only on a secured college computer. It is git-ignored and should not be
  emailed or shared.
- **As-of date** comes from the date in the file name (YYYYMMDD). A cohort is reported for a KPI only after enough
  time has passed. For example, fall-to-spring persistence needs about 0.6 years and the 2-year completion rate
  needs 2 years.
- **Breakdowns:** race/ethnicity (default), gender, Pell, Cerritos Complete, Puente, age at entry, high school GPA.
  EOPS and Umoja are left out because the 10/30/2026 file has EOPS = "Not EOPS" for everyone and the Umoja
  column holds Puente values.
- **KPI definitions used** (confirm with IERPG). The denominator is all students in the entering fall cohort
  unless noted.
  - A-K1: has a CSEP/DPP by end of year 1. A blank counts as no.
  - A-K2: 15+ degree-applicable units attempted in the first fall.
  - A-K3: 30+ attempted by end of year 1.
  - B-K1: passed 5 of the first 5 courses. Students who haven't attempted 5 count as not passing.
  - B-K2: 15+ degree-applicable units completed by end of year 1.
  - B-K3: CTE year-1 completion flag. The denominator is CTE students only.
  - B-K4: 30+ units completed by end of year 2.
  - B-K5: 45+ units completed by end of year 3.
  - B-K6: passed transfer-level math and English in year 1.
  - B-K7: persisted from first fall to first spring.
  - B-K8: retained to the second fall.
  - B-K9: retained to the second spring.
  - B-K10: graduated within 2 years (`time_grad` = 2; IERPG codes it in whole years, and 3 = graduated in year 3).
  - Completer (SFF definition, 11/6/2026): earned a degree, OR earned a certificate, OR completed 60+ degree-applicable
    units (`CompletedUnits_DA60_current`). A CSU GE / IGETC / Cal-GETC certification alone does not count.
  - CMP-TD: completers so far, as of the file date. For the Fall 2024 goal cohort this is the running total toward the
    50% goal (780 of 3,634, 21.5%, as of 10/30/2026). CMP-DEG, CMP-CERT and CMP-U60 split it by how students completed
    (degree; certificate, no degree; 60+ units, no award). CMP-GE counts GE-certification-only students under 60 units
    (not completers). CMP-ADT counts ADT earners.
  - GOAL: completers within 5 years (`time_grad_or_c60_daunits` ≤ 5). This is not available until the Fall 2024 cohort reaches 2029. Older
    cohorts' 5-year rates can be supplied as aggregated rows in `kpi_results.csv`.

## Strategy Progress Report

Download from the Core Inquiry 3 Evidence page, or run
`python -c "from sff.report import build_report; open('report.xlsx','wb').write(build_report())"`.
Sheets: Cover, Goal Pace, Lever Scorecard, Strategy Progress, Activities, Decision Log, Measure Results.

## Adding data

- **Another year or area:** put the workbook in `data/source/` and add an entry to `REQUEST_SOURCES` in
  `sff/config.py`. Files in the FY27 area template can use reader `"mapped"` with a mapping file like
  `tools/ss_fy27_strategy_map.py` (row -> primary, secondary, activity, note). Rerun `python -m tools.build_db`.
- **Real KPI results:** save IERPG data as `data/source/kpi_results.csv` with columns
  `kpi_code, year, group, value` (value as a proportion, e.g. 0.42; groups as in `EQUITY_GROUPS`). Include
  `kpi_code = GOAL` rows for five-year completion by group. It replaces the sample automatically.
- **Moving to a server database:** change `_connect()` in `sff/data.py` (e.g., SQLAlchemy engine).

## Data currently loaded

| Area | FY | Requests | VP/President approved | Source |
|---|---|---|---|---|
| Academic Affairs | FY26 | 157 | 15 granted ($497,833) | FY26 AA file + 2025-26 granted list (3 granted items added) |
| Student Services | FY26 | 42 | 13 granted ($1,083,924); 28 area-approved only; 1 denied | FY26 SS file + 2025-26 granted list |
| Business Services / President's Office | FY26 | 1 / 2 | all granted ($135,000 / $99,100) | added from the 2025-26 granted list |
| Academic Affairs | FY27 | 135 | 56 (3 general fund + 53 other funding); 47 ranked not funded; 32 deferred | AA file with 11/2026 alignment; decisions from the all-areas ranking and the AA approved list |
| Student Services | FY27 | 44 | 6 (4 general fund + 2 categorical) | 2025-2026 FY27 Area Resource Requests ALL AREAS_Ranking.xlsx |
| Business Services | FY27 | 24 | 5 (general fund) | same |
| Human Resources | FY27 | 9 | 5 (general fund) | same |
| President's Office | FY27 | 7 | 2 (general fund; 5 denied) | same |

### FY26 granted list

`data/source/fy26_approved_gf.xlsx` is "Resource Allocation – Granted, Annual College Plan 2025-26" ($1,815,857, 31
items, one-time, unrestricted general fund; Felipe Lopez to EC 8/21/2025, campus memo 9/4/2025). `tools/fy26_approvals.py`
maps each item to its FY26 area-file row; the granted amount replaces the requested cost (the request is kept in the
note). Six items not in the loaded FY26 files are added (`ADDED_FY26`). Student Services rows the area file marks
Approved but that are not on the list lose that approval (`clear_unlisted`) and are noted for confirmation; they may
have been funded from categorical sources.

### FY27 all-areas ranking

**"Approved" in the ranking file means area-approved and ranked, not funded.** Only the general-fund block Felipe Lopez
highlighted on 8/17/2026 was funded: sheet rows 8–26, $1,081,671 (`FUNDED_GF_FY27` in `tools/fy27_ranking_map.py`;
Conrad Selorio's 9/16/2026 notice to Academic Affairs lists the same three AA items). Ranked items below that line are
"Not approved" with a note; rows ranked "Cat Fun" (categorical funding) stay approved. Academic Affairs requests funded
from other sources (SWF, SEAP, AB1705, Vintage, AB19, Lottery, Instructional Equipment, grants) come from
`tools/fy27_aa_other_approvals.py`.

`data/source/fy27_all_areas_ranking.xlsx` is the institutional list with the President/VP decision for every area,
so it is the FY27 source for decisions. SS, BS, HR and President's Office requests are read from it directly. Its
Academic Affairs rows have the justification where the request name should be, so AA requests still come from the
AA alignment file and take their decision, rank and VP comment from the ranking through `AA_CROSSWALK`
(matched on justification + cost using "GenFund and Other Funding Combined 2.xlsx"). AA requests that are not in
the ranking were reviewed on 11/6/2026: 50 were approved with other funding (SWF, SEAP, AB1705, Vintage, AB19,
Lottery, ...) and are listed in `tools/fy27_aa_other_approvals.py` with their funding source. One approved item not in
the AA file (HSS SPSS, $7,500) is added there as a request. The remaining 34 (about $2.2M) have no decision and are not
counted as activities. Update 11/6/2026: the Kitchen (grant funding, in progress) and ASK tutoring (SEAP) were approved, and the other 32 are marked Deferred (`AA_DEFERRED`). The funding source shows in the activity's Funding column ("Resource request – SWF").

- VP comments in the ranking (e.g., "Fund only 1 vehicle at $100,000") are added to the request's note.
- Where the ranked amount differs from the AA file, the note says so. If the AA file had no numeric cost, the
  ranked amount is used.
- The ranking replaces the separate SS and BS area files. The BS area file listed IT's Master Plan and enterprise
  manager requests twice (once under Physical Plant); the ranking has Physical Plant's own requests (project
  tracking system, 3 custodians, maintenance lead).
- `python -m tools.build_db` moves any status/approval entries saved under the old SS area-file keys to the new
  ranking-file keys (`KEY_MIGRATIONS`).

## How strategies were assigned

All FY27 assignments (all five areas) are **proposals from the 11/2026 alignment review** and should be
confirmed by each area.

### FY26

FY26 departments often listed several strategies per request. Each request gets one primary strategy, and
`strategy_source` records how:

1. **Carried from FY27 alignment** – the same request was reviewed in FY27 (27 requests).
2. **Dept-selected (single)** – the department listed one strategy; not independently reviewed (81).
3. **Proposed 11/2026** – department listed several or none; proposed in `tools/fy26_strategy_map.py` (46).

FY26 Student Services follows the same rules (11 carried, 18 single, 13 in `tools/ss_fy26_strategy_map.py`).

Four FY26 AA rows whose request field reads "None" (Kinesiology/HED objectives with no request) are excluded.

## Caveats

- KPIs come from the IERPG student-level file when it is in data/source; otherwise the synthetic sample is used and the app shows a banner.
- FY26 Business Services, Human Resources and President's Office files are not loaded.
- FY26 Student Services: 18 requests use the single strategy the department listed and 11 reuse the FY27
  alignment by request name (generic names such as "Short Term Hourlies" should be checked).
- Strategy leads and measures are proposals pending confirmation by each VP.

## SFF at a Glance (simpler alternative)

A plain-language, read-only version for campus-wide audiences, using the same database:

    python -m streamlit run simple_app.py

- **How our students are doing**: the Fall 2024 completer rate against the 50% goal, how students completed, completion by
  student group, and the early milestones that lead to completion, with the change from the year before.
- **What we're doing about it**: the 4 levers and 25 strategies, each opening to its funded activities (who, cost,
  status), with a school-year switch and a search box.

Updates (approvals, activity status) are still made in the full dashboard (`app.py`).
