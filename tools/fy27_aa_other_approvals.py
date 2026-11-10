"""FY27 Academic Affairs requests approved OUTSIDE the all-areas ranking (other funding: SWF, SEAP, AB1705,
Vintage, AB19, Lottery, etc.), as confirmed by Frank Mixson on 11/6/2026 from the AA "approved" list.
Instructional Equipment, Vintage, and AB1705 items were all funded (confirmed 11/6/2026).

AA_OTHER_APPROVALS  AA alignment-file row -> (funding / comment from the list, approved amount if it differs
                    from the AA file or the AA file had no numeric cost; else None)
AA_ADDED_REQUESTS   approved requests that are not in the AA FY27 file at all (added as requests).
AA_DEFERRED         the remaining unranked AA requests, marked Deferred by Frank Mixson on 11/6/2026.
"""
AA_OTHER_APPROVALS = {
    54: ('Grant funding (in progress)', None, "Confirmed funded by F. Mixson 11/9/2026"),  # Kitchen (Health Occupation) - confirmed 11/6/2026
    94: ('SEAP', None),  # ASK tutoring - confirmed 11/6/2026
    3: ('Instructional Equipment', None),  # CourseLeaf CLSS (Class Schedule)
    4: ('Instructional Equipment', None),  # CourseLeaf CIM (Curriculum)
    7: ('Instructional Equipment', None),  # Simple Syllabus
    8: ('Instructional Equipment', None),  # Pronto
    10: ('Instructional Equipment', None),  # CidiLabs ReadyGO, UDOIT, DesignPLUS
    12: ('Instructional Equipment', None),  # Annotation / Hypothesis
    13: ('Instructional Equipment', None),  # Respondus Lockdown Browser
    15: ('AB1705', None),  # Engineerica Accudemia ($4,790 license set; the $8,490 set is ranked)
    17: ('PRT for 2025-2026, GP for 2026-2027', None, "Confirmed funded by F. Mixson 11/9/2026"),  # EAB
    18: ('Lottery', None),  # Turnitin
    24: ('SWF', None),  # Software purchase, access, and updates
    31: ('AB19 $700,000 + Vintage $650,000 = $1,350,000', 1350000),  # CCPP Student Fees (AB 19 and Vintage)
    32: ('Vintage (funded annually)', None),  # Annual Dual Enrollment Support (STH, Materials)
    33: ('AB19 (funded annually)', None),  # Cerritos Complete Classified Overtime and Non Instructional 
    34: ('Vintage', None),  # Senior Steps, Marketing: Post Cards, Point Contact Meetings,
    35: ('Increase to general district funds', None, "Confirmed funded by F. Mixson 11/9/2026"),  # Increase Faculty Stipends
    36: ('Title V MADE grant ended; ongoing 20% reassigned time', None, "Confirmed funded by F. Mixson 11/9/2026"),  # Dual Enrollment Faculty Liaison
    37: ('Title V MADE grant ended; SWP Round 10 as fallback', None, "Confirmed funded by F. Mixson 11/9/2026"),  # DualEnroll.com
    45: ('SWF', None),  # (1) FT Program Assistant II/CLINICAL COORDINATOR / ADMIN ASS
    49: ('SWF', None),  # Hire PT dentist.
    50: ('SWF', None),  # Pay for 8 hours per week of part-time faculty AED hours
    51: ('SWF', None),  # STH Clinical Assistants for all PTA labs
    52: ('SWF', None),  # STH Application Specialist for PTA x 20 hours per week x 9 w
    46: ('SWF', None),  # District to fund additional SIM Assistants in the SIM Lab.
    47: ('SWF', None),  # Application Specialist
    48: ('SWF', None),  # (2) PT Clinical Coordinator Assistants designated for nursin
    132: ('AB1705', None),  # Funding for expanding Bootcamps, Math course shell creation,
    118: ('Instructional Equipment', None),  # Subscriptions for WIRIS Assessment which include MathType.
    120: ('Instructional Equipment', None),  # Oxford Nanopore MinION Sequencer
    122: ('Instructional Equipment', None),  # Lung Model
    123: ('Instructional Equipment', None),  # Vernier GC Syringe
    124: ('Instructional Equipment', None),  # Heating Mantle/stir plate combination
    125: ('Instructional Equipment', None),  # Sediment/soil sifters (wooden)
    126: ('Instructional Equipment', None),  # Dissectible Coils and cores for a Physics lab
    127: ('Instructional Equipment', None),  # Rotovap (rotary evaporators)
    128: ('Instructional Equipment', None),  # Apera portable meter (conductivity/TDS/temp/pH/salinity)
    129: ('Instructional Equipment', None),  # Analytical Balance
    114: ('Instructional Equipment', None),  # Biotech Lab Supplies
    115: ('Instructional Equipment', None),  # Celestron - CGX-L Computerized Mount without Tripod 91531-1
    77: ('AB1705', None, "Confirmed funded by F. Mixson 11/9/2026"),  # Modular furniture for LA 110
    78: ('AB1705 (cost TBD)', None, "Confirmed funded by F. Mixson 11/9/2026"),  # Convert LA 105 to classroom/computer lab
    81: ('AB1705', None),  # Funding for English Adjunct Academy
    82: ('Vintage', None),  # Food buget for engagement
    83: ('AB1705', None),  # Two PT Specialized Support I Positions (Academic Success Dat
    85: ('SEAP', None),  # Student Laptop Semester-Loan
    89: ('Vintage', None),  # Money for the book budget
    91: ('SEAP', None),  # Math Tutoring
    92: ('SEAP', None),  # Embedded Tutoring
    101: ('SWF', None),  # Money for law collection
    63: ('Instructional Equipment', 10000),  # Humanoid Bones and carrying case (x2)
}

AA_ADDED_REQUESTS = [
    {"id": 1, "division": "Humanities and Social Sciences", "department": "Psychology", "request": "SPSS",
     "cost": 7500, "resource_type": "Instructional Equipment", "strategy": "B.4", "secondary": None,
     "activity": "Provide SPSS statistics software for Psychology and Economics 210 statistics courses.",
     "funding": "Instructional Equipment", "note": "On the AA approved list (11/6/2026) but not in the AA FY27 request file; annual cost."},
]

# Deferred (11/6/2026): all other FY27 AA requests not in the ranking or the approved list.
AA_DEFERRED = [
    11,  # Academic Affairs - CidiLabs expansion/incentivization
    21,  # Business Education - Program advisor
    22,  # Business Education - Student hourlies
    23,  # Business Education - Faculty hourlies
    28,  # Business Education - Technology and software
    30,  # Business Education - Administrative Clerk II
    58,  # Humanities and Social Sc - Purchase 40 student laptops and charging cart
    59,  # Humanities and Social Sc - SPSS Licensure (30) for Division Laptops
    66,  # Humanities and Social Sc - Simulator Managment and Operation Coordinator
    68,  # Humanities and Social Sc - Faculty reassigned time (Increase from 10% to 20%) or s
    95,  # Academic Success (Librar - Additional funds for adjunct librarians.
    97,  # Academic Success (Librar - Program Facilitator
    102,  # Academic Success (Librar - New CTX Workshop Space - Furniture
    103,  # Academic Success (Librar - Education Technology Trainer
    104,  # Academic Success (Librar - Security gates
    105,  # Academic Success (Librar - Digital licenses for core textbooks
    106,  # Academic Success (Librar - PA system
    107,  # Academic Success (Librar - Increase CTX budget for reclassification of current Off
    108,  # Academic Success (Librar - Increase CTX Budget for professional development aligne
    109,  # Academic Success (Librar - 30 laptops
    110,  # Academic Success (Librar - Stats Crunchsoftware
    111,  # Academic Success (Librar - Locker software subscription.
    112,  # Academic Success (Librar - Signage
    113,  # Academic Success (Librar - Therapy dogs
    117,  # Science, Engineering, an - Expanding MESA AEW support to additional courses and wo
    119,  # Science, Engineering, an - Evening Full-time instructional support staff
    130,  # Science, Engineering, an - AEW-styled Chem 100 workshops
    131,  # Science, Engineering, an - Additional funding for ASEM and SEM students
    133,  # Technology - New computers for lab every 2 years
    134,  # Technology - biannual update computers lab to allow PDM, and advance
    135,  # Technology - Full-time faculty
    136,  # Technology - FT Faculty to support this program.
]
