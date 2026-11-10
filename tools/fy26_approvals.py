"""FY26 (2025-26) approved resource allocations: "Resource Allocation - Granted, Annual College Plan 2025-26"
(data/source/fy26_approved_gf.xlsx; sent by Felipe Lopez to EC 8/21/2025 and campus-wide 9/4/2025 after the
Board adopted the budget). $1,815,857, 31 items, all one-time, Unrestricted General Fund.

Maps each granted item to its row in the FY26 area file: row -> (funding, granted amount, note).
Granted amounts replace the requested cost (the list shows what was funded).
Items not in an area file are added as requests (ADDED_FY26).
"""
GF = "Unrestricted General Fund (one-time)"

AA_FY26 = {   # 2024-2025 (FY26) Area Resource Requests - Academic Affairs.xlsm
    8: (GF, 81101, ""),     # CourseLeaf CIM (Curriculum)
    146: (GF, 40000, ""),   # CHEM 100 iPad class set and cart
    142: (GF, 2100, ""),    # Brain model, polypropylene pans, tube racks
    149: (GF, 155000, ""),  # Nanalysis 100 MHz multinuclear NMR
    143: (GF, 6200, ""),    # PHYS traveling microscopes (16)
    144: (GF, 3432, ""),    # Cenco ballistic pendulum
    133: (GF, 6000, ""),    # Norton Anthology class sets (ENGL 230A/B)
    147: (GF, 11000, ""),   # Rock and mineral sets (ESCI)
    145: (GF, 3000, ""),    # CHEM 100 take-home kits
    63: (GF, 25000, "Granted list: Music storage lockers for instruments."),
    160: (GF, 5000, "Granted list: replace the unsafe AUTO shop door (matched on justification)."),
    161: (GF, 80000, "Granted list: WMT dust collection system maintenance (matched on justification)."),
}

SS_FY26 = {   # 2024-2025 (FY26) Area Resource Requests - Student Services.xlsm
    7: (GF, 67000, ""),     # Deaf/Hard of Hearing mentors and tutors
    8: (GF, 150000, ""),    # Student Ambassador Budget
    9: (GF, 50000, ""),     # VRC program facilitator (district share)
    19: (GF, 45000, ""),    # Senior Preview Day
    36: (GF, 25000, ""),    # Paradigm
    38: (GF, 100000, ""),   # Book Vouchers
    41: (GF, 7500, ""),     # Drug testing devices
    24: (GF, 20000, ""),    # Counseling professional development
    14: (GF, 134424, "Granted list calls these 'Interns'."),
    10: (GF, 220000, ""),   # Transfer Center part-time counselors
    11: (GF, 125000, "Granted list: part-time counselors for projects currently funded through SEAP."),
    27: (GF, 125000, "Granted list: 'PT Counselors' $125,000; matched to this CG request - confirm."),
    35: (GF, 15000, "Granted list: Student Services professional development $15,000; matched by cost - confirm."),
}

ADDED_FY26 = [   # granted items with no row in a loaded FY26 area file
    {"id": 1, "area": "Academic Affairs", "division": "Academic Affairs", "request": "RSI and AI Professional Development",
     "cost": 30000, "strategy": "B.7", "activity": "Offer RSI and AI professional development for faculty teaching online.",
     "funding": GF, "note": "On the 2025-26 granted list (tagged D.6) but not in the FY26 AA file."},
    {"id": 2, "area": "Academic Affairs", "division": "Academic Affairs", "request": "AI related professional development",
     "cost": 20000, "strategy": "B.7", "activity": "Offer AI-related professional development for faculty.",
     "funding": GF, "note": "On the 2025-26 granted list (tagged D.6) but not in the FY26 AA file."},
    {"id": 3, "area": "Academic Affairs", "division": "Humanities and Social Sciences", "request": "Simulator prep, PD, furniture",
     "cost": 30000, "strategy": "D.6", "activity": "Prepare the HSS simulator space: setup, training, and furniture.",
     "funding": GF, "note": "On the 2025-26 granted list but not in the FY26 AA file."},
    {"id": 4, "area": "Business Services", "division": "Information Technology",
     "request": "Funding to cover the increase in the All Campus Annual Maintenance", "cost": 135000, "strategy": "D.6",
     "activity": "Cover annual software and systems maintenance increases.", "funding": GF,
     "note": "Granted list tagged D.6; assigned to D.6 by F. Mixson 11/9/2026 (same as FY27). BS FY26 area file not loaded."},
    {"id": 5, "area": "President's Office", "division": "Government Relations",
     "request": "Establish & institutionalize a government relations budget", "cost": 97100, "strategy": "D.5",
     "activity": "Establish a government relations budget to pursue state and federal funding.", "funding": GF,
     "note": "President's Office FY26 area file not loaded."},
    {"id": 6, "area": "President's Office", "division": "Public Relations", "request": "Professional (development)",
     "cost": 2000, "strategy": "D.2", "activity": "Public Relations staff professional development.", "funding": GF,
     "note": "President's Office FY26 area file not loaded."},
]


# ---------------------------------------------------------------------------------------------------------------
# Funded from OTHER sources in 2025-26 (not on the general-fund granted list). Confirmed by Frank Mixson 11/9/2026
# ("please include all the items on your 25-26 list"), from the "2025-26 - possibly missing" tab of
# SFF Activities Check - Decisions Needed.xlsx. Amounts are the requested amounts (funded amounts not recorded).
OTHER = "Funded from other sources in 2025-26 (confirmed by F. Mixson 11/9/2026)"
NOT_REC = "Other funds (source not recorded)"
_AMT = "Amount shown is the request; the funded amount isn't recorded."

AA_FY26_OTHER = {
    3: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),    # CourseLeaf CAT
    4: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),    # CourseLeaf CLSS
    5: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),    # Simple Syllabus
    6: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),    # Pronto
    7: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),    # CidiLabs
    9: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),    # Hypothesis
    10: (NOT_REC, None, "Ongoing software; Instructional Equipment in 2026-27. " + _AMT, OTHER),   # Respondus
    24: (NOT_REC, None, "SWF in 2026-27. " + _AMT, OTHER),                                          # Bus. Ed software
    30: ("AB19", None, "Source named in the request. " + _AMT, OTHER),                              # CC fees FT
    31: ("Vintage", None, "Source named in the request. " + _AMT, OTHER),                           # CC fees PT
    32: ("AB19", None, "Source named in the request. " + _AMT, OTHER),                              # CC activities/ASCC fees
    34: ("AB19", None, "Source named in the request. " + _AMT, OTHER),                              # AB19 STH staff
    37: (NOT_REC, None, "Vintage in 2026-27. " + _AMT, OTHER),                                      # Senior Steps
    33: (NOT_REC, None, "Vintage (annual) in 2026-27. " + _AMT, OTHER),                             # DE support
    36: (NOT_REC, None, "Title V grant in 2025-26? " + _AMT, OTHER),                                 # DualEnroll.com
    43: (NOT_REC, None, "Title V grant in 2025-26? " + _AMT, OTHER),                                 # DE faculty liaison
    41: (NOT_REC, None, "Cerritos Complete (AB19/Vintage)? " + _AMT, OTHER),                        # CCPP success coaches
    # 162 (Technology/WMT "Funding for embedded tutors", $150,000) removed 11/9/2026 at F. Mixson's request: it had
    # been listed only because its wording resembled Academic Success's SEAP-funded embedded tutoring; no evidence
    # this Technology request was funded.
}
SS_FY26_OTHER = {r: (NOT_REC, None, "Area-approved; not on the general-fund granted list. " + _AMT, OTHER)
                 for r in (3, 4, 5, 6, 12, 13, 15, 16, 17, 18, 20, 21, 22, 23, 25, 26, 28, 29, 30, 31, 32, 33, 34,
                           37, 39, 40, 42, 43)}

AA_FY26_ALL = AA_FY26 | AA_FY26_OTHER
SS_FY26_ALL = SS_FY26 | SS_FY26_OTHER
