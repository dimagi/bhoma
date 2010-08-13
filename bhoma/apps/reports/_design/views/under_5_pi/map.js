function(doc) {
    /* 
     * Under-five Performance Indicator Report
     */
    
    // these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
	
	NAMESPACE = "http://cidrz.org/bhoma/underfive"
    
    
    if (xform_matches(doc, NAMESPACE))
    {   
        report_values = [];
        /* this field keeps track of total forms */
        report_values.push(new reportValue(1,1,"total",true));
        
        new_case = doc.encounter_type == "new_case" ? 1 : 0;
        report_values.push(new reportValue(new_case, 1, "new_case", true));
        
        followup_case = doc.encounter_type == "new_case" ? 0 : 1;
        report_values.push(new reportValue(followup_case, 1, "followup_case", true));
        
        enc_date = get_encounter_date(doc);     
        
        /* 
		#-----------------------------------
		# 1. Height and Weight recorded 
		*/
		
        /* TODO: Figure out if last visit within a month */
        last_visit_within_a_month = function(doc) {
            return true;
        };
		vitals = doc.vitals;
        ht_wt_rec_num = Boolean((new_case || !last_visit_within_a_month(doc)) && vitals["height"] && vitals["weight"]) ? 1 : 0;
		report_values.push(new reportValue(ht_wt_rec_num, 1, "Height and weight recorded"));
        
        /* 
		#-----------------------------------
		# 2. Temperature, respiratory rate, and heart rate recorded 
		*/
		
        vitals_rec_num = Boolean(vitals["temp"] && vitals["resp_rate"] && vitals["heart_rate"]) ? 1 : 0;
		report_values.push(new reportValue(vitals_rec_num, 1, "Vitals recorded"));
		
        /*
		#-----------------------------------
		# 3. HIV test ordered appropriately
		*/
	    assessment = doc.assessment;
	    investigations = doc.investigations;
		
		var shows_hiv_symptoms = function(doc) {
	       return (exists(assessment["resp"],"sev_indrawing") ||
				   exists(assessment["resp"],"mod_fast_breath") ||
	               exists(assessment["diarrhea"],"sev_two_weeks") ||
	               exists(assessment["diarrhea"], "mod_two_weeks") ||
	               exists(assessment["diarrhea"], "mild_two_weeks") ||
	               exists(assessment["fever"], "sev_one_week") ||
				   exists(assessment["ear"], "mild_pus") ||
				   exists(assessment["malnutrition"], "sev_sd") ||
				   exists(assessment["malnutrition"], "mod_sd"));
	               
	    }
	    hiv = doc.hiv;
	    hiv_unknown = hiv["status"] == "unk";
		hiv_exposed = hiv["status"] == "exp";
		hiv_not_exposed = hiv["status"] == "unexp";
	    if ((hiv_unknown || hiv_exposed) || (hiv_not_exposed && shows_hiv_symptoms(doc))) {
	       should_test_hiv = 1;
	       did_test_hiv = (exists(investigations["categories"], "hiv_rapid") || exists(investigations["categories"], "pcr")) ? 1 : 0;
	    } else {
	       should_test_hiv = 0;
           did_test_hiv = 0;
	    }
	    report_values.push(new reportValue(did_test_hiv, should_test_hiv, "HIV Test Ordered"));
	    
	    /*	    
		#-----------------------------------------------
	    #4. Weight for age assessed correctly
		*/
		/***************
	    #TODO
	    # Get Z-score for ped
	    #for L != 0, Z = (((X/M)^L)-1)/(L*S)
	    #for L == 0, Z = ln(x/m)/x
	    
	    
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
	    
	    report_values.push(new reportValue(1, 1, "Weight for age assessed")); 
        
        /* 
	    #--------------------------------------
	    #5. Low weight for age managed appropriately
		*/
		
		if (exists(assessment["malnutrition"],"sev_sd") || exists(assessment["malnutrition"],"mod_sd")) {
	       lwfa_managed_denom = 1;
		   resolution_case_closed = doc.resolution == "closed" ? 1 : 0;
	       lwfa_managed_num = !resolution_case_closed;
	    } else {
	       lwfa_managed_denom = 0;
	       lwfa_managed_num = 0;
	    }
		report_values.push(new reportValue(lwfa_managed_num, lwfa_managed_denom, "Low weight managed"));      
	    
		/*    
	    #-----------------------------------------
	    #6. Fever managed appropriately
	    */
	    drugs_prescribed = doc.drugs_prescribed;
	    if (exists(assessment["categories"], "fever")) {
	       fever_managed_denom = 1;
	       /* If malaria test positive, check for anti_malarial*/
	       if (exists(investigations["rdt_mps"], "p") && drugs_prescribed) {
	       		/* check if severe */
	       		if (exists(assessment["fever"],"sev_one_week") || exists(assessment["fever"],"sev_stiff_neck")) {
       				fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial","injectable");	
       			} else {
       			    fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial");	
       			}
	       /* If malaria test negative, check for antibiotic*/
	       } else if (exists(investigations["rdt_mps"], "n") && drugs_prescribed) {
	       		/* check if severe */
	       		if (exists(assessment["fever"],"sev_one_week") || exists(assessment["fever"],"sev_stiff_neck")) {
       				fever_managed_num = check_drug_type(drugs_prescribed,"antibiotic","injectable");	
       			} else {
       				fever_managed_num = check_drug_type(drugs_prescribed,"antibiotic");			       		
	       		}
	       } else {
	       		fever_managed_num = 0;
	       }
	    } else {
	       fever_managed_denom = 0;
           fever_managed_num = 0;
	    }
	    report_values.push(new reportValue(fever_managed_num, fever_managed_denom, "Fever Managed")); 
        
	    /*
	    #----------------------------------------
	    #7. Diarrhea managed appropriately
	    */
	    drugs = doc.drugs;
	    
		if (exists(assessment["categories"],"diarrhea")) {
	       diarrhea_managed_denom = 1;
	       /* Check dehydration level */
	       if (exists(assessment["diarrhea"],"sev_dehyd") && drugs_prescribed) {
	       		if (exists(investigations["stool"],"blood") || exists(investigations["stool"],"pus")) {
	       			diarrhea_managed_num = check_drug_type(drugs_prescribed,"antibiotic") && check_drug_name(drugs_prescribed,"ringers_lactate");
	       		} else {
	       			diarrhea_managed_num = check_drug_name(drugs_prescribed,"ringers_lactate");;
	       		}
	       } else if (exists(assessment["diarrhea"],"mod_dehyd") && drugs_prescribed) {
	       		if (exists(investigations["stool"],"blood") || exists(investigations["stool"],"pus")) {
	       			diarrhea_managed_num = check_drug_type(drugs_prescribed,"antibiotic") && check_drug_name(drugs_prescribed,"ors");;
	       		} else {
	       			diarrhea_managed_num = check_drug_name(drugs_prescribed,"ors");;
	       		}
	       } else {
	       		diarrhea_managed_num = 0;
	       }
	    } else {
	       diarrhea_managed_denom = 0;
           diarrhea_managed_num = 0;
	    }
	    report_values.push(new reportValue(diarrhea_managed_num, diarrhea_managed_denom, "Diarrhea Managed"));    
        
	    /*
	    #----------------------------------------
	    #8. RTI managed appropriately 
		*/
		if (exists(assessment["categories"],"resp") && exists(assessment["categories"],"fever")) {
	       rti_managed_denom = 1;
	       /* If resp and fever ticked in assessment, check for anitbiotic (injectable for severe fever)) */
	       if (drugs_prescribed && (exists(assessment["fever"],"sev_one_week") || exists(assessment["fever"],"sev_stiff_neck"))) {
	       		rti_managed_num = check_drug_type(drugs_prescribed,"antibiotic","injectable");
	       } else if (drugs_prescribed){
	       		rti_managed_num = check_drug_type(drugs_prescribed,"antibiotic");
	       } else {
	       		rti_managed_num = 0;
	       }
	    } else {
	       rti_managed_denom = 0;
           rti_managed_num = 0;
	    }
	    report_values.push(new reportValue(rti_managed_num, rti_managed_denom, "RTI Managed")); 
		
	    /*
	    #-------------------------------------------
	    #9. Hb done if pallor detected
		*/
		
	    if (exists(doc.general_exam,"severe_pallor") || exists(doc.general_exam,"mod_pallor")) {
	       hb_if_pallor_denom = 1;
	       hb_if_pallor_num = exists(investigations["categories"], "hb_plat") ? 1 : 0;
	    } else {
	       hb_if_pallor_denom = 0;
	       hb_if_pallor_num = 0;
	    }
		report_values.push(new reportValue(hb_if_pallor_num,hb_if_pallor_denom,"Hb done if pallor"));
        
	    /*
	    #-------------------------------------------
	    #10. Proportion of patients followed up
	    #10a.Proportion of forms with Case Closed or Follow-Up recorded   
		*/
		
		followup_recorded_num = Boolean(doc.resolution) ? 1 : 0;
		report_values.push(new reportValue(followup_recorded_num, 1, "Patients followed up"));
        
	    /*
	    #10b.Verify Case Closed and Outcome given for all forms that are Follow-Up Appointments  
		*/
		
	    if (!new_case) {
	       outcome_recorded_denom = 1;
	       outcome_recorded_num = Boolean(exists(doc.resolution,"closed") && doc.outcome) ? 1 : 0;
	    } else {
	       outcome_recorded_denom = 0;
	       outcome_recorded_num = 0;
	    }
		report_values.push(new reportValue(outcome_recorded_num, outcome_recorded_denom, "Review cases managed"));
		
	    /*
	    #11.  Drugs dispensed appropriately
		*/

		drugs = doc.drugs;
		if (exists(drugs["dispensed_as_prescribed"])) {
	       drugs_appropriate_denom = 1;
	       drugs_appropriate_num = exists(drugs["dispensed_as_prescribed"], "y") ? 1 : 0;
	    } else {
	       drugs_appropriate_denom = 0;
	       drugs_appropriate_num = 0;
	    }
		report_values.push(new reportValue(drugs_appropriate_num, drugs_appropriate_denom, "Drugs dispensed appropriately")); 
        
	    emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 
    } 
}