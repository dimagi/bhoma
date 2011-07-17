function(doc) {
    /* 
     * Paediatric (was Under-five) Performance Indicator Report
     */
    
    // !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
	
	var NAMESPACE = "http://cidrz.org/bhoma/underfive";
    
    if (xform_matches(doc, NAMESPACE))
    {   
        var enc_date = get_encounter_date(doc);
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
		
		var vitals = doc.vitals;
		var ht_wt_rec_num = Boolean(vitals.height && vitals.weight) ? 1 : 0;
		_emit("ht_wt_rec",ht_wt_rec_num, 1);
        
        /* 
		#-----------------------------------
		# 2. Temperature, respiratory rate, and heart rate recorded 
		*/
		
        var vitals_rec_num = Boolean(vitals.temp && vitals.resp_rate && vitals.heart_rate) ? 1 : 0;
		_emit("vit_rec", vitals_rec_num, 1);
		
        /*
		#-----------------------------------
		# 3. HIV test ordered appropriately
		*/
	    
	    
		// whether there was an hiv test in the last 3 months
        var recent_non_reactive_hiv_test = function(doc) {
           if (doc.hiv.test_result === "nr" && doc.hiv.test_date) {
               test_date = parse_date(doc.hiv.test_date);
               var days_since_last_test = days_between(test_date, enc_date);
               return days_since_last_test <= 90;
           }
        }
        
		var shows_hiv_symptoms = function(doc) {
	       return (exists(doc.phys_exam_detail,"lymph") ||
	       		   exists(doc.phys_exam_detail,"liver_spleen") ||
				   exists(doc.assessment.resp,"mod_fast_breath") ||
	               exists(doc.assessment.diarrhea, "mod_two_weeks") ||
	               exists(doc.assessment.fever, "sev_one_week") ||
				   exists(doc.assessment.malnutrition, "sev_sd") ||
				   exists(doc.assessment.malnutrition, "mod_sd") ||
				   exists(doc.secondary_diagnosis_one,"rti_pneumonia") ||
				   exists(doc.secondary_diagnosis_one,"persistent_diarrhea") ||
				   exists(doc.secondary_diagnosis_one,"chronic_ear_infection") ||
				   exists(doc.secondary_diagnosis_two,"very_low_weight") ||
	               exists(doc.diagnosis,"rti_pneumonia") ||
				   exists(doc.diagnosis,"persistent_diarrhea") ||
				   exists(doc.diagnosis,"chronic_ear_infection") ||
				   exists(doc.diagnosis,"very_low_weight"));
	    }
	    
	    var get_age_in_days = function (doc) {
	       // doesn't exist yet but might one day.
	       //if (doc.age_in_months) {
	       //    return doc.age_in_months;
	       //}
	       if (doc.dob_raw) {
	           var dob = parse_date(doc.dob_raw);
	           return days_between(dob, enc_date);
	       } else if (doc.age) {
	           // this is the best proxy we have.
	           return doc.age * 365.25;
	       } else if (doc.age_raw) {
               // this is the best proxy we have.
               return doc.age_raw * 365.25;
           } else {
               return null;
	       }
	    };
	    
	    var assessment = doc.assessment;
        var investigations = doc.investigations;
        var hiv = doc.hiv;
		
		var hiv_unk_exp = (hiv.status == "unk" || hiv.status == "exp" || hiv.status == "blank") ? 1 : 0;
		var no_hiv_test = (hiv.test_result == "nd" || hiv.test_result =="blank") ? 1 : 0;
		var non_reactive = hiv.test_result != "r";
		var no_card = hiv.status == "no_card";
		var should_test_hiv = 0;
        var did_test_hiv = 0;
        
        // age check
        var age_cutoff = 365 * 1.5; // 18 months
        var age_in_days = get_age_in_days(doc);
        var age_matches = age_in_days != null ? age_in_days > age_cutoff : true; // by default include people if we don't have data
		if (age_matches && ((hiv_unk_exp && no_hiv_test) || ((non_reactive || no_card) && !recent_non_reactive_hiv_test(doc) && shows_hiv_symptoms(doc)))) {
	       should_test_hiv = 1;
	       did_test_hiv = (investigations.hiv_rapid == "r" || investigations.hiv_rapid == "nr" || investigations.hiv_rapid == "ind") ? 1 : 0;
	    } 
	    _emit("hiv_test", did_test_hiv, should_test_hiv);
	    
	    /*	    
		#-----------------------------------------------
	    #4. Weight for age assessed correctly
		*/
	    var wfa_assess_num = 0;
        var wfa_assess_denom = 0;
	    if (parseInt(doc.age) <= 5 && doc.zscore_calc_good) {
	    	wfa_assess_denom = 1;
	    	if (doc.zscore_calc_good === true || doc.zscore_calc_good == "true") {
	    		wfa_assess_num = 1;
    		} else {
    			wfa_assess_num = 0;
			}
	    } 
	    _emit("wt_assessed", wfa_assess_num, wfa_assess_denom);
        
        /* 
	    #--------------------------------------
	    #5. Low weight for age managed appropriately
		*/

        var lwfa_managed_denom = 0;
        var lwfa_managed_num = 0;
		if ((parseInt(doc.age) <= 5) && (assessment.malnutrition && !exists(assessment.malnutrition,"blank"))) {
	       lwfa_managed_denom = 1;
	       lwfa_managed_num = (doc.resolution == "followup" || doc.resolution == "referral" || doc.admitted == "y") ? 1 : 0;
	    } 
		_emit("low_wt_follow", lwfa_managed_num, lwfa_managed_denom);
	    
		/*    
	    #-----------------------------------------
	    #6. Fever managed appropriately
	    */
	    var drugs_prescribed = doc.drugs_prescribed;
	    var severe_fever_symptom = function(doc) {
	       return (exists(doc.assessment.fever,"sev_cornea") ||
	       		   exists(doc.assessment.fever,"sev_mouth_ulcer") ||
	       		   exists(doc.assessment.fever,"sev_one_week") ||
				   exists(doc.assessment.fever,"sev_stiff_neck"));
		}
		var any_danger_sign = (exists(doc.danger_signs, "none") || exists(doc.danger_signs, "blank")) ? 0 : 1;
		var danger_sign_w_fever = (any_danger_sign && (assessment.fever || (vitals.temp >= 37.5)));
 		var fever_managed_denom = 0;
        var fever_managed_num = 0;				   
	    if (doc.encounter_type === "new_case" &&
            ((exists(assessment.categories, "fever")) ||
	    	 (assessment.fever && !exists(assessment.fever,"blank")) ||
	    	 (vitals.temp >= 37.5))) {
	       fever_managed_denom = 1;
	       /* If malaria test positive, check for anti_malarial*/
	       if (investigations.rdt_mps == "p" && drugs_prescribed) {
	       		fever_managed_num = check_drug_type(drugs_prescribed,"antimalarial"); 
	       /* If malaria test negative, check for antibiotic*/
	       } else if (investigations.rdt_mps == "n") {
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
	    }
	    _emit("fev_mgd", fever_managed_num, fever_managed_denom);
        
	    /*
	    #----------------------------------------
	    #7. Diarrhea managed appropriately
	    */
	    var sev_diarrhea = function(doc) {
	       return (exists(doc.assessment.diarrhea,"sev_drink") ||
	       		   exists(doc.assessment.diarrhea,"sev_eyes") ||
	       		   exists(doc.assessment.diarrhea,"sev_turgor"));
	    }
		var any_danger_sign_but_conv = (exists(doc.danger_signs, "none") || exists(doc.danger_signs, "blank") || exists(doc.danger_signs, "convuls")) ? 0 : 1;
		var diarrhea_managed_denom = 0;
        var diarrhea_managed_num = 0;			   
		if (assessment.diarrhea && !exists(assessment.diarrhea,"blank")) {
	       diarrhea_managed_denom = 1;
	       /* Check dehydration level */
	       if (sev_diarrhea(doc) || any_danger_sign_but_conv) {
	       		if (drugs_prescribed && exists(assessment.diarrhea,"mod_blood_in_stool")) {
	       			diarrhea_managed_num = (check_drug_type(drugs_prescribed,"antibiotic") && (check_drug_name(drugs_prescribed,"ringers_lactate") || check_drug_name(drugs_prescribed,"sodium_chloride")) || (doc.other_treatment == "fluids")) ? 1 : 0;
	       		} else if (drugs_prescribed) {
	       			diarrhea_managed_num = (check_drug_name(drugs_prescribed,"ringers_lactate") || check_drug_name(drugs_prescribed,"sodium_chloride") || (doc.other_treatment == "fluids")) ? 1 : 0;
	       		} else {
	       			diarrhea_managed_num = 0;
	       		}
       		/* If its not Severe, its Moderate */
	       } else if (drugs_prescribed) {
	       		if (exists(assessment.diarrhea,"mod_blood_in_stool")) {
	       			diarrhea_managed_num = check_drug_type(drugs_prescribed,"antibiotic") && check_drug_name(drugs_prescribed,"ors");
	       		} else {
	       			diarrhea_managed_num = check_drug_name(drugs_prescribed,"ors");
	       		}
	       } else {
	       		diarrhea_managed_num = 0;
	       }
	    } 
	    _emit("dia_mgd", diarrhea_managed_num, diarrhea_managed_denom);
        
	    /*
	    #----------------------------------------
	    #8. RTI managed appropriately 
		*/
				
		var high_resp_rate = function(doc) {
	       return ((parseInt(doc.age) > 5 && vitals.resp_rate > 30) ||
                   (parseInt(doc.age) <= 5 && parseInt(doc.age) > 1 && vitals.resp_rate > 40) ||
	       		   (parseInt(doc.age) <= 1 && parseInt(doc.age) > (2/12) && vitals.resp_rate > 50) ||
	       		   (parseInt(doc.age) <= (2/12) && vitals.resp_rate > 60)) ? 1 : 0;
	    }
		
		var rti_managed_denom = 0;
        var rti_managed_num = 0;
		if ((exists(assessment.categories,"resp") && 
			(exists(doc.danger_signs, "indrawing") || high_resp_rate(doc))) ||
			(assessment.resp && !exists(assessment.resp,"blank"))) {
	   		rti_managed_denom = 1;
   			if (drugs_prescribed) {
				rti_managed_num = check_drug_type(drugs_prescribed,"antibiotic");
       		} else {
       			rti_managed_num = 0;
   			}
	    }
	    _emit("rti_mgd", rti_managed_num, rti_managed_denom);
		
	    /*
	    #-------------------------------------------
	    #9. Hb done if pallor detected
		*/
		var hb_if_pallor_denom = 0;
        var hb_if_pallor_num = 0;
	    if (exists(doc.danger_signs,"pallor") || exists(doc.general_exam,"mod_pallor")) {
	       hb_if_pallor_denom = 1;
	       hb_if_pallor_num = Boolean(investigations.hgb || investigations.hct) ? 1 : 0;
	    } 
		_emit("pallor_mgd", hb_if_pallor_num, hb_if_pallor_denom);
        
	    /*
	    #-------------------------------------------
	    #10. Proportion of patients followed up 
		*/
		
		var followup_recorded_num = doc.resolution == "blank" ? 0 : 1;
		_emit("fu_rec", followup_recorded_num, 1);
		
	    /*
	    #11.  Drugs dispensed appropriately
	    #Proportion of the Protocol Recommended Prescription written without Not in stock ticked.
		*/
        
		var drugs = doc.drugs.prescribed.med;
		var drug_stock_denom = 0;
        var drug_stock_num = 0;
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } 
		_emit("drugs_stocked", drug_stock_num, drug_stock_denom);
        
        /*
         * All children from 6 weeks old to 10 weeks who are exposed should have PCR ordered.
         */
        // numerator : all children between  6 weeks and 10 weeks who are exposed who get a PCR test ordered
        // denominator: all children between  6 weeks and 10 weeks who are exposed
        
        var age_lower_bound = 6 * 7; // 6 weeks
        var age_upper_bound = 11 * 7; // 11 weeks
        // by default don't include people if we don't have data (window too small)
        age_matches = age_in_days != null ? age_in_days >= age_lower_bound && age_in_days < age_upper_bound : true;
        //var got_pcr_test = doc.hiv.test_type == "pcr";
        var got_pcr_test = exists(doc.investigations.other, "hiv_pcr");
        var pcr_wks_denom = (doc.hiv.status == "exp" && age_matches) ? 1 : 0;
        var pcr_wks_num = (pcr_wks_denom && got_pcr_test) ? 1 : 0;
        _emit("pcr_done_10wk", pcr_wks_num, pcr_wks_denom);
        
        /*
         * All Children from 6 weeks to 17 Months who are exposed and exhibit symptoms 
         * or diagnoses with an asterisk should have PCR ordered.
         */
        // Numerator: all children between  6 weeks and 17 months who are exposed and have an asterisk who get a PCR test ordered
        // Denominator: all children between  6 weeks and 17 months who are exposed and have an asterisk
        age_upper_bound = 365 * 1.5; // 18 months
        // by default don't include people if we don't have data (window too small)
        age_matches = age_in_days != null ? age_in_days >= age_lower_bound && age_in_days < age_upper_bound : true; 
        var pcr_mos_denom = (doc.hiv.status == "exp" && age_matches && shows_hiv_symptoms(doc)) ? 1 : 0;
        var pcr_mos_num = (pcr_mos_denom && got_pcr_test) ? 1 : 0;
        _emit("pcr_done_17mo", pcr_mos_num, pcr_mos_denom);

    } 
}