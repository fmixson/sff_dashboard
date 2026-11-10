"""Proposed primary SFF strategy for FY26 requests where the department listed
several strategies (or none). Keyed by row number in the FY26 'Academic Affairs'
sheet. Requests matching an FY27-reviewed item, or listing a single strategy,
are assigned automatically in sff/etl.py and are not repeated here.

"None" = operational, no direct SFF strategy.
"""
FY26_MANUAL = {
    11: "B.5",   # Grammarly
    21: "A.1",   # BA marketing materials
    22: "C.5",   # BA soft skills dinner / consultants
    30: "A.6",   # Cerritos Complete fees - FT (AB19)
    31: "A.6",   # Cerritos Complete fees - PT (Vintage)
    32: "A.6",   # Cerritos Complete student activities & ASCC fees
    34: "A.2",   # AB19 hourly liaisons at district high schools
    35: "A.3",   # Dual enrollment coordinator
    37: "A.1",   # Senior Steps outreach/marketing (matches FY27 treatment)
    38: "A.3",   # FT dual enrollment counselor
    39: "A.3",   # Dual enrollment A&R technician
    40: "B.5",   # Cerritos Complete PT counselor
    41: "B.5",   # CCPP success coaches
    42: "A.1",   # Remind texting to prospective students
    46: "A.3",   # Dual enrollment GradComm outreach campaign
    47: "A.3",   # CTE Course Connect (dual enrollment CTE)
    48: "B.3",   # Teacher TRAC counselor (ed plans)
    49: "B.5",   # Teacher TRAC success coach
    50: "D.6",   # IT programmer/analyst for Cerritos Complete
    51: "A.3",   # PT dual enrollment counselor
    52: "C.4",   # SERVE coordinator (field experience)
    53: "B.5",   # Learning Communities leadership release time
    54: "B.7",   # LC conferences + FIGs
    55: "B.7",   # LC conferences + FIGs
    56: "B.7",   # LC faculty stipends
    57: "B.5",   # LC hourly marketing/clerical support
    70: "C.1",   # Dental Hygiene director 11-month contract (DHBC compliance)
    73: "C.1",   # PTA neuro lab (clinical partner feedback)
    74: "B.5",   # PTA open-lab faculty hours
    76: "D.2",   # HSS program assistant
    80: "A.1",   # Global Studies coordinator release (promotion)
    81: "C.4",   # SERVE coordination (EDEL)
    82: "B.5",   # Anthropology PTC testing equipment
    83: "A.1",   # Anthropology display case (student interest)
    85: "A.1",   # Political Science posters
    89: "C.1",   # EDEL certificate development (paraprofessional workforce)
    94: "B.7",   # Instruction conference attendance
    98: "B.7",   # Political Science conference attendance
    108: "B.2",  # HED fewer 18-week classes (no $ request)
    115: "A.3",  # HED online/hybrid/high school sections (no $ request)
    120: "C.1",  # KIN training-facility equipment
    121: "C.1",  # HED Community Health Worker certificate (SWP)
    126: "B.1",  # HED recruit faculty
    129: "None", # Liberal Arts copiers (operational)
    130: "B.7",  # Liberal Arts PD (TBD)
    138: "B.5",  # COMM iPads for speech recording
    141: "B.7",  # COMM association memberships
    160: "D.6",  # AUTO equipment / safety door
}
