function(doc) {
    /* Under-five Performance Indicator Report
     */
    
    NAMESPACE = "http://cidrz.org/bhoma/underfive"
    
    
    if (doc["#doc_type"] == "XForm" && doc["@xmlns"] == NAMESPACE)
    {   
        values = {};
        new_case = doc.encounter_type == "new_case";
        enc_date = new Date(Date.parse(doc.encounter_date));
        
        vitals = doc.vitals;
        
        /* Height and Weight recorded */
        /* TODO: Figure out if last visit within a month */
        last_visit_within_a_month = function(doc) {
            return true;
        };
        values["ht_wt_rec"] = Boolean((new_case || last_visit_within_a_month(doc)) && vitals.height && vitals.weight);
        log("height weight recorded: " + values["ht_wt_rec"]);
        
        /* Temperature, respiratory rate, and heart rate recorded */
        values["vitals_rec"] = Boolean(vitals["temp"] && vitals["resp_rate"] && vitals["heart_rate"]);
        
        /*
	    3. HIV test ordered appropriately
	    
	    Check for any symptoms with an * to see if at risk for HIV
	    
	    TODO
	    
	    iv_symptoms_present = check_list('ped_hiv_symptoms',ped_form['symptoms'])
	    
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
	
	    */
	    values["hiv_test_ordered"] = true;
	    
	    /*******************
	    
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
	    # for data_row in sn_data_table:
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
	    */
	    
	    values["weight_assessed"] = true;
        
	    
        /* 
	    #--------------------------------------
	    #5. Low weight for age managed appropriately
	    if ped_form['assess_lwfa'] and not ped_form['mild_lwfa']:
	        if ped_form['referral'] or ped_form['follow_up_needed']:
	            ped_form['pi_lwfa_mgmt'] = mgmt_good
	        else:
	            ped_form['pi_lwfa_mgmt'] = mgmt_bad
	    else:
	        ped_form['pi_lwfa_mgmt'] = mgmt_na
	    */
	    
	    values["low_weight_managed"] = true;
         
	    /*    
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
	        
	    */
	    
	    values["fever_managed"] = true;
        
	    
	    /*
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
	        
	    */
	    
	    values["diarrhea_managed"] = true;
        
	    /*
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
	    
	    */ 
	    
	    values["rti_managed"] = true;
        
	    /*
	    
	    #-------------------------------------------
	    #9. Hb done if pallor detected 
	    if ped_form['sev_pallor'] or ped_form['mod_pallor']:
	        if ped_form['test_hb']:
	            ped_form['pi_hb_for_pallor'] = mgmt_good
	        else:
	            ped_form['pi_hb_for_pallor'] = mgmt_bad
	    else:
	        ped_form['pi_hb_for_pallor'] = mgmt_na
	    
	    */
	    
	    values["hb_if_pallor"] = true;
        
	    /*
	    #-------------------------------------------
	    #10. Proportion of patients followed up
	    #10a.Proportion of forms with Case Closed or Follow-Up recorded   
	    if ped_form['case_closed'] or ped_form['referral'] or ped_form['follow_up_needed']:
	        ped_form['pi_case_created'] = mgmt_good
	    else:
	        ped_form['pi_case_created'] = mgmt_bad
	        
	    */
	    
	    values["followup_recorded"] = true;
        
	    /*
	    #10b.Verify Case Closed and Outcome given for all forms that are Follow-Up Appointments   
	    if ped_form['review_case']:
	        if ped_form['case_closed'] and check_list('ped_outcomes',ped_form['case_outcome']):
	            ped_form['pi_case_closed'] = mgmt_good
	        else:
	            ped_form['pi_case_closed'] = mgmt_bad
	    else:
	        ped_form['pi_case_closed'] = mgmt_na
	    
	    */
	    
	    values["followup_case"] = !new_case;
        values["outcome_recorded"] = true;
        
	    /*
	    #11.  Drugs dispensed appropriately
	    if ped_form['prescription_dispensed']: 
	        ped_form['pi_drugs'] = mgmt_good
	    elif ped_form['prescription_not_dispensed']:
	        ped_form['pi_drugs'] = mgmt_bad
	    else:
	        ped_form['pi_drugs'] = mgmt_na
	        
	    */
	    
	    values["drugs_disp_app"] = true;
        
	    emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), enc_date.getDate()], values); 
    } 
}