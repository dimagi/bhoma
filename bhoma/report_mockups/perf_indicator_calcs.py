
#-------------------------------------------------------------------------------
#*******************************************************************************
#Under-Five Clinic Performance Indicators
#-------------------------------------------------------------------------------

def add_ped_pi_to_form(ped_form):
    '''Adds Under Five Clinic Performance Indicators to dictionary created from each
    Under Five Visit form.  Pass in form dictionary'''

    (mgmt_na, mgmt_bad, mgmt_good) = (0,1,2)   

    #-----------------------------------------------
    #1. Height and Weight Recorded on each form (unless within last month 
    # or for a follow-up appointment - take this into account during aggregation
    if ped_form['new_case'] and ped_form['height'] and ped_form['weight']:
        ped_form['pi_height_weight'] = mgmt_good
    else:
        #TODO: Figure out if last visit within a month
        if ped_form['new_case'] and last_visit_within_month:
            ped_form['pi_height_weight'] = mgmt_good
        else:
            ped_form['pi_height_weight'] = mgmt_bad
 
    #-----------------------------------------------
    #2. Temperature, respiratory rate, and heart rate recorded
    if ped_form['temp'] and ped_form['resp_rate'] and ped_form['heart_rate']:
        ped_form['pi_vitals'] = mgmt_good
    else:
        ped_form['pi_vitals'] = mgmt_bad

    #-----------------------------------------------
    #3. HIV test ordered appropriately
    
    #Check for any symptoms with an * to see if at risk for HIV
    #TODO = can pass in just 'symptoms...'
    hiv_symptoms_present = check_list('ped_hiv_symptoms',ped_form['symptoms'])
    
    if (ped_form['hiv_exposed'] or ped_form['hiv_unknown']) or \
       (ped_form['hiv_not_exposed'] and hiv_symptoms_present):
        if ped_form['hiv_test_rapid']:
            ped_form['pi_hiv_test'] = mgmt_good
        elif ped_form['hiv_test_pcr']:
            ped_form['pi_hiv_test'] = mgmt_good
        else:
            ped_form['pi_hiv_test'] = mgmt_bad
    else:
        ped_form['pi_hiv_test'] = mgmt_na

    #-----------------------------------------------
    #4. Weight for age assessed correctly
    #TODO
    # Get Z-score for ped
    #for L != 0, Z = (((X/M)^L)-1)/(L*S)
    #for L == 0, Z = ln(x/m)/x
    import standard_normal_table
    import math
    
    #Get age and sex for calculations, sex from patient registration form
    ped_age = ped_form['years'] + (ped_form['months'] / 12) + (ped_form['weeks'] / 52)
    #TODO: create lookup function lookup by ped_form.patiend_id reg_form.sex
    ped_sex = lookup(reg_form['gender'],ped_form['patient_id'])
    
    #Get zscore from standard normal tables
    #TODO - this mess once have data
    #sn_data_table from file input
    #sn_data_table = [sex][age][L][M][S]
    #round ped_age in a given way
    
    #Return row of data needed, found by age and sex
  #  for data_row in sn_data_table:
 #       while sn_data[:][0] == reg_form.sex:
 #           while sn_data[:][1] <= ped_age:
                #increment until find desired row
                
    #lookup in standard_normal_table L,M,S using ped_age, ped_form.weight, reg_form.sex
    if l_value == 0:
        z_score_calc = log1p(ped_form['weight'] / sn_data_table[data_row][3]) / ped_form['weight']
    else:
        z_score_calc = (((ped_form['weight'] / sn_data_table[data_row][3])^sn_data_table[data_row][2]) - 1) \
                       / (sn_data_table[data_row][2] * sn_data_table[data_row][4])
    
    #Check calculated z_score with recorded z_score
    if (z_score_calc > 0 and ped_form['wfa_pos']) or \
       ((0 >= z_score_calc > -2) and ped_form['wfa_zero_neg_two']) or \
       ((-2 >= z_score_calc > -3) and ped_form['wfa_neg_two_neg_three']) or \
       (z_score_calc <= -3 and ped_form['wfa_neg_three']):
        ped_form['pi_wfa_correct'] = mgmt_good
    else:
        ped_form['pi_wfa_correct'] = mgmt_bad

    #--------------------------------------
    #5. Low weight for age managed appropriately
    if ped_form['assess_lwfa'] and not ped_form['mild_lwfa']:
        if ped_form['referral'] or ped_form['follow_up_needed']:
            ped_form['pi_lwfa_mgmt'] = mgmt_good
        else:
            ped_form['pi_lwfa_mgmt'] = mgmt_bad
    else:
        ped_form['pi_lwfa_mgmt'] = mgmt_na
        
    #-----------------------------------------
    #6. Fever managed appropriately
    if ped_form['assess_fever']:
        severe_fever = ped_form['sev_fever_one_week'] or ped_form['stiff_neck']
        if ped_form['test_malaria_pos'] and severe_fever:
            #Check inj-anti-malarial prescribed for severe malaria
            if check_list('inj_anti_malarial',ped_form['drugs_prescribed']):
                ped_form['pi_fever_mgmt'] = mgmt_good
            else:
                ped_form['pi_fever_mgmt'] = mgmt_bad
        elif ped_form['test_malaria_pos'] and not severe_fever:
            #Check anti-malarial prescribed for non-severe malaria
            if check_list('anti_malarial',ped_form['drug_prescribed']):
                ped_form['pi_fever_mgmt'] = mgmt_good
            else:
                ped_form['pi_fever_mgmt'] = mgmt_bad
        elif ped_form['test_malaria_neg'] and severe_fever:
            #Check inj-anti-biotic prescribed for severe fever that isn't malaria
            if check_list('inj_anti_biotic',ped_form['drug_prescribed']):
                ped_form['pi_fever_mgmt'] = mgmt_good
            else:
                ped_form['pi_fever_mgmt'] = mgmt_bad
        elif ped_form['test_malaria_neg'] and not severe_fever:
            #Check anti-biotic prescribed for not severe fevere that isn't malaria
            if check_list('anti_biotic',ped_form['drug_prescribed']):
                ped_form['pi_fever_mgmt'] = mgmt_good
            else:
                ped_form['pi_fever_mgmt'] = mgmt_bad
        else:
            ped_form['pi_fever_mgmt'] = mgmt_bad
    else:
        ped_form['pi_fever_mgmt'] = mgmt_na
    
    #----------------------------------------
    #7. Diarrhea managed appropriately
    if ped_form['assess_diarrhea']:
        
        #Classify types of diarrhea
        severe_diarrhea = ped_form['severe_dehydration'] or ped_form['sev_diarrhea_two_weeks']
        mod_diarrhea = not severe_diarrhea and \
                     ped_form['moderate_dehydration'] or ped_form['mod_diarrhea_two_weeks']
        nasty_stool = ped_form['blood_in_stool'] or ped_form['pus_in_stool']
        
        if severe_diarrhea and nasty_stool:
            #Check sev_diarrhea AND anti-biotics prescribed
            if check_list('sev_diarrhea',ped_form['drug_prescribed']) and \
               check_list('anti_biotic',ped_form['drug_prescribed']):
                ped_form['pi_diarrhea_mgmt'] = mgmt_good
            else:
                ped_form['pi_diarrhea_mgmt'] = mgmt_bad
        elif severe_diarrhea and not nasty_stool:
            #Check sev_diarrhea prescribed
            if check_list('sev_diarrhea',ped_form['drug_prescribed']):
                ped_form['pi_diarrhea_mgmt'] = mgmt_good
            else:
                ped_form['pi_diarrhea_mgmt'] = mgmt_bad
        elif mod_diarrhea and nasty_stool:
            #Check mod_diarrhea AND anti-biotics prescribed
            if check_list('mod_diarrhea',ped_form['drug_prescribed']) and \
               check_list('anti_biotic',ped_form['drug_prescribed']):
                ped_form['pi_diarrhea_mgmt'] = mgmt_good
            else:
                ped_form['pi_diarrhea_mgmt'] = mgmt_bad
        elif mod_diarrhea and not nasty_stool:
            #Check mod_diarrhea prescribed
            if check_list('mod_diarrhea',ped_form['drug_prescribed']):
                ped_form['pi_diarrhea_mgmt'] = mgmt_good
            else:
                ped_form['pi_diarrhea_mgmt'] = mgmt_bad
        #Else is mild case - dont want to inadvertantly classify mild diarrhea as bad mgmt
        else:
            ped_form['pi_diarrhea_mgmt'] = mgmt_na
    else:
        ped_form['pi_diarrhea_mgmt'] = mgmt_na
        
    
    #----------------------------------------
    #8. RTI managed appropriately 
    if ped_form['assess_cough']:
        
        if ped_form['assess_fever']:
            #Check anti_biotic prescribed
            if check_list('anti_biotic',ped_form['drug_prescribed']):
                ped_form['pi_rti_mgmt'] = mgmt_good
            else:
                ped_form['pi_rti_mgmt'] = mgmt_bad
        else:
            ped_form['pi_rti_mgmt'] = mgmt_na
            
        #Upgrade to injectable anti-biotic if rti severe
        if ped_form['stridor'] or ped_form['indrawing']:
            if check_list('inj_anti_biotic',ped_form['drug_prescribed']):
                ped_form['pi_rti_mgmt'] = mgmt_good
            else:
                ped_form['pi_rti_mgmt'] = mgmt_bad
        
    else:
        ped_form['pi_rti_mgmt'] = mgmt_na
        
    
    #-------------------------------------------
    #9. Hb done if pallor detected 
    if ped_form['sev_pallor'] or ped_form['mod_pallor']:
        if ped_form['test_hb']:
            ped_form['pi_hb_for_pallor'] = mgmt_good
        else:
            ped_form['pi_hb_for_pallor'] = mgmt_bad
    else:
        ped_form['pi_hb_for_pallor'] = mgmt_na
    
    #-------------------------------------------
    #10. Proportion of patients followed up
    #10a.Proportion of forms with Case Closed or Follow-Up recorded   
    if ped_form['case_closed'] or ped_form['referral'] or ped_form['follow_up_needed']:
        ped_form['pi_case_created'] = mgmt_good
    else:
        ped_form['pi_case_created'] = mgmt_bad
        
    #10b.Verify Case Closed and Outcome given for all forms that are Follow-Up Appointments   
    if ped_form['review_case']:
        if ped_form['case_closed'] and check_list('ped_outcomes',ped_form['case_outcome']):
            ped_form['pi_case_closed'] = mgmt_good
        else:
            ped_form['pi_case_closed'] = mgmt_bad
    else:
        ped_form['pi_case_closed'] = mgmt_na
        
    #11.  Drugs dispensed appropriately
    if ped_form['prescription_dispensed']: 
        ped_form['pi_drugs'] = mgmt_good
    elif ped_form['prescription_not_dispensed']:
        ped_form['pi_drugs'] = mgmt_bad
    else:
        ped_form['pi_drugs'] = mgmt_na
        
    return

#------------------------------------------------------------------------
#************************************************************************
#Prego Clinic Performance Indicators
#------------------------------------------------------------------------

def add_prego_pi_to_form(prego_form, [sick_prego_form]):#TODO - how add optional function input?
    '''Adds Pregnancy Clinic Performance Indicators to dictionary created from each
    visit on a pregnancy form.  Note: this treats each single pregnancy visit as a
    single instance, rather than the form as a whole.  If any danger signs are present
    a sick pregnancy form is linked to the same visit.  Pass in form dictionary'''

    (mgmt_na, mgmt_bad, mgmt_good) = (0,1,2)   
    #-----------------------------------
    #1. Pre-eclampsia screening and management
    #1a.Proportion of routine visits with Blood Pressure and Urinalysis results
    if prego_form['blood_pressure'] and prego_form['urinalysis']:
        prego_form['pi_preeclamp_screen'] = mgmt_good
    else:
        prego_form['pi_preeclamp_screen'] = mgmt_bad
        
    #1b.Proportion of (1a) above with abnormal results or Oedema who are 
    #prescribed with Antihypertensives and Referred. 
    
    #Treat bp in as a string.  Extract values
    blood_press = prego_form['blood_pressure'].split()
    bp_systolic, bp_diastolic = int(blood_press[0]), int(blood_press[1])
    
    #Find abnormal pre-eclampsia
    abnormal_bp = bp_systolic >= 140 or bp_diastolic >= 90
    abnormal_preeclamp = abnormal_bp and prego_form['proteinuria'] and prego_ga > 20

    #Assess treatment methods
    if abnormal_preeclamp or prego_form['danger_oedema']:
        if prego_form['referral'] and \
           check_list('anti_hypertensive', prego_form['drugs_prescribed']):
            prego_form['pi_preeclamp_mgmt'] = mgmt_good
        else:
            prego_form['pi_preeclamp_mgmt'] = mgmt_bad
    else:
        prego_form['pi_preeclamp_mgmt'] = mgmt_na

    #2. Danger signs followed up
    #Assess if sick pregnancy form needs to be filled out
    prego_danger_signs = retrieve_list('prego_danger_signs')
    for sign in prego_form[prego_danger_signs]:
        if prego_form[sign] == 'yes': danger_sign_present = 'TRUE'
    breech_presentation = prego_form['breech_presentation'] and \
                        (prego_form['ga_age'] > 27)
    no_fetal_hr = prego_form['fetal_heart_rate'] == 0
    
    #Assess if sick pregnancy form filled out if needed to
    #TODO - lookup function to get data from other form...
    if danger_sign_present or breech_presentation or no_fetal_hr:
        #ASSUME sick pregnancy form filled out for visit that needs one
        #and is recorded in prego_form dictionary for given visit
        if prego_form['sick_prego_date']:
            prego_form['pi_sick_prego'] = mgmt_good
        else:
            prego_form['pi_sick_prego'] = mgmt_bad
    else:
        prego_form['pi_sick_prego'] = mgmt_na

    #----------------------------------
    #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
    clinical_exam_done = prego_form['fundal_height'] and prego_form['fetal_heart_rate'] and \
                       (prego_form['breech_presentation'] or prego_form['cephalic_presentatino'])
    if clinical_exam_done:
        prego_form['pi_clinical_exam'] = mgmt_good
    else:
        prego_form['pi_clinical_exam'] = mgmt_bad

    #----------------------------------
    #4. HIV Testing: Proportion of all pregnant women seen with HIV test done
    if prego_form['hiv_test_pr'] or prego_form['hiv_test_r'] or prego_form['hiv_test_nr']:
        prego_form['pi_hiv_test'] = mgmt_good
    else:
        prego_form['pi_hiv_test'] = mgmt_bad

    #----------------------------------
    #5. NVP: Proportion of all women testing HIV-positive provided a dose of NVP on the 1st visit
    
    #Need HIV+ Info for the next few...
    visit_number = prego_form['visit_number']
    while visit_number > 0 and not hiv_positive:
        hiv_positive = lookup(prego_form['hiv_test_r'],prego_form['visit_number'] == visit_number)
    #Catch last case = first visit, previously diagnosed reactive
    hiv_positive = hiv_positive or prego_form['hiv_test_pr']
    
    #Now for #5:
    if prego_form['visit_number'] == 1 and hiv_positive:
        if prego_form['pmtct_nvp']:
            prego_form['pi_nvp_given'] = mgmt_good
        else:
            prego_form['pi_nvp_given'] = mgmt_bad
    else:
        prego_form['pi_nvp_given'] = mgmt_na

    #-----------------------------------
    #6. AZT: a.Proportion of all women testing HIV-positive provided AZT on ANY visit
    #        b.Proportion of all women provided AZT who received it at their last visit
            
    #Assess azt mgmt for single visit
    if prego_form['visit_number'] == 1 and hiv_positive:
        if prego_form['pmtct_azt']:
            prego_form['pi_azt_given'] = mgmt_good
        else:
            prego_form['pi_azt_given'] = mgmt_bad           
        prego_form['pi_azt_last_visit'] = mgmt_na
        
    elif prego_form['visit_number'] > 1 and hiv_positive:
        #Cycle through previous visits to see if AZT given
        visit_number = prego_form['visit_number']-1
        azt_last_visit = lookup(prego_form['pmtct_azt'],prego_form['visit_number'] == visit_number)
        while visit_number > 0 and not azt_prev_given:
            #TODO - is this going to work?
            azt_prev_given = lookup(prego_form['pmtct_azt'],prego_form['visit_number'] == visit_number)
            visit_number -= 1
            
        #Assess if any AZT given:
        if  prego_form['pmtct_azt'] or azt_prev_given:
            prego_form['pi_azt_given'] = mgmt_good
        else:
            prego_form['pi_azt_given'] = mgmt_bad
        
        #Assess if AZT given on last visit
        if  prego_form['pmtct_azt'] and azt_last_visit:
            prego_form['pi_azt_last_visit'] = mgmt_good    
        else:
            prego_form['pi_azt_Last_visit'] = mgmt_bad
        
    else:
        prego_form['pi_azt_given'] = mgmt_na
        prego_form['pi_azt_last_visit'] = mgmt_na

    #-----------------------------------
    #7a.Proportion of all pregnant women seen with RPR test given on the 1st visit
    if prego_form['visit_number'] == 1:
        if prego_form['rpr_r'] or prego_form['rpr_nr']:
            prego_form['pi_rpr_given'] = mgmt_good
        else:
            prego_form['pi_rpr_given'] = mgmt_bad
    else:
        prego_form['pi_rpr_given'] = mgmt_na

    #7b.Proportion of all women testing RPR-positive provided a dose of penicillin
    if prego_form['rpr_r']:
        if prego_form['penicillin']:
            prego_form['pi_rpr_penicillin'] = mgmt_good
        else:
            prego_form['pi_rpr_penicillin'] = mgmt_bad
    else:
        prego_form['pi_rpr_penicillin'] = mgmt_na

    #7c. Proportion of all women testing RPR-positive whose partners are given penicillin 
    #(does not include first visit that women discovers she is RPR positive)
    if prego_form['rpr_r']:
        visit_number = prego_form['visit_number']-1
        realized_rpr_r = lookup(prego_form['rpr_r'],prego_form['visit_number'] == visit_number)
        #Hopeful case:
        if prego_form['partner_penicillin']:
            prego_form['pi_rpr_prtnr_penicillin'] = mgmt_good
        #Don't punish if just realized rpr_r
        elif realized_rpr_r and not prego_form['partner_penicillin']:
            prego_form['pi_rpr_prtnr_penicillin'] = mgmt_na
        else:
            prego_form['pi_rpr_prtnr_penicillin'] = mgmt_bad
    else:
        prego_form['pi_rpr_prtnr_penicillin'] = mgmt_na

    #--------------------------------------------
    #8. Fansidar:  Proportion of all pregnant women seen provided three doses of fansidar
    #(measured after expected close of pregnancy)  TODO - not sure of best way to do this...
    #THIS ONE NEEDS TO BE DONE AT REPORT COMPILE TIME (?!)

    #9.  Drugs dispensed appropriately
    if prego_form['prescription_dispensed']: 
        prego_form['pi_drugs'] = mgmt_good
    elif prego_form['prescription_not_dispensed']:
        prego_form['pi_drugs'] = mgmt_bad
    else:
        prego_form['pi_drugs'] = mgmt_na
        
    return

#-------------------------------------------------------------------------------
#*******************************************************************************
#Adult Clinic Performance Indicators
#-------------------------------------------------------------------------------
def add_adult_pi_to_form(adult_form):
    '''Adds Adult Clinic Performance Indicators to dictionary created from each
    General Visit form.  Pass in form data.'''
    
    (mgmt_na, mgmt_bad, mgmt_good) = (0,1,2)
    
    #-----------------------------------
    #1. Blood Pressure recorded
    if adult_form['blood pressure']:
        adult_form['pi_bp_recorded'] = mgmt_good
    else:
        adult_form['pi_bp_recorded'] = mgmt_bad
    
    #-----------------------------------
    #2. TB managed appropriately
    if adult_form[assess_cough] and adult_form[over_two_weeks]:
        if adult_form['test_sputum']:
            adult_form['pi_tb_mgmt'] = mgmt_good
        else:
            adult_form['pi_tb_mgmt'] = mgmt_bad
    else:
        adult_form['pi_tb_mgmt'] = mgmt_na
    
    #-----------------------------------
    #3. Malaria managed appropriately
    if adult_form['danger_sign_fever']:
        if adult_form['test_malaria_pos']:
            #Check anti-malarial prescribed for malaria
            if check_list('anti_malarial',adult_form['drugs_prescribed']):
                adult_form['pi_fever_mgmt'] = mgmt_good
            else:
                adult_form['pi_fever_mgmt'] = mgmt_bad
        elif adult_form['test_malaria_neg']:
            #Check anti-biotic prescribed for non-malaria
            if check_list('anti_biotic',adult_form['drug_prescribed']):
                adult_form['pi_fever_mgmt'] = mgmt_good
            else:
                adult_form['pi_fever_mgmt'] = mgmt_bad
        #If fever indicated, should have done one of the above
        else:
            adult_form['pi_fever_mgmt'] = mgmt_bad
    else:
        adult_form['pi_fever_mgmt'] = mgmt_na
    
    #----------------------------------------------
    #4. HIV test ordered appropriately
    # Check if HIV symptoms present
    hiv_symptoms = retrieve_list('adult_hiv_symptoms')
    for sign in adult_form[hiv_symptoms]:
        if adult_form[sign]: hiv_symptom_present = 'TRUE'
    hiv_symptom_present = hiv_symptom_present or adult_form['abnormal_lymph_nodes']

    # Check to see if test ordered
    if adult_form['hiv_result_nd'] and hiv_symptom_present:
        if adult_form['hiv_rapid_test']:
            adult_form['pi_hiv_test'] = mgmt_good
        else:
            adult_form['pi_hiv_test'] = mgmt_bad
    else:
        adult_form['pi_hiv_test'] = mgmt_na
        
    #5. Drugs dispensed appropriately
    if adult_form['prescription_dispensed']: 
        adult_form['pi_drugs'] = mgmt_good
    elif adult_form['prescription_not_dispensed']:
        adult_form['pi_drugs'] = mgmt_bad
    else:
        adult_form['pi_drugs'] = mgmt_na
        
        
    return

#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------

#CHW Performance Indicators

#-----------------------------------
#1. Follow Up Follow Through
#(# Referrals from Follow Up Cases + # Follow Up Cases given Outcomes) / Total # of Follow Ups

#-----------------------------------
#2. Referrals that Visit Clinic
#Proportion of new Referrals to go to the Clinic


def check_list(master_list_name,list_in):
    '''See if list passed in is a subset of another list referenced from the 
    Master List Name.
    Categories: (inj_)anti_biotics,(inj_)anti_malarial,(inj_)anti_hypertensive,
    mod_rehydration,sev_rehydration, ped_hiv_symptoms, adult_hiv_symptoms,
    ped_outcomes, prego_danger_signs'''
    
    master_list = eval(master_list_name)        #Expect exact string
    master_set = set(master_list)               #Is this better than looping?
    list_to_check = set(list_in)                #List of strings to check
    return list_to_check.issubset(master_list)

def retrieve_list(list_name_in):
    '''Enter string name of list to retrieve, sends back list from the following:
    Categories: (inj_)anti_biotics,(inj_)anti_malarial,(inj_)anti_hypertensive,
    mod_rehydration,sev_rehydration, ped_hiv_symptoms, adult_hiv_symptoms,
    ped_outcomes, prego_danger_signs'''
    
    list_to_retrieve = eval(list_name_in)
    return list_to_retrive

ped_hiv_symptoms = ['indrawing',\
                    'fast_breathing',\
                    'sev_diarrhea_two_weeks',\
                    'mod_diarrhea_two_weeks',\
                    'mild_diarrhea_two_weeks',\
                    'sev_fever_one_week',\
                    'ear_pus_two_weeks',\
                    'sev_low_weight',\
                    'mod_low_weight']

adult_hiv_symptoms = ['fast_breathing',\
                      'cough_two_weeks',\
                      'penile_discharge',\
                      'sig_weight_loss']

ped_outcomes = ['dehydration_treated',\
                'malnutrition_treated',\
                'pneumonia_treated',\
                'meningitis_treated',\
                'malaria_treated',\
                'other_infection_treated',\
                'death',\
                'unknown']

prego_danger_signs = ['vaginal_bleeding',\
                      'leaking_fluid',\
                      'contractions',\
                      'pain_urination',\
                      'pelvic_pressure',\
                      'oedema']

#TODO: Need to see if injectables are subsets of normal meds, or normal sets
#shouldn't include injectables
anti_biotics = ['amoxycillin',\
                'benzathine',\
                'benzyl_penicillin',\
                'cefotaxime'\
                'ceftriaxone'\
                'cephalexin',\
                'chloramphenicol',\
                'ciprofloxacin',\
                'cloxacillin',\
                'co_trimoxazole',\
                'doxycycline,'\
                'erythromycine',\
                'gentamycin,'\
                'metronidazole',\
                'nalidixic_acid',\
                'nitrofurantoin',\
                'phenoxymethyl_penicillin',\
                'procaine_penicillin']

inj_anti_biotics = ['benzathine',\
                    'benzyl_penicillin',\
                    'cefotaxime'\
                    'ceftriaxone'\
                    'chloramphenicol',\
                    'gentamycin,'\
                    'metronidazole']

anti_malarial = ['co_artem',\
                 'quinine']

inj_anti_malarial = ['quinine']

anti_hypertensive = ['atenelol',\
                     'co_amiloride',\
                     'enalapril',\
                     'frusemide'\
                     'hydralazine',\
                     'magnesium_sulphate',\
                     'methyldopa',\
                     'nifedipine',\
                     'nifedipine_sublingual',\
                     'propranolol']

inj_anti_hypertensive = ['frusemide'\
                         'hydralazine',\
                         'magnesium_sulphate',\]

mod_rehydration = ['ors']

sev_rehydration = ['ringers_lactate']
    

