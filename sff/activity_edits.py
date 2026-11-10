"""Corrections to activity wording that came from request forms.

ACTIVITY_SPLITS  one request whose activity cell lists several activities -> one activity per item.
                 activity_key -> [(activity text, strategy), ...]. The first item keeps the request's full cost;
                 the others show no cost of their own (they are funded by the same request), so dollar totals
                 are unchanged. Each item gets its own key (<request key>/<n>) for status and results.
ACTIVITY_TEXT    one request whose activity cell lists items from OTHER requests, or carries a stray "1." ->
                 the wording for this request only.
"""
ACTIVITY_SPLITS = {
    # FY26 CourseLeaf CIM (granted $81,101) was split on 11/6/2026, and the split was undone on 11/9/2026
    # (F. Mixson). Its five outcomes belonged to three CourseLeaf products. The meeting-time errors outcome moved to
    # CLSS (row 4) and the catalog outcome to CAT (row 3), so each activity sits under the request that funded it.
    # The course-availability and streamline-scheduling outcomes were dropped as repeats. Saved updates were moved
    # with them (KEY_MIGRATIONS in tools/fy27_ranking_map.py).
}

ACTIVITY_TEXT = {
    # the English cell lists all four department requests (a-d); this request is item d only
    "fy26_aa_requests.xlsm#133": "Purchase a class set of the Norton Anthology of American Literature, volumes 1 and 2, "
                                 "for English 230A and English 230B.",
    "fy26_aa_requests.xlsm#63": "Replace doors on current lockers to allow individual storage for each student.",
    "fy26_ss_requests.xlsm#38": "Develop and implement outreach tactics to increase student awareness of opportunities "
                                "for current and prospective students.",
}

# 2025-26: the request files' "Activities" column holds each department's goals or targets, shared by several
# requests (so the same text appeared under different activities). Each funded request gets its own one-line
# activity, written from the request and its justification (11/9/2026, after F. Mixson spotted a duplicate).
_AA26, _SS26 = "fy26_aa_requests.xlsm#", "fy26_ss_requests.xlsm#"
ACTIVITY_TEXT |= {_AA26 + str(r): t for r, t in {
    3: "Publish and maintain the online catalog in CourseLeaf CAT, increasing its accuracy and currency so students see current program requirements.",
    4: "Decrease the number of meeting time computation errors in the class schedule by building it in CourseLeaf CLSS.",
    8: "Implement CourseLeaf CIM so more departments regularly update their curriculum through periodic review.",
    5: "Build course syllabi in Simple Syllabus from a common template that meets compliance and accessibility standards.",
    6: "Provide Pronto so instructors can message students in Canvas and LCP teams can text their students.",
    7: "Provide CidiLabs tools (DesignPLUS, UDOIT, ReadyGo) so online courses are well designed and accessible.",
    9: "Provide Hypothesis social annotation in Canvas so students read and discuss course texts together.",
    10: "Provide Respondus LockDown Browser for secure online exams.",
    24: "Maintain student access to Lexis Advance, Clio and other legal software required for the paralegal program.",
    30: "Pay enrollment fees for full-time Cerritos Complete students (AB19).",
    31: "Pay enrollment fees for part-time Cerritos Complete students (Vintage).",
    32: "Pay student activity and ASCC fees for Cerritos Complete students (AB19).",
    33: "Fund short-term hourly staff and materials to process dual enrollment applications and support high school partners.",
    34: "Pay Cerritos Complete high school liaisons to attend weekly program and partnership meetings (AB19).",
    36: "Use DualEnroll.com to process dual enrollment applications faster and track their status.",
    37: "Host Cerritos Complete information nights and mail postcards to raise awareness and applications.",
    41: "Hire four Cerritos Complete success coaches to guide students and keep them in the program.",
    43: "Fund a faculty liaison to coordinate dual enrollment instruction with K-12 partners and mentor new dual enrollment faculty.",
    142: "Buy a brain model, polypropylene pans and autoclavable tube racks for biology labs.",
    143: "Buy 16 traveling microscopes for Physics 203.",
    144: "Buy a ballistic pendulum for 100-level physics labs.",
    145: "Provide take-home lab kits so CHEM 100 students can complete the online lab without buying supplies.",
    146: "Buy a class set of iPads, pencils and a cart so CHEM 100 students can collect lab data in the cloud.",
    147: "Buy rock and mineral sets for online and hybrid earth science (ESCI) labs.",
    149: "Buy a 100 MHz NMR spectrometer so chemistry students learn research techniques.",
    160: "Replace the heavy, unsafe door on the Automotive steam bay.",
    161: "Maintain the woodworking (WMT) dust collection system so the equipment can run safely.",
}.items()} | {_SS26 + str(r): t for r, t in {
    3: "Hire a director to oversee the credit recovery program.",
    4: "Fund an Admissions & Records Technician II after the position lost its categorical funding.",
    5: "Fund the outreach Program Assistant II after the position lost its categorical funding.",
    6: "Add an Admissions & Records Technician II to process growing dual enrollment.",
    7: "Keep Deaf/Hard of Hearing mentors and tutors who give DHH students direct language support.",
    8: "Fund student ambassadors who give campus tours, do outreach, and help students apply and enroll.",
    9: "Cover the district share of the Veterans Resource Center program facilitator.",
    10: "Fund part-time Transfer Center counselors to keep current counseling hours.",
    11: "Fund part-time counselors for appointments, drop-ins and division projects now funded by SEAP.",
    12: "Provide Otter.ai notetaking licenses for at least 500 students with disabilities.",
    13: "Hire a full-time GED/credit recovery faculty member for noncredit programs.",
    14: "Fund counseling interns and short-term hourly staff for check-in, scheduling and front-desk help.",
    15: "Hire a part-time licensed mental health counselor for LGBTQ+ students.",
    16: "Backfill a full-time Career Services counselor so appointment levels stay the same.",
    17: "Hire a student conduct and grievances coordinator for the higher volume that comes with student housing.",
    18: "Hire a noncredit program facilitator for onboarding and state reporting in noncredit programs.",
    19: "Host Senior Preview Day for more than 1,500 prospective students.",
    20: "Host Welcome Day for new and continuing students.",
    21: "Hire an apprenticeship program director to oversee the growing apprenticeship program.",
    22: "Hire a full-time GED/ESL faculty member for noncredit programs.",
    23: "Increase the adjunct counselor budget to restore about 150 counseling appointment hours.",
    24: "Send counselors to professional development on supporting students on academic probation and on transfer updates.",
    25: "Fund part-time Umoja counselors to complete ed plans, teach the Umoja counseling course and support Black students.",
    26: "Fund part-time Puente counselors to complete ed plans and support Puente students.",
    27: "Fund part-time counselors for the SEM and Health Occupations LCPs, including the bachelor's degree program.",
    28: "Increase the Career Services short-term hourly budget for front-desk and appointment support.",
    29: "Fund additional short-term hourly staff for counseling check-in, scheduling and phones.",
    30: "Fill the vacant Career Technician position in Career Services.",
    31: "Run transfer workshops and application events through the Transfer Center.",
    32: "Run Puente programming that connects students to campus resources and community.",
    33: "Run Umoja programming that connects students to campus resources and community.",
    34: "Cover counseling software: OnBase transcript review, Advantage orientation and SARS.",
    35: "Fund counseling faculty professional development (conferences and workshops on teaching and student development).",
    36: "Pay for Paradigm diploma and certificate printing as the number of awards grows.",
    37: "Add a Financial Aid Specialist to handle packaging, disbursement and compliance work.",
    38: "Provide book vouchers for students who can't afford books and supplies.",
    39: "Hire a short-term case manager and two LCSWs to meet growing mental health demand.",
    40: "Hire an assistant manager for Mental Health Services.",
    41: "Provide free drug testing devices and education, as AB 1524 requires.",
    42: "Provide emergency grants for students facing financial hardship, including undocumented students.",
    43: "Hire an administrative clerk for the Equity Center front desk.",
}.items()}
