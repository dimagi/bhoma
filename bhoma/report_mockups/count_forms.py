#Code to Run when Report Created that accumulates scores and displays

def pi_aggregate(variable_to_count,start_date,end_date):
    '''Aggregates Performance Indicator Data.  Pass in key to count and 
    date range.  Cycles through all forms from start date to end date.  Returns
    proportion of good to good plus bad cases (ignores na cases)'''
    
    #Find first form within start date
    #Find last form within end date
    #For each form, get value from key to aggregate
    #Keep track of number of good, bad or na
    #Return proportion, or need need to pass out numbers for good, bad and na?
    
#Agregate Under-Five Clinic Performance Indicators
def aggregate_ped_pi(start_date, end_date):
    '''Get values for Ped Report into Dictionary.  Pass in report 
    start and stop dates.'''
        
    #1. Proportion Height and Weight Recorded on each form 
    ped_report['pi_height_weight'] = pi_aggregate(ped_form['pi_height_weight'], start_date, end_date)
    
    #2. Temperature, respiratory rate, and heart rate recorded
    ped_report['pi_vitals'] = pi_aggregate(ped_form['pi_vitals'], start_date, end_date)

    #3. HIV test ordered appropriately
    ped_report['pi_hiv_test'] = pi_aggregate(ped_form['pi_hiv_test'], start_date, end_date)

    #4. Weight for age assessed correctly
    ped_report['pi_wfa_correct'] = pi_aggregate(ped_form['pi_wfa_correct'], start_date, end_date)
    
    #5. Low weight for age managed appropriately
    ped_report['pi_lwfa_mgmt'] = pi_aggregate(ped_form['pi_lwfa_mgmt'], start_date, end_date)

    #6. Fever managed appropriately
    ped_report['pi_fever_mgmt'] = pi_aggregate(ped_form['pi_fever_mgmt'], start_date, end_date)
    
    #7. Diarrhea managed appropriately
    ped_report['pi_rti_mgmt'] = pi_aggregate(ped_form['pi_rti_mgmt'], start_date, end_date)

    #8. RTI managed appropriately
    ped_report['pi_diarrhea_mgmt'] = pi_aggregate(ped_form['pi_diarrhea_mgmt'], start_date, end_date)

    #9. Hb done if pallor detected
    ped_report['pi_hb_for_pallor'] = pi_aggregate(ped_form['pi_hb_for_pallor'], start_date, end_date)

    #10. Proportion of patients followed up
    ped_report['pi_case_created'] = pi_aggregate(ped_form['pi_case_created'], start_date, end_date)
    ped_report['pi_case_closed'] = pi_aggregate(ped_form['pi_case_closed'], start_date, end_date)
    
    #11.  Drugs dispensed appropriately
    ped_report['pi_drugs'] = pi_aggregate(ped_form['pi_drugs'], start_date, end_date)
    
    return
    
#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#Agregate Pregnant Clinic Performance Indicators
def aggregate_prego_pi(start_date, end_date):
    '''Get values for Pregnant Report into Dictionary.  Pass in report 
    start and stop dates.'''
        
    #1. Pre-eclampsia screening and management
    prego_report['pi_preeclamp_screen'] = pi_aggregate(prego_form['pi_preeclamp_screen'], start_date, end_date)
    prego_report['pi_preeclamp_mgmt'] = pi_aggregate(prego_form['pi_preeclamp_mgmt'], start_date, end_date)

    #2. Danger signs followed up
    prego_report['pi_sick_prego'] = pi_aggregate(prego_form['pi_sick_prego'], start_date, end_date)

    #3. Clinical Exam
    prego_report['pi_clinical_exam'] = pi_aggregate(prego_form['pi_clinical_exam'], start_date, end_date)

    #4. HIV Testing:
    prego_report['pi_hiv_test'] = pi_aggregate(prego_form['pi_hiv_test'], start_date, end_date)

    #5. NVP
    prego_report['pi_nvp_given'] = pi_aggregate(prego_form['pi_nvp_given'], start_date, end_date)
    
    #6. AZT
    prego_report['pi_azt_given'] = pi_aggregate(prego_form['pi_azt_given'], start_date, end_date)
    prego_report['pi_azt_last_visit'] = pi_aggregate(prego_form['pi_azt_last_visit'], start_date, end_date)
    
    #7. RPR
    prego_report['pi_rpr_given'] = pi_aggregate(prego_form['pi_rpr_given'], start_date, end_date)
    prego_report['pi_rpr_penicillin'] = pi_aggregate(prego_form['pi_rpr_penicillin'], start_date, end_date)
    prego_report['pi_rpr_prtnr_penicillin'] \
                = pi_aggregate(prego_form['pi_rpr_prtnr_penicillin'], start_date, end_date)

    #8. Fansidar
    #Cycle through each pregnancy form.  For those where end date of report 
    #generation is after Estimated Date of Delivery, count Fansidar doses
    
    #Find first form within start date
    #Find last form within end date
    #For each form, see if end date is after EDD
    #If so, count fansidar doses for each routine visit
    #If 3 or more, mgmt is good, increment good mgmt count.
    #If not, increment bad mgmt count
    
    prego_report['pi_fansidar_mgmt'] = \
                num_fansidar_mgmt_good / (num_fansidar_mgmt_good + num_fansidar_mgmt_bad)
    
    #9.  Drugs dispensed appropriately
    prego_report['pi_drugs'] = pi_aggregate(prego_form['pi_drugs'], start_date, end_date)
    
    return

#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#Agregate Pregnant Clinic Performance Indicators
def aggregate_adult_pi(start_date, end_date):
    '''Get values for Adult Report into Dictionary.  Pass in report 
    start and stop dates.'''
    
    #1. Blood Pressure
    adult_report['pi_bp_recorded'] = pi_aggregate(adult_form['pi_bp_recorded'], start_date, end_date)

    #2. TB managed appropriately
    adult_report['pi_tb_mgmt'] = pi_aggregate(adult_form['pi_tb_mgmt'], start_date, end_date)
    
    #3. Malaria managed appropriately
    adult_report['pi_fever_mgmt'] = pi_aggregate(adult_form['pi_fever_mgmt'], start_date, end_date)

    #4. HIV test ordered appropriately
    adult_report['pi_hiv_test'] = pi_aggregate(adult_form['pi_hiv_test'], start_date, end_date)

    #5.  Drugs dispensed appropriately
    adult_report['pi_drugs'] = pi_aggregate(adult_form['pi_drugs'], start_date, end_date)
    
    return

#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
#CHW Performance Indicator Report
def chw_pi(start_date, end_date):
    '''Create CHW PI report.  Pass in report start and stop dates.'''

#1. Follow Up Follow Through
#(# Referrals from Follow Up Cases + # Follow Up Cases given Outcomes) / Total # of Follow Ups

#2. Referrals that Visit Clinic
#Proportion of new Referrals to go to the Clinic

#-------------------------------------------------------------------------------
#*******************************************************************************
#-------------------------------------------------------------------------------
if __name__ == '__main__' :
    
    #Get user input for which type of report to generate
    #Get user input for start date
    #Get user input for end date
    
    if make_adult_report:
        aggregate_adult_pi(start_date, end_date)
        #Display adult report from dictionary values
    elif make_adult_report:
        aggregate_prego_pi(start_date, end_date)
        #Display adult report from dictionary values
    elif make_ped_report:
        aggregate_adult_pi(start_date, end_date)
        #Display adult report from dictionary values
    elif make_chw_report:
        chw_pi(start_date, end_date)
        #Display adult report from dictionary values
        
    return
