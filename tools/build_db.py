"""Build (or refresh) data/sff.db from the source files in data/source/.

    python -m tools.build_db

Source tables (elements, requests, kpi_results) are rebuilt every run.
The reviews table (status ratings/decisions entered in the app) is NEVER dropped.
"""
import importlib
from datetime import date
import re
import sqlite3
import warnings


import pandas as pd

from sff import cohort, config as C, etl
from sff.data import PERSISTENT_SCHEMA

warnings.filterwarnings("ignore", category=UserWarning, module="openpyxl")


def _load(ref: str):
    """'package.module:NAME' -> the object (mapping dicts live in tools/)."""
    mod, attr = ref.split(":")
    return getattr(importlib.import_module(mod), attr)


def _check_sources():
    """Stop with a clear message if any source workbook is missing from data/source."""
    paths = {C.MATRIX_XLSX}
    for src in C.REQUEST_SOURCES:
        paths.add(src["path"])
        if "ranking" in src:
            paths.add(src["ranking"]["path"])
    missing = sorted(p.name for p in paths if not p.exists())
    if missing:
        raise SystemExit("Missing source file(s) in data\\source — copy them from the zip's data/source folder "
                         "(only these files; keep your data\\sff.db):\n  " + "\n  ".join(missing))


def main():
    _check_sources()
    elements = etl.read_matrix(C.MATRIX_XLSX)

    frames, carry = [], {}
    # FY27 first: its aligned strategies seed carry-over for matching FY26 items in the same area
    for src in sorted(C.REQUEST_SOURCES, key=lambda s: s["fy"], reverse=True):
        fy, area, reader, path = src["fy"], src["area"], src["reader"], src["path"]
        mapping = _load(src["mapping"]) if "mapping" in src else {}
        if reader == "fy27":
            df = etl.read_requests_fy27(path, fiscal_year=fy, area=area)
        elif reader == "fy26":
            df = etl.read_requests_fy26(path, carry.get(area, {}), mapping, fiscal_year=fy, area=area)
        elif reader == "mapped":
            df = etl.read_requests_mapped(path, src["sheet"], mapping, fiscal_year=fy, area=area,
                                          header_row=src.get("header_row", 1), area_filter=src.get("area_filter"),
                                          funded_rows=_load(src["funded"]) if src.get("funded") else None)
        else:
            raise ValueError(f"No reader for {reader}")
        if "ranking" in src:                      # decisions from the all-areas ranking file
            rk = src["ranking"]
            df = etl.apply_ranking(df, rk["path"], _load(rk["crosswalk"]), rk["area_filter"],
                                   funded_rows=_load(rk["funded"]) if rk.get("funded") else None)
        if "other_approvals" in src:              # approved outside the ranking (other funding) / deferred
            df = etl.apply_other_approvals(
                df, _load(src["other_approvals"]),
                _load(src["added_requests"]) if src.get("added_requests") else [], fy, area,
                label=src["other_approvals"].split(":")[0].split(".")[-1] + ".py",
                deferred=_load(src["deferred"]) if src.get("deferred") else None,
                granted_amounts=src.get("granted_amounts", False), clear_unlisted=src.get("clear_unlisted", False),
                **({"approval_label": src["approval_label"]} if "approval_label" in src else {}))
        if fy == "FY27":
            for r in df.itertuples():
                carry.setdefault(area, {}).setdefault(etl.norm(r.request), r.strategy)
        frames.append(df)
        n_app = int(df["area_approval"].eq("Approved").sum())
        print(f"{fy} {area}: {len(df)} requests from {path.name} ({n_app} approved in file)")
    requests = pd.concat(frames, ignore_index=True)

    # strategy -> KPI links parsed from the matrix "Linked KPI(s)" column (e.g. "B-K1, B-K6")
    strat = elements[elements["element_type"] == "Strategy"]
    links = [(r.code, k) for r in strat.itertuples()
             for k in etl.KPI_CODE.findall(str(r.linked_kpis or ""))]
    strategy_kpis = pd.DataFrame(links, columns=["strategy", "kpi_code"]).drop_duplicates()

    # KPI results, in priority order:
    #   1. IERPG student-level report(s) in data/source -> aggregates computed here (identifiers dropped)
    #   2. data/source/kpi_results.csv (already-aggregated results)
    #   3. synthetic sample (placeholder)
    reports = cohort.find_student_reports()
    if reports:
        latest = max(reports, key=lambda p: cohort.as_of_from_filename(p) or date.min)
        as_of = cohort.as_of_from_filename(latest) or date.fromtimestamp(latest.stat().st_mtime)
        students = cohort.read_student_report(latest)
        kpi, sample = cohort.compute_kpis(students, as_of), 0
        awards = cohort.award_counts(students)
        del students   # no student rows are kept
        kpi["source"] = f"{latest.name} (as of {as_of})"
        print(f"KPIs computed from student-level report: {latest.name} (as of {as_of}); "
              f"{kpi['kpi_code'].nunique()} KPIs, cohorts {sorted(kpi['year'].unique())}")
    elif C.KPI_RESULTS_CSV.exists():
        kpi, sample = pd.read_csv(C.KPI_RESULTS_CSV), 0
        if "source" not in kpi:
            kpi["source"] = C.KPI_RESULTS_CSV.name
        print(f"KPIs loaded from {C.KPI_RESULTS_CSV.name} (aggregated results; source: {kpi['source'].iloc[0]})")
    else:
        kpi, sample = pd.read_csv(C.KPI_SAMPLE_CSV), 1
        kpi["source"] = "SAMPLE (synthetic)"
        xl = [p.name for p in C.SOURCE_DIR.iterdir() if p.suffix.lower() in (".xlsx", ".xls", ".xlsm")]
        print("WARNING: no KPI data found, so SAMPLE (synthetic) KPIs were loaded.\n"
              "  Put IERPG's student-level file in data\\source (its name must contain 'KPI - Student Level Report')\n"
              "  or an aggregated data\\source\\kpi_results.csv, then rerun.  Excel files seen: " + ", ".join(xl))
    if not reports:
        awards = pd.read_csv(C.AWARD_COUNTS_CSV) if C.AWARD_COUNTS_CSV.exists() and not sample else \
            pd.DataFrame(columns=["year", "award_type", "award", "students"])
    if "dimension" not in kpi:
        kpi["dimension"] = kpi["group"].map(lambda g: "All" if g == "All students" else "Race/ethnicity")
    for c in ("numerator", "denominator"):
        if c not in kpi:
            kpi[c] = None
    kpi["is_sample"] = sample

    with sqlite3.connect(C.DB_PATH) as con:
        elements.to_sql("elements", con, if_exists="replace", index=False)
        requests.to_sql("requests", con, if_exists="replace", index_label="id")
        kpi.to_sql("kpi_results", con, if_exists="replace", index=False)
        if not sample and reports:   # keep a de-identified copy (aggregates only, small cells suppressed)
            kpi.drop(columns=["is_sample"], errors="ignore").to_csv(C.KPI_RESULTS_CSV, index=False)
            awards.to_csv(C.AWARD_COUNTS_CSV, index=False)
        awards.to_sql("award_counts", con, if_exists="replace", index=False)
        strategy_kpis.to_sql("strategy_kpis", con, if_exists="replace", index=False)
        con.executescript(PERSISTENT_SCHEMA)   # reviews, measure_results, activity_status, kpi_targets
        # move app entries to new activity keys when a request's source file changes
        from tools.fy27_ranking_map import KEY_MIGRATIONS
        # keys saved by a Windows build before 11/9/2026 carried the full file path ("C:\\...\\file.xlsm#8");
        # keep only the file name so they match the activities again
        fixed = 0
        for t in ("activity_status", "request_approvals", "activity_strategy", "activity_text"):
            for (k,) in con.execute(f"SELECT DISTINCT activity_key FROM {t}").fetchall():
                path, sep, row = str(k).partition("#")          # only the part before "#" can carry a path;
                if sep and re.search(r"[\\/]", path):          # "file#8/2" (a split activity) is left alone
                    fixed += con.execute(f"UPDATE {t} SET activity_key = ? WHERE activity_key = ?",
                                         (re.split(r"[\\/]", path)[-1] + "#" + row, k)).rowcount
        if fixed:
            print(f"Fixed {fixed} saved entries whose keys carried a full file path")
        moved = 0
        for old, new in KEY_MIGRATIONS.items():
            for t in ("activity_status", "request_approvals", "activity_strategy", "activity_text"):
                moved += con.execute(f"UPDATE {t} SET activity_key = ? WHERE activity_key = ?", (new, old)).rowcount
        if moved:
            print(f"Moved {moved} saved entries to their new activity keys")
        con.execute("DROP TABLE IF EXISTS meta")
        con.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT)")
        con.execute("INSERT INTO meta VALUES ('built', datetime('now','localtime'))")
    print(f"elements={len(elements)} requests={len(requests)} strategy_kpi_links={len(strategy_kpis)} "
          f"kpi_rows={len(kpi)} sample_kpis={bool(sample)}")
    print(requests.groupby(["fiscal_year", "area", "strategy_source"]).size().to_string())


if __name__ == "__main__":
    main()
