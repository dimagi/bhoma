
# used to render the report. These values must align with couch's emits
ADULT_PI_DISPLAY = {
    "bp_rec": [False, "Blood Pressure Recorded", "'Blood Pressure' recorded under Vitals section."],
    "vit_rec": [False, "Vitals recorded", "Temperature, Respiratory Rate, and Heart Rate under Vitals section recorded."],
    "mal_mgd": [False, "Malaria Managed", "Febrile adult given RDT, and managed according to result (antimalarial if POS; none if NEG)."],
    "hiv_test": [False, "HIV Test Ordered", "HIV test done in previously non-reactive or untested adults with asterisked (*) symptoms or diagnoses."],
    "drugs_stocked": [False, "Drugs In Stock", "Protocol recommended prescriptions in stock at the clinic."],
}

UNDER_5_PI_DISPLAY = {
    "ht_wt_rec": [False, "Height and weight recorded", "Height and Weight under Vitals section recorded."],
    "vit_rec": [False, "Vitals recorded", "Temperature, Respiratory Rate, and Heart Rate under Vitals section recorded."],
    "hiv_test": [False, "HIV Test Ordered", "Tests done for untested/at-risk children, or children with previous negative or unknown status with asterisked (*) symptoms or diagnoses."],
    "wt_assessed": [False, "Weight for age assessed", "Weight for age standard deviation (Z-score) calculated correctly on patients under 5."],
    "low_wt_follow": [False, "Low Weight Followed Up", "Severely malnourished or very low weight children admitted, referred, or asked to follow-up at clinic."],
    "fev_mgd": [False, "Fever Managed", "Febrile children given RDT, and managed according to severity and RDT result (antimalarial if POS; antibiotic if severe and NEG)."], 
    "dia_mgd": [False, "Diarrhea Managed", "Children with moderately dehydration given ORS, severe dehydration given IV fluids, and dysentery given antibiotics."],
    "rti_mgd": [False, "RTI Managed", "Paediatric patients with severe or moderate RTIs given antibiotics."],
    "pallor_mgd": [False, "Hgb/Hct for Pallor", "Hgb or Hct test done for paediatric patients with pallor."],
    "fu_rec": [False, "Visits Concluded", "Follow-up PRN, follow-up at health facility, death, or referral ticked."],
    "drugs_stocked": [False, "Drugs In Stock", "Protocol recommended prescriptions in stock at the clinic."],
}

PREGNANCY_PI_DISPLAY = {
    "preeclamp": [False, "Preeclampsia Screening", "Blood Pressure recorded and results received for Urinalysis Protein test."],
    "clin_exam": [False, "Clinical Exam", "Fundal Height (GA > 16 weeks), Presentation (GA > 28 weeks), and Fetal Heart Rate (GA > 16 weeks) recorded."],
    "hiv_test": [False, "HIV Test Done", "HIV test results recorded at first ANC visit."],
    "drugs_stocked": [False, "Drugs In Stock", "Protocol recommended prescriptions in stock at the clinic."],
    "maternal_hiv": [False, "Maternal HIV", "For HIV-positive women not already on HAART, an antiretroviral is prescribed on the Delivery form."],
    "infant_nvp": [False, "Infant NVP", "Infants of HIV-positive mothers prescribed NVP after delivery."],
    "del_mgmt": [False, "Delivery Mgmt", "Severe symptoms referred or admitted, fluids given for fetal distress, severe vaginal bleeding given oxygen and fluids, and uterine infection given antibiotics."],
    "preeclamp_mgd": [False, "Pre-eclampsia Managed","Patients with high blood pressure, proteinuria, and symptoms of pre-eclampsia after GA of 20 weeks."],
    "nvp_1st_visit": [False, "NVP First Visit", "HIV-positive women not already on HAART dispensed NVP on first visit with a reactive test recorded."],
    "azt_1st_visit": [False, "AZT First Visit", "HIV-positive women not already on HAART dispensed AZT on first visit with a reactive test recorded after GA of 14 weeks."],
    "azt_haart": [False, "AZT/Haart", "HIV-positive women given either AZT or on HAART, recorded at both current and previous visits after GA of 14 weeks."],
    "rpr_1st_visit": [False, "RPR 1st visit", "RPR result recorded at first ANC visit."],
    "rpr_pen": [False, "RPR+ Penicillin", "Women testing RPR-positive given a dose of penicillin at the same visit."],
    "rpr_partner": [False, "RPR+ Partner", "Women testing RPR-positive whose partners are given penicillin at the visit after the womans test done."],
    "fansidar": [False, "Fansidar", "3 doses of Fansidar given during pregnancy."],
}

REPORTS = {
    "adult_pi": {"name": "Adult Performance Indicator Report",
                 "view": "reports/adult_pi",
                 "cols": ADULT_PI_DISPLAY},
    "pregnancy_pi": {"name": "Pregnancy Performance Indicator Report",
                     "view": "reports/pregnancy_pi",
                     "cols": PREGNANCY_PI_DISPLAY},
    "under_5_pi": {"name": "Under 5 Performance Indicator Report",
                   "view": "reports/under_5_pi",
                   "cols": UNDER_5_PI_DISPLAY},
}

def get_name(report_slug):
    return REPORTS[report_slug]["name"]

def get_view_name(report_slug):
    return REPORTS[report_slug]["view"]

def get_cols(report_slug):
    return REPORTS[report_slug]["cols"]

def is_hidden(report_slug, col_slug):
    if col_slug in get_cols(report_slug):
        return get_cols(report_slug)[col_slug][0]
    return True  # we assume things that aren't listed are hidden

def get_display_name(report_slug, col_slug):
    if col_slug in get_cols(report_slug):
        return get_cols(report_slug)[col_slug][1]
    return col_slug

def get_description(report_slug, col_slug):
    if col_slug in get_cols(report_slug):
        return get_cols(report_slug)[col_slug][2]
    return col_slug
