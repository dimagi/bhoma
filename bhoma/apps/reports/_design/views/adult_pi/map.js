function(doc) {
    /* 
     * Adult Performance Indicator Report
     */
    
    // !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
    
    NAMESPACE = "http://cidrz.org/bhoma/general"
    
    
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
    
        _emit("total", 1, 1);
        
        /*
        #-----------------------------------
        #1. Blood Pressure recorded
        */
        
        vitals = doc.vitals;        
        bp_recorded_num = Boolean(vitals["bp"]) ? 1 : 0;
        _emit("bp_rec", bp_recorded_num, 1);
        /* 
		#-----------------------------------
		# 2. Temperature, respiratory rate, and heart rate recorded 
		*/
		
        vitals_rec_num = Boolean(vitals["temp"] && vitals["resp_rate"] && vitals["heart_rate"]) ? 1 : 0;
		_emit("vit_rec", vitals_rec_num, 1);
		
	    /*
	    #-----------------------------------
	    #3. Malaria managed appropriately
	    */  
	    drugs_prescribed = doc.drugs_prescribed;	
	    assessment = doc.assessment;				   
	    if (exists(assessment["categories"], "fever") ||
	    	(assessment["fever"] && !exists(assessment["fever"],"blank")) ||
	    	(vitals["temp"] >= 37.5) || exists(doc.danger_signs, "fever")) {
	       malaria_managed_denom = 1;
	       /* If malaria test positive, check for anti_malarial*/
	       if (doc.investigations["rdt_mps"] == "p" && drugs_prescribed) {
	       		malaria_managed_num = check_drug_type(drugs_prescribed,"antimalarial"); 
	       /* If malaria test negative, check anti_malarial not given*/
	       } else if (doc.investigations["rdt_mps"] == "n") {
	       		if (drugs_prescribed) {
       				malaria_managed_num = check_drug_type(drugs_prescribed,"antimalarial") ? 0 : 1;			       		
	       		} else {
	       		/* Neg RDT, no drugs means no antimalarial, consider good */
	       			malaria_managed_num = 1;
       			}
	       } else {
	       		malaria_managed_num = 0;
	       }
	    } else {
	       malaria_managed_denom = 0;
           malaria_managed_num = 0;
	    }
	    _emit("mal_mgd", malaria_managed_num, malaria_managed_denom);
	    
        /*
	    #----------------------------------------------
	    #4. HIV test ordered appropriately
	    # Check if HIV symptoms present
	    */
	    
	    var shows_hiv_symptoms = function(doc) {
	       return (exists(doc.phys_exam_detail, "lymph") || 
	               exists(assessment["categories"],"weight") ||
	               exists(assessment["resp"],"sev_fast_breath") ||
				   exists(assessment["resp"],"mod_cough_two_weeks") ||
	               exists(assessment["resp"],"mod_sweats") ||
	               exists(assessment["abdom_anog"], "mod_vesicles") ||
	               exists(assessment["abdom_anog"], "mod_groin") ||
	               exists(assessment["abdom_anog"], "mod_sores") ||
	               exists(assessment["abdom_anog"], "mod_warts") ||
	               exists(assessment["abdom_anog"], "mod_burning") ||
	               exists(assessment["abdom_anog"], "mod_swelling") ||
	               exists(assessment["abdom_anog"], "mod_itching") ||
	               exists(assessment["abdom_anog"], "mod_sti") ||
	               exists(assessment["abdom_anog"], "mod_discharge") ||
	               exists(assessment["abdom_anog"], "mod_cervical") ||
	               exists(assessment["abdom_anog"], "mod_abdomen") ||
	               exists(assessment["categories"], "mouth_throat") ||
	               exists(assessment["fever"], "mod_fever") ||
	               exists(assessment["fever"], "mod_no_apparent_cause_fever") ||
	               exists(assessment["dehydration_diarrhea"], "mod_diarrhea") ||
	               exists(doc.secondary_diagnosis_one,"rti_pneumonia") ||
				   exists(doc.secondary_diagnosis_one,"tb") ||
				   exists(doc.secondary_diagnosis_one,"sti") ||
				   exists(doc.secondary_diagnosis_one,"pid") ||
				   exists(doc.secondary_diagnosis_two,"persistent_diarrhea") ||
				   exists(doc.secondary_diagnosis_two,"skin_infection") ||
				   exists(doc.secondary_diagnosis_two,"anaemia") ||
				   exists(doc.diagnosis,"rti_pneumonia") ||
				   exists(doc.diagnosis,"tb") ||
				   exists(doc.diagnosis,"sti") ||
				   exists(doc.diagnosis,"pid") ||
				   exists(doc.diagnosis,"persistent_diarrhea") ||
				   exists(doc.diagnosis,"skin_infection") ||
				   exists(doc.diagnosis,"anaemia"));           
	    }
	    
	    not_reactive = doc.history["hiv_result"] != "r";
	    if (not_reactive && shows_hiv_symptoms(doc)) {
	       should_test_hiv = 1;
	       did_test_hiv = (doc.investigations["hiv_rapid"] == "r" || doc.investigations["hiv_rapid"] == "nr" || doc.investigations["hiv_rapid"] == "ind") ? 1 : 0;
	    } else {
	       should_test_hiv = 0;
           did_test_hiv = 0;
	    }
	    _emit("hiv_test", did_test_hiv, should_test_hiv);
		    
		/*
	    #----------------------------------------------
	    #5.  Drugs dispensed appropriately
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