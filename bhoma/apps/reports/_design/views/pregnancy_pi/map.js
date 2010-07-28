function(doc) {
    /* Under-five Performance Indicator Report
     */
    
    NAMESPACE = "http://cidrz.org/bhoma/pregnancy"
    
    
    if (doc["#doc_type"] == "XForm" && doc["@xmlns"] == NAMESPACE)
    {   
        values = {};
        /* this field keeps track of total forms */
        values["total"] = true;
        new_case = doc.encounter_type == "new_case";
        values["followup_case"] = !new_case;
        enc_date = new Date(Date.parse(doc.encounter_date));
        
        /* TODO
        
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
	        
	    */
        
        emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), enc_date.getDate()], values); 
    } 
}