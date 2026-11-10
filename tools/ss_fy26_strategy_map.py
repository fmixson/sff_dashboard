"""Proposed primary SFF strategy for FY26 Student Services requests where the department
listed several strategies (or none). Keyed by row number in the FY26 'Student Services'
sheet of '2024-2025 (FY26) Area Resource Requests - Student Services.xlsm'.

Requests whose name matches an FY27 Student Services request reuse that FY27 alignment, and
requests listing a single strategy use it (see sff/etl.py). Rows listed here take precedence.
"""
SS_FY26 = {
    4: "A.4",    # A&R Tech II (application processing; categorical funds ended)
    5: "A.1",    # Program Assistant II, School Relations (outreach and recruitment)
    6: "A.3",    # A&R Technician II for Dual Enrollment
    7: "B.5",    # Deaf/Hard of Hearing mentors and tutors
    10: "C.3",   # Transfer Center part-time counselors
    12: "B.5",   # Otter.ai licenses for students with disabilities
    19: "A.2",   # Senior Preview Day (matches FY27 treatment)
    20: "A.5",   # Welcome Day (new-student onboarding)
    28: "C.5",   # Career Services short-term hourlies
    30: "C.5",   # Career Technician (vacant since 2021)
    31: "C.3",   # Transfer Center programming and workshops
    35: "B.7",   # Counseling faculty professional development
    43: "D.2",   # Administrative Clerk II, Equity Center front desk (matches FY27 treatment)
}
