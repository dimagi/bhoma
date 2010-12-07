function(doc) {
    /* 
     * Paediatric (was Under-five) Performance Indicator Report
     */
    
    // these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
	
	NAMESPACE = "http://cidrz.org/bhoma/underfive"
    
    if (xform_matches(doc, NAMESPACE))
    {   
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        report_values = [];
        /* this field keeps track of total forms */
        report_values.push(new reportValue(1,1,"total",true));
        
        new_case = doc.encounter_type == "new_case" ? 1 : 0;
        report_values.push(new reportValue(new_case, 1, "new_case", true));
        
        followup_case = doc.encounter_type == "new_case" ? 0 : 1;
        report_values.push(new reportValue(followup_case, 1, "followup_case", true));
        
        /* 
		#-----------------------------------
		# 1. Height and Weight recorded 
		*/
		
		vitals = doc.vitals;
		ht_wt_rec_num = Boolean(vitals["height"] && vitals["weight"]) ? 1 : 0;
		report_values.push(new reportValue(ht_wt_rec_num, 1, "Height and weight recorded", false, "Height and Weight under Vitals section recorded."));
        
        /* 
		#-----------------------------------
		# 2. Temperature, respiratory rate, and heart rate recorded 
		*/
		
        vitals_rec_num = Boolean(vitals["temp"] && vitals["resp_rate"] && vitals["heart_rate"]) ? 1 : 0;
		report_values.push(new reportValue(vitals_rec_num, 1, "Vitals recorded", false, "Temperature, Respiratory Rate, and Heart Rate under Vitals section recorded."));
		
        /*
		#-----------------------------------
		# 3. HIV test ordered appropriately
		*/
	    assessment = doc.assessment;
	    investigations = doc.investigations;
		
		var shows_hiv_symptoms = function(doc) {
	       return (exists(doc.phys_exam_detail,"lymph") ||
	       		   exists(doc.phys_exam_detail,"liver_spleen") ||
				   exists(assessment["resp"],"mod_fast_breath") ||
	               exists(assessment["diarrhea"], "mod_two_weeks") ||
	               exists(assessment["fever"], "sev_one_week") ||
				   exists(assessment["malnutrition"], "sev_sd") ||
				   exists(assessment["malnutrition"], "mod_sd") ||
				   exists(doc.secondary_diagnosis_one,"rti_pneumonia") ||
				   exists(doc.secondary_diagnosis_one,"persistent_diarrhea") ||
				   exists(doc.secondary_diagnosis_one,"chronic_ear_infection") ||
				   exists(doc.secondary_diagnosis_two,"very_low_weight") ||
	               exists(doc.diagnosis,"rti_pneumonia") ||
				   exists(doc.diagnosis,"persistent_diarrhea") ||
				   exists(doc.diagnosis,"chronic_ear_infection") ||
				   exists(doc.diagnosis,"very_low_weight"));
	    }
	    hiv = doc.hiv;
		
		hiv_unk_exp = hiv["status"] == "unk" || "exp" || "blank";
		no_hiv_test = hiv["test_result"] == "nd" || "blank";
		non_reactive = hiv["test_result"] != "r";
		no_card = hiv["status"] == "no_card";	
		if ((hiv_unk_exp && no_hiv_test) || ((non_reactive || no_card) && shows_hiv_symptoms(doc))) {
	       should_test_hiv = 1;
	       did_test_hiv = investigations["hiv_rapid"] == "r" || "nr" || "ind";
	    } else {
	       should_test_hiv = 0;
           did_test_hiv = 0;
	    }
	    report_values.push(new reportValue(did_test_hiv, should_test_hiv, "HIV Test Ordered", false, "Proportion of visits with Height and Weight under Vitals section recorded."));
	    
	    /*	    
		#-----------------------------------------------
	    #4. Weight for age assessed correctly
		*/
	    if (doc.age <= 5) {
	    	wfa_assess_denom = 1;
	    	if (doc.zscore_calc_good === true || doc.zscore_calc_good == "true") {
	    		wfa_assess_num = 1;
    		} else {
    			wfa_assess_num = 0;
			}
	    } else {
	    	wfa_assess_num = 0;
	    	wfa_assess_denom = 0;
	    }
	    report_values.push(new reportValue(wfa_assess_num, wfa_assess_denom, "Weight for age assessed", false, "Weight for age standard deviation (Z-score) calculated correctly on patients under 5.")); 
        
        /* 
	    #--------------------------------------
	    #5. Low weight for age managed appropriately
		*/
		
		if ((doc.age <= 5) && (assessment["malnutrition"] && !exists(assessment["malnutrition"],"blank"))) {
	       lwfa_managed_denom = 1;
	       lwfa_managed_num = (doc.resolution == "followup" || doc.resolution == "referral" || doc.admitted == "y") ? 1 : 0;
	    } else {
	       lwfa_managed_denom = 0;
	       lwfa_managed_num = 0;
	    }
		report_values.push(new reportValue(lwfa_managed_num, lwfa_managed_denom, "Low weight managed", false, "Very low weight for age or malnourished patients under 5 given appropriate follow up."));      
	    
		/*    
	    #-----------------------------------------
	    #6. Fever managed appropriately
	    */
	    drugs_prescribed = doc.drugs_prescribed;
	    var severe_fever_symptom = function(doc) {
	       return (exists(assessment["fever"],"sev_cornea") ||
	       		   exists(assessment["fever"],"sev_mouth_ulcer") ||
	       		   exists(assessment["fever"],"sev_one_week") ||
				   exists(assessment["fever"],"sev_stiff_neck"));
		}
		any_danger_sign = (exists(doc.danger_signs, "none") || exists(doc.danger_signs, "blank")) ? 0 : 1;
		danger_sign_w_fever = (any_danger_sign && (assessment["fever"] || (vitals["temp"].parseFloat >= 37.5)));
 						   
	    if ((exists(assessment["categories"], "fever")) ||
	    	(assessment["fever"] && !exists(assessment["fever"],"blank")) ||
	    	(vitals["temp"].parseFloat >= 37.5)) {
	       fever_managed_denom = 1;
	       /* If malaria test positive, check for anti_malarial*/
	       if (investigations["rdt_mps"] == "p" && drugs_prescribed) {
	       		fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial"); 
	       /* If malaria test negative, check for antibiotic*/
	       } else if (investigations["rdt_mps"] == "n") {
	       		/* check if severe */
	       		if ((danger_sign_w_fever || severe_fever_symptom(doc)) && drugs_prescribed) {
       				fever_managed_num = check_drug_type(drugs_prescribed,"antibiotic") && !check_drug_type(drugs_prescribed,"antimalarial");	
       			/* Check antimalarial not given */
       			} else if (drugs_prescribed) {
       				fever_managed_num = !check_drug_type(drugs_prescribed,"antimalarial");			       		
	       		} else {
	       		/* Neg RDT, no danger signs, no severe symptoms, no drugs: mgmt is good */
	       			fever_managed_num = 1;
       			}
	       } else {
	       		fever_managed_num = 0;
	       }
	    } else {
	       fever_managed_denom = 0;
           fever_managed_num = 0;
	    }
	    report_values.push(new reportValue(fever_managed_num, fever_managed_denom, "Fever Managed", false, "Fever managed appropriately in paediatric patients.")); 
        
	    /*
	    #----------------------------------------
	    #7. Diarrhea managed appropriately
	    */
	    drugs = doc.drugs;
	    var sev_diarrhea = function(doc) {
	       return (exists(assessment["diarrhea"],"sev_drink") ||
	       		   exists(assessment["diarrhea"],"sev_eyes") ||
	       		   exists(assessment["diarrhea"],"sev_turgor"));
	    }
		any_danger_sign_but_conv = (exists(doc.danger_signs, "none") || exists(doc.danger_signs, "blank") || exists(doc.danger_signs, "convuls")) ? 0 : 1;
						   
		if (assessment["diarrhea"] && !exists(assessment["diarrhea"],"blank")) {
	       diarrhea_managed_denom = 1;
	       /* Check dehydration level */
	       if (sev_diarrhea(doc) || any_danger_sign_but_conv) {
	       		if (drugs_prescribed && exists(assessment["diarrhea"],"mod_blood_in_stool")) {
	       			diarrhea_managed_num = check_drug_type(drugs_prescribed,"antibiotic") && (check_drug_name(drugs_prescribed,"ringers_lactate") || check_drug_name(drugs_prescribed,"sodium_chloride")) || (doc.other_treatment == "fluids");
	       		} else if (drugs_prescribed) {
	       			diarrhea_managed_num = check_drug_name(drugs_prescribed,"ringers_lactate") || check_drug_name(drugs_prescribed,"sodium_chloride") || (doc.other_treatment == "fluids");
	       		} else {
	       			diarrhea_managed_num = 0;
	       		}
       		/* If its not Severe, its Moderate */
	       } else if (drugs_prescribed) {
	       		if (exists(assessment["diarrhea"],"mod_blood_in_stool")) {
	       			diarrhea_managed_num = check_drug_type(drugs_prescribed,"antibiotic") && check_drug_name(drugs_prescribed,"ors");
	       		} else {
	       			diarrhea_managed_num = check_drug_name(drugs_prescribed,"ors");
	       		}
	       } else {
	       		diarrhea_managed_num = 0;
	       }
	    } else {
	       diarrhea_managed_denom = 0;
           diarrhea_managed_num = 0;
	    }
	    report_values.push(new reportValue(diarrhea_managed_num, diarrhea_managed_denom, "Diarrhea Managed", false, "Diarrhea and dehydration managed appropriately in paediatric patients."));    
        
	    /*
	    #----------------------------------------
	    #8. RTI managed appropriately 
		*/
				
		sev_resp = exists(assessment["fever"],"sev_stridor") || exists(assessment["fever"],"sev_indrawing");	
		var high_resp_rate = function(doc) {
	       return ((doc.age > 5 && vitals["resp_rate"].parseFloat > 30) ||
	       			(doc.age <= 5 && doc.age > 1 && vitals["resp_rate"].parseFloat > 40) ||
	       			(doc.age <= 1 && doc.age > (2/12) && vitals["resp_rate"].parseFloat > 50) ||
	       			(doc.age <= (2/12) && vitals["resp_rate"].parseFloat > 60));
	    }
		
		if ((exists(assessment["categories"],"resp") && 
			(exists(doc.danger_signs, "indrawing") || high_resp_rate)) ||
			(assessment["resp"] && !exists(assessment["resp"],"blank"))) {
	   		rti_managed_denom = 1;
   			if (drugs_prescribed) {
				rti_managed_num = check_drug_type(drugs_prescribed,"antibiotic");
       		} else {
       			rti_managed_num = 0;
   			}
	    } else {
	       rti_managed_denom = 0;
           rti_managed_num = 0;
	    }
	    report_values.push(new reportValue(rti_managed_num, rti_managed_denom, "RTI Managed", false, "RTI managed appropriately in paediatric patients.")); 
		
	    /*
	    #-------------------------------------------
	    #9. Hb done if pallor detected
		*/
		
	    if (exists(doc.danger_signs,"pallor") || exists(doc.general_exam,"mod_pallor")) {
	       hb_if_pallor_denom = 1;
	       hb_if_pallor_num = Boolean(investigations["hgb"] || investigations["hct"]) ? 1 : 0;
	    } else {
	       hb_if_pallor_denom = 0;
	       hb_if_pallor_num = 0;
	    }
		report_values.push(new reportValue(hb_if_pallor_num,hb_if_pallor_denom,"Hb done if pallor", false, "Pallor investigated in paediatric patients."));
        
	    /*
	    #-------------------------------------------
	    #10. Proportion of patients followed up 
		*/
		
		followup_recorded_num = doc.resolution == "blank" ? 0 : 1;
		report_values.push(new reportValue(followup_recorded_num, 1, "Patients followed up", false, "Case Closed, Follow-Up, or Referral ticked."));
		
	    /*
	    #11.  Drugs dispensed appropriately
	    Proportion of the ’Protocol Recommended Prescription’ written without ‘Not in stock’ ticked.
		*/
        
		drugs = doc.drugs["prescribed"]["med"];
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } else {
	       drug_stock_denom = 0;
	       drug_stock_num = 0;
	    }
		report_values.push(new reportValue(drug_stock_num, drug_stock_denom, "Drugs In Stock", false, "First line drugs in stock at the clinic.")); 
        
	    emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 
    } 
}