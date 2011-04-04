function(doc) {
    /* 
     * Paediatric (was Under-five) Performance Indicator Report
     */
    
    // !code util/dates.js
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
        
        function _emit(name, num, denom) {
            emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id, name], [num, denom]);    
        }
    
        /* this field keeps track of total forms */
        _emit("total", 1, 1);
        
        /* 
		#-----------------------------------
		# 1. Height and Weight recorded 
		*/
		
		vitals = doc.vitals;
		ht_wt_rec_num = Boolean(vitals["height"] && vitals["weight"]) ? 1 : 0;
		_emit("ht_wt_rec",ht_wt_rec_num, 1);
        
        /* 
		#-----------------------------------
		# 2. Temperature, respiratory rate, and heart rate recorded 
		*/
		
        vitals_rec_num = Boolean(vitals["temp"] && vitals["resp_rate"] && vitals["heart_rate"]) ? 1 : 0;
		_emit("vit_rec", vitals_rec_num, 1);
		
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
		
		hiv_unk_exp = (hiv["status"] == "unk" || hiv["status"] == "exp" || hiv["status"] == "blank") ? 1 : 0;
		no_hiv_test = (hiv["test_result"] == "nd" || hiv["test_result"] =="blank") ? 1 : 0;
		non_reactive = hiv["test_result"] != "r";
		no_card = hiv["status"] == "no_card";	
		if ((hiv_unk_exp && no_hiv_test) || ((non_reactive || no_card) && shows_hiv_symptoms(doc))) {
	       should_test_hiv = 1;
	       did_test_hiv = (investigations["hiv_rapid"] == "r" || investigations["hiv_rapid"] == "nr" || investigations["hiv_rapid"] == "ind") ? 1 : 0;
	    } else {
	       should_test_hiv = 0;
           did_test_hiv = 0;
	    }
	    _emit("hiv_test", did_test_hiv, should_test_hiv);
	    
	    /*	    
		#-----------------------------------------------
	    #4. Weight for age assessed correctly
		*/
	    if (parseInt(doc.age) <= 5) {
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
	    _emit("wt_assessed", wfa_assess_num, wfa_assess_denom);
        
        /* 
	    #--------------------------------------
	    #5. Low weight for age managed appropriately
		*/
		
		if ((parseInt(doc.age) <= 5) && (assessment["malnutrition"] && !exists(assessment["malnutrition"],"blank"))) {
	       lwfa_managed_denom = 1;
	       lwfa_managed_num = (doc.resolution == "followup" || doc.resolution == "referral" || doc.admitted == "y") ? 1 : 0;
	    } else {
	       lwfa_managed_denom = 0;
	       lwfa_managed_num = 0;
	    }
		_emit("low_wt_follow", lwfa_managed_num, lwfa_managed_denom);
	    
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
		danger_sign_w_fever = (any_danger_sign && (assessment["fever"] || (vitals["temp"] >= 37.5)));
 						   
	    if ((exists(assessment["categories"], "fever")) ||
	    	(assessment["fever"] && !exists(assessment["fever"],"blank")) ||
	    	(vitals["temp"] >= 37.5)) {
	       fever_managed_denom = 1;
	       /* If malaria test positive, check for anti_malarial*/
	       if (investigations["rdt_mps"] == "p" && drugs_prescribed) {
	       		fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial"); 
	       /* If malaria test negative, check for antibiotic*/
	       } else if (investigations["rdt_mps"] == "n") {
	       		/* check if severe */
	       		if ((danger_sign_w_fever || severe_fever_symptom(doc)) && drugs_prescribed) {
       				fever_managed_num = (check_drug_type(drugs_prescribed,"antibiotic") && !check_drug_type(drugs_prescribed,"antimalarial")) ? 1 : 0;	
       			/* Check antimalarial not given */
       			} else if (drugs_prescribed) {
       				fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial") ? 0 : 1;			       		
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
	    _emit("fev_mgd", fever_managed_num, fever_managed_denom);
        
	    /*
	    #----------------------------------------
	    #7. Diarrhea managed appropriately
	    */
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
	       			diarrhea_managed_num = (check_drug_type(drugs_prescribed,"antibiotic") && (check_drug_name(drugs_prescribed,"ringers_lactate") || check_drug_name(drugs_prescribed,"sodium_chloride")) || (doc.other_treatment == "fluids")) ? 1 : 0;
	       		} else if (drugs_prescribed) {
	       			diarrhea_managed_num = (check_drug_name(drugs_prescribed,"ringers_lactate") || check_drug_name(drugs_prescribed,"sodium_chloride") || (doc.other_treatment == "fluids")) ? 1 : 0;
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
	    _emit("dia_mgd", diarrhea_managed_num, diarrhea_managed_denom);
        
	    /*
	    #----------------------------------------
	    #8. RTI managed appropriately 
		*/
				
		var high_resp_rate = function(doc) {
	       return ((parseInt(doc.age) > 5 && vitals["resp_rate"] > 30) ||
	       			(parseInt(doc.age) <= 5 && parseInt(doc.age) > 1 && vitals["resp_rate"] > 40) ||
	       			(parseInt(doc.age) <= 1 && parseInt(doc.age) > (2/12) && vitals["resp_rate"] > 50) ||
	       			(parseInt(doc.age) <= (2/12) && vitals["resp_rate"] > 60)) ? 1 : 0;
	    }
		
		if ((exists(assessment["categories"],"resp") && 
			(exists(doc.danger_signs, "indrawing") || high_resp_rate(doc))) ||
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
	    _emit("rti_mgd", rti_managed_num, rti_managed_denom);
		
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
		_emit("pallor_mgd", hb_if_pallor_num, hb_if_pallor_denom);
        
	    /*
	    #-------------------------------------------
	    #10. Proportion of patients followed up 
		*/
		
		followup_recorded_num = doc.resolution == "blank" ? 0 : 1;
		_emit("fu_rec", followup_recorded_num, 1);
		
	    /*
	    #11.  Drugs dispensed appropriately
	    #Proportion of the Protocol Recommended Prescription written without Not in stock ticked.
		*/
        
		drugs = doc.drugs["prescribed"]["med"];
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } else {
	       drug_stock_denom = 0;
	       drug_stock_num = 0;
	    }
		_emit("drugs_stocked", drug_stock_num, drug_stock_denom);
        
    } 
}