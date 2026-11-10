"""Generate SYNTHETIC KPI results so the dashboard layout can be reviewed.

These numbers are NOT Cerritos College data. Replace with IERPG results in the
same long format (kpi_code, year, group, value) saved as data/kpi_results.csv.
"""
import numpy as np
import pandas as pd

from sff import config as C

rng = np.random.default_rng(2026)
YEARS = ["2020-21", "2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]
# rough starting level and yearly drift for each student KPI (synthetic)
BASE = {"A-K1": (0.45, 0.03), "A-K2": (0.22, 0.01), "A-K3": (0.18, 0.01), "B-K1": (0.40, 0.015),
        "B-K2": (0.38, 0.015), "B-K3": (0.30, 0.01), "B-K4": (0.33, 0.01), "B-K5": (0.28, 0.01),
        "B-K6": (0.20, 0.035), "B-K7": (0.72, 0.005), "B-K8": (0.55, 0.008), "B-K9": (0.50, 0.007),
        "B-K10": (0.29, 0.01), "GOAL": (0.27, 0.011), "C-K1": (0.70, 0.005), "C-K2": (0.25, 0.008)}
OFFSET = {"All students": 0, "African American": -0.08, "Asian": 0.07, "Filipino": 0.05,
          "Hispanic/Latino": -0.02, "White": 0.03, "Two or more races": -0.03}
rows = []
for k, (b, d) in BASE.items():
    for g in C.EQUITY_GROUPS:
        for i, y in enumerate(YEARS):
            v = b + OFFSET[g] + d * i + rng.normal(0, 0.008 if g == "All students" else 0.015)
            rows.append((k, y, g, round(float(np.clip(v, 0.02, 0.98)), 4)))
pd.DataFrame(rows, columns=["kpi_code", "year", "group", "value"]).to_csv(C.KPI_SAMPLE_CSV, index=False)
print("wrote", C.KPI_SAMPLE_CSV, len(rows), "rows")
