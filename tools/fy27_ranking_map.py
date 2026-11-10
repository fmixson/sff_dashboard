"""FY27 all-areas ranking (2025-2026 FY27 Area Resource Requests ALL AREAS_Ranking.xlsx).

This is the institutional list with the President/VP decision (Area Approval) for every area. Keys are
row numbers in its 'Resource Requests' sheet.

RANKING_FY27  Student Services, Business Services, Human Resources and President's Office requests are read
              from the ranking file: row -> (primary, secondary, activity, note). SS and BS alignments carry
              over from the 11/2026 review of each area file; HR, President's Office and the three Physical
              Plant rows are new proposals.
AA_CROSSWALK  Academic Affairs rows in the ranking file have no request names (the column holds the
              justification), so AA requests stay in the FY27 alignment file and take their decision
              from the ranking row: ranking row -> AA alignment-file row. Matched on justification and
              cost through the "GenFund and Other Funding Combined" list.
KEY_MIGRATIONS  activity keys from the retired Student Services area file -> ranking-file keys, so status
              and approvals already entered in the app follow their request.
"""
RANKING_FY27 = {
    # --- Student Services (alignment from the SS area file review)
    9: ('B.5', 'B.2', 'Pay data coach stipends so LCP success teams can identify at-risk second- and third-year students and reach out to keep them enrolled.', ''),
    15: ('B.2', 'C.2', 'Sustain a records evaluator (original funding ended) to process degree and ADT award evaluations.', 'Dept listed 7 strategies.'),
    21: ('B.5', '', 'Cover the district share of the Veterans Resource Center program facilitator to sustain services for military-connected students.', ''),
    26: ('B.3', 'B.6', 'Fund adjunct counselors so first-year students complete a comprehensive educational plan (CSEP).', ''),
    31: ('A.1', 'A.2', 'Fund student ambassadors who represent the college at outreach events and staff the Welcome, ID, and Admissions centers.', ''),
    35: ('B.6', '', "Replenish Falcon's Finest pins and cards recognizing students at each momentum point (bronze, silver, gold).", 'Only SS request directly funding B.6.'),
    41: ('A.5', 'A.4', 'Hire a noncredit program facilitator to onboard students into noncredit programs, including credit recovery.', ''),
    44: ('C.5', 'B.2', 'Backfill Career Services counselor time (articulation and Cerritos Complete release) to keep career counseling appointments available.', ''),
    47: ('A.2', 'A.1', 'Host Senior Preview Day for graduating high school seniors and their families.', ''),
    50: ('B.5', '', 'Increase part-time counseling hours so international students have counseling access all five days.', ''),
    53: ('B.5', '', 'Hire a part-time licensed mental health counselor for the Equity Center (LGBTQ+ students).', ''),
    56: ('C.3', 'C.2', 'Fund part-time Transfer Center counselors for transfer appointments, application workshops, and CSEPs (beyond SEAP funding).', ''),
    59: ('A.2', '', 'Host a high school counselor conference to strengthen feeder-school partnerships.', ''),
    62: ('A.6', 'B.5', 'Provide emergency grants to students facing financial hardship, including undocumented students.', ''),
    67: ('C.5', '', 'Restore adjunct counseling hours in Career Services (about 150 appointment hours lost to cost increases).', ''),
    70: ('None', '', 'Pay for Paradigm diploma and certificate production as award volume grows.', 'Operational; supports completion recognition but no direct strategy.'),
    73: ('B.3', 'B.6', 'Fund adjunct counselors for Umoja and Puente to build CSEPs with 15 units scheduled and promote completing 15 units in year one.', ''),
    76: ('A.5', 'B.3', 'Fund counseling interns/hourlies to support onboarding (Buccaneers, Cerritos Complete Super Saturdays) and the Umoja/Puente space.', ''),
    77: ('C.3', '', 'Run Transfer Center programming: Transfer Academy seminars, application workshops, university tours, Transfer Bootcamp, Signing Day.', ''),
    79: ('A.6', 'B.5', 'Provide book vouchers for students who cannot afford books and supplies.', 'Dept selected A.1.'),
    81: ('C.3', '', 'Fund summer short-term hourly staff for Transfer Center check-in and drop-in sessions.', ''),
    83: ('A.6', 'B.5', 'Fund an adjunct counselor for financial aid SAP appeals so students keep aid eligibility (AB 789).', ''),
    84: ('B.2', 'A.4', 'Upgrade a program assistant to instructional schedule specialist for noncredit and apprenticeship scheduling.', ''),
    86: ('C.5', '', 'Fund Career Services front-desk hourlies to schedule counseling and employment appointments.', ''),
    88: ('A.1', '', 'Produce outreach publications for prospective students, families, counselors, and community partners.', ''),
    90: ('B.5', 'B.3', 'Fund an Umoja program facilitator for retention and completion programming.', ''),
    92: ('B.5', 'B.3', 'Fund a Puente program facilitator for retention and completion programming.', ''),
    94: ('D.2', '', 'Add an administrative clerk for the shared International Student Services front desk (serves 6 programs).', 'Cost is a shared estimate ($139,000 total, about $47,000 per department).'),
    96: ('D.2', '', 'Realign the division secretary to be fully dedicated to Student Equity and Success (12 programs).', ''),
    98: ('D.4', 'D.1', 'Hire a Student Conduct & Grievances coordinator to handle the added volume tied to student housing.', 'Housing-related support; confirm.'),
    101: ('B.2', 'C.2', 'Make the temporary records evaluator a permanent full-time role for award evaluations.', ''),
    103: ('B.5', 'B.6', 'Hire a full-time EOPS specialist to support growing CARE and NextUp caseloads.', ''),
    105: ('A.6', 'A.1', 'Maintain HighPoint financial aid tools (Message Center, SIS automation) to reach students about aid.', ''),
    107: ('C.6', 'C.2', "Hire a full-time apprenticeship/bachelor's degree faculty member through the faculty hiring process.", 'Area approval blank in source.'),
    109: ('A.6', '', 'Maintain Ellucian financial aid products (Student Forms, Campus Communicator) for secure aid document submission.', ''),
    111: ('C.4', 'C.5', 'Fill the Career Technician position (vacant since 2021) to expand paid internships and student employment.', ''),
    113: ('D.2', '', 'Add an Admin Secretary I for Financial Aid budget, payroll, and clerical workload.', ''),
    115: ('C.5', '', 'Purchase giveaways and promotional items to draw students to Career Services events.', ''),
    117: ('C.3', '', 'Purchase supplies, a color copier, and event food for Transfer Center programming.', ''),
    119: ('B.7', '', 'Bring retention-strategy speakers to counseling and send counselors to UC/CSU conferences.', ''),
    121: ('D.6', '', 'Counseling software (amount $65,000).', 'Activity and justification text appear copied from the hourly request; confirm what the software is.'),
    123: ('D.6', '', 'Hire a user support specialist for counseling division software and data processing.', 'No cost entered.'),
    133: ('C.6', '', 'Hire an apprenticeship program director to oversee a growing apprenticeship program.', "Area rank 'Cat Fun' (categorical funding)."),
    134: ('A.5', 'C.6', "Hire an apprenticeship program facilitator for outreach and onboarding, including the bachelor's degree.", "Area rank 'Cat Fun' (categorical funding)."),
    # --- Business Services (alignment from the BS area file review)
    8: ('D.6', '', 'Cover annual maintenance increases (PeopleSoft, Microsoft, VMware, Zoom Rooms, Adobe, 911 compliance).', 'Assigned to D.6 (technology infrastructure) by F. Mixson 11/9/2026.'),
    14: ('D.1', 'D.6', 'Adopt bank P-card software and train card users so employees can pay travel costs without using personal funds.', 'No cost given. Dept listed D.5 (revenue); no revenue link.'),
    19: ('D.1', 'D.6', 'Subscribe to budget software (Euna) that integrates budgeting, position control, and grant management.', ''),
    20: ('D.1', 'D.6', 'Implement the budget software: configuration, data migration, and staff training.', ''),
    25: ('D.1', 'D.6', 'Use FIN document scanning to go paperless (e.g., W-9s for year-end 1099 processing) and train staff.', 'No cost given. Dept listed D.5 (revenue); no revenue link.'),
    38: ('D.6', '', 'Replace two 2016 patrol vehicles with chronic mechanical failures (over $10K/yr each in repairs) to keep campus police response reliable.', ''),
    40: ('D.6', 'D.2', 'Hire a manager of enterprise applications to lead PeopleSoft updates, modifications, and add-ons.', ''),
    46: ('D.6', '', 'Replace an aging golf cart used daily by cadets for parking enforcement.', ''),
    49: ('D.2', '', 'Train one additional officer as a Rape Aggression Defense (RAD) instructor to offer self-defense classes.', ''),
    52: ('D.6', '', 'Replace staff computers on a five-year cycle.', ''),
    55: ('D.6', '', 'Replace student lab computers on a five-year cycle.', 'Most directly student-facing IT request.'),
    58: ('D.6', '', 'Replace servers and network devices on their lifecycle schedules to keep systems secure.', ''),
    61: ('D.6', '', 'Fund new technology and software requests that arise during the year.', 'Unallocated pool; ask IT to name the planned uses.'),
    64: ('D.6', '', 'Add, replace, or upgrade HyFlex classroom audio-visual equipment.', ''),
    66: ('D.6', 'D.1', 'Continue PeopleSoft optimization: regulatory reporting changes, new functionality, and modernization.', ''),
    69: ('D.6', '', 'Replace the campus phone system.', 'Justification copied from row 20; ask IT for the phone-system justification.'),
    72: ('D.6', '', 'Replace older and failing security cameras.', "Activity text in file (mandated reports) doesn't match the request."),
    75: ('D.6', 'D.1', 'Implement Phase I of the Information Technology Master Plan.', ''),
    135: ('D.2', 'D.1', 'Reclassify an accountant doing out-of-class work since the FIN/BEST accounting system conversion (to Grade 35 or higher).', 'Dept also listed D.3 and C.1; no hiring or career link.'),
    136: ('D.1', 'D.2', 'Add a full-time budget technician to shorten turnaround for budget development, adjustments, and grant transactions.', ''),
    137: ('D.2', 'D.1', 'Reclassify an accountant doing out-of-class work since the FIN/BEST conversion (to Grade 32).', 'Dept also listed D.3 and C.1; no hiring or career link.'),
    # --- new: Physical Plant, Human Resources, President's Office
    30: ('D.1', 'D.6', 'Adopt a project tracking system to organize Physical Plant projects, deadlines, and resources.', ''),
    34: ('D.6', '', 'Hire three custodians for the new Student Services and Administration Building (about 49,830 sq ft), staffed to APPA standards.', ''),
    43: ('D.6', 'D.2', 'Create a Maintenance and Trades lead position to coordinate daily maintenance work.', ''),
    11: ('D.1', '', 'Set up NeoGov eForms to automate HR compliance forms (e.g., TB clearance) for new hires and employees.', 'One-time setup fee.'),
    12: ('D.1', '', 'Pay the NeoGov eForms annual fee.', 'Annual fee for row 11.'),
    17: ('D.1', '', 'Add Revver AI features to speed high-volume personnel file entry.', ''),
    22: ('D.3', 'D.1', 'Set up NeoEd Onboard so new-hire paperwork and TB clearance move online.', 'One-time setup cost.'),
    23: ('D.3', 'D.1', 'Pay the NeoEd Onboard subscription for online employee onboarding.', 'Ongoing cost for row 22.'),
    27: ('D.3', '', 'Set up the NeoEd export feature to track new-hire demographic data for EEO Plan compliance and equitable hiring.', 'One-time setup fee.'),
    28: ('D.3', '', 'Pay the NeoEd export feature annual fee.', 'Annual fee for row 27.'),
    32: ('None', '', 'Increase the legal fees budget for employee relations matters.', 'Operational (legal counsel). Dept listed D.1.'),
    36: ('D.3', '', 'Fund short-term hourly staff to speed new-employee onboarding and cover HR reception and phones.', "Cost stated as 'Additional $20k'."),
    10: ('A.1', '', 'Expand targeted digital, print, and multimedia campaigns for enrollment, transfer, and support services.', ''),
    16: ('A.4', 'D.6', 'Improve usability and accessibility of high-traffic student-facing web pages and sustain the website CMS.', ''),
    138: ('D.5', 'D.2', 'Train Foundation staff in fundraising and major-gift moves management.', ''),
    139: ('D.5', '', 'Hire a grants manager to increase competitive grant applications and awards (e.g., Title III, Title V).', ''),
    140: ('A.1', 'D.6', 'Adopt digital asset management software for campus photo and video assets.', ''),
    141: ('D.2', '', 'Train Public Relations staff in higher-education communications, digital marketing, and accessibility.', ''),
    142: ('None', '', 'Adopt a centralized event and stakeholder management system for trustee, legislative, and executive events.', 'Operational. Dept listed D.5.'),
}

AA_CROSSWALK = {
    13: 5,
    18: 6,
    24: 9,
    29: 14,
    33: 16,
    37: 19,
    39: 20,
    42: 38,
    45: 39,
    48: 40,
    51: 99,
    54: 88,
    57: 90,
    60: 98,
    63: 75,
    65: 116,
    68: 61,
    71: 86,
    74: 25,
    78: 26,
    80: 65,
    82: 43,
    85: 44,
    87: 121,
    89: 74,
    91: 73,
    93: 42,
    95: 60,
    97: 80,
    99: 87,
    100: 93,
    102: 53,
    104: 69,
    106: 100,
    108: 72,
    110: 76,
    112: 27,
    114: 64,
    116: 29,
    118: 67,
    120: 57,
    122: 70,
    124: 41,
    126: 84,
    127: 62,
    128: 79,
    129: 55,
    130: 96,
    131: 56,
    132: 71,
}

KEY_MIGRATIONS = {
    # 11/9/2026: CourseLeaf CIM split undone. Updates follow each outcome to the request that funded it.
    "fy26_aa_requests.xlsm#8/1": "fy26_aa_requests.xlsm#8",   # curriculum review stays with CIM
    "fy26_aa_requests.xlsm#8/2": "fy26_aa_requests.xlsm#4",   # meeting-time errors -> CLSS
    "fy26_aa_requests.xlsm#8/3": "fy26_aa_requests.xlsm#3",   # catalog accuracy -> CAT
    "fy27_ss_requests.xlsx#3": "fy27_all_areas_ranking.xlsx#9",
    "fy27_ss_requests.xlsx#4": "fy27_all_areas_ranking.xlsx#15",
    "fy27_ss_requests.xlsx#5": "fy27_all_areas_ranking.xlsx#21",
    "fy27_ss_requests.xlsx#6": "fy27_all_areas_ranking.xlsx#26",
    "fy27_ss_requests.xlsx#7": "fy27_all_areas_ranking.xlsx#31",
    "fy27_ss_requests.xlsx#8": "fy27_all_areas_ranking.xlsx#35",
    "fy27_ss_requests.xlsx#9": "fy27_all_areas_ranking.xlsx#41",
    "fy27_ss_requests.xlsx#10": "fy27_all_areas_ranking.xlsx#44",
    "fy27_ss_requests.xlsx#11": "fy27_all_areas_ranking.xlsx#47",
    "fy27_ss_requests.xlsx#12": "fy27_all_areas_ranking.xlsx#50",
    "fy27_ss_requests.xlsx#13": "fy27_all_areas_ranking.xlsx#53",
    "fy27_ss_requests.xlsx#14": "fy27_all_areas_ranking.xlsx#56",
    "fy27_ss_requests.xlsx#15": "fy27_all_areas_ranking.xlsx#59",
    "fy27_ss_requests.xlsx#16": "fy27_all_areas_ranking.xlsx#62",
    "fy27_ss_requests.xlsx#17": "fy27_all_areas_ranking.xlsx#67",
    "fy27_ss_requests.xlsx#18": "fy27_all_areas_ranking.xlsx#70",
    "fy27_ss_requests.xlsx#19": "fy27_all_areas_ranking.xlsx#73",
    "fy27_ss_requests.xlsx#20": "fy27_all_areas_ranking.xlsx#76",
    "fy27_ss_requests.xlsx#21": "fy27_all_areas_ranking.xlsx#77",
    "fy27_ss_requests.xlsx#22": "fy27_all_areas_ranking.xlsx#79",
    "fy27_ss_requests.xlsx#23": "fy27_all_areas_ranking.xlsx#81",
    "fy27_ss_requests.xlsx#24": "fy27_all_areas_ranking.xlsx#83",
    "fy27_ss_requests.xlsx#25": "fy27_all_areas_ranking.xlsx#84",
    "fy27_ss_requests.xlsx#26": "fy27_all_areas_ranking.xlsx#86",
    "fy27_ss_requests.xlsx#27": "fy27_all_areas_ranking.xlsx#88",
    "fy27_ss_requests.xlsx#28": "fy27_all_areas_ranking.xlsx#90",
    "fy27_ss_requests.xlsx#29": "fy27_all_areas_ranking.xlsx#92",
    "fy27_ss_requests.xlsx#30": "fy27_all_areas_ranking.xlsx#94",
    "fy27_ss_requests.xlsx#31": "fy27_all_areas_ranking.xlsx#96",
    "fy27_ss_requests.xlsx#32": "fy27_all_areas_ranking.xlsx#98",
    "fy27_ss_requests.xlsx#33": "fy27_all_areas_ranking.xlsx#101",
    "fy27_ss_requests.xlsx#34": "fy27_all_areas_ranking.xlsx#103",
    "fy27_ss_requests.xlsx#35": "fy27_all_areas_ranking.xlsx#105",
    "fy27_ss_requests.xlsx#36": "fy27_all_areas_ranking.xlsx#107",
    "fy27_ss_requests.xlsx#37": "fy27_all_areas_ranking.xlsx#109",
    "fy27_ss_requests.xlsx#38": "fy27_all_areas_ranking.xlsx#111",
    "fy27_ss_requests.xlsx#39": "fy27_all_areas_ranking.xlsx#113",
    "fy27_ss_requests.xlsx#40": "fy27_all_areas_ranking.xlsx#115",
    "fy27_ss_requests.xlsx#41": "fy27_all_areas_ranking.xlsx#117",
    "fy27_ss_requests.xlsx#42": "fy27_all_areas_ranking.xlsx#119",
    "fy27_ss_requests.xlsx#43": "fy27_all_areas_ranking.xlsx#121",
    "fy27_ss_requests.xlsx#44": "fy27_all_areas_ranking.xlsx#123",
    "fy27_ss_requests.xlsx#46": "fy27_all_areas_ranking.xlsx#133",
    "fy27_ss_requests.xlsx#47": "fy27_all_areas_ranking.xlsx#134",
}

# ---------------------------------------------------------------------------------------------------------
# What was actually FUNDED (11/6/2026). "Approved" in the ranking file = area-approved and ranked, not funded.
# Felipe Lopez (8/17/2026, "RE: 2026-27 Resource Allocation"): "We have enough surplus to allocate only $1 million
# in resource requests as highlighted in the worksheet." The highlighted (yellow) block is the top of the
# interleaved ranking: sheet rows 8-26, $1,081,671 (the workbook's own subtotal in cell M4). Conrad Selorio's
# 9/16/2026 notice to Academic Affairs lists exactly the three AA items in that block (rows 13, 18, 24).
# Ranked items below the line are "Not approved - ranked, not funded". Rows ranked "Cat Fun" were approved for
# categorical funding and stay approved.
FUNDED_GF_FY27 = set(range(8, 27))

# Funded rows with their funding label. Row 136 (BS Full-Time Budget Technician, $125,000) is marked Approved in the
# ranking without a rank; Frank Mixson confirmed on 11/6/2026 that it was approved.
FUNDED_FY27 = {r: "General fund (2026-27 allocation)" for r in FUNDED_GF_FY27} | {
    136: "Approved outside the ranked list (confirmed 11/6/2026)",
}
