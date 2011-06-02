function(doc) {
    /* 
     * Adult Performance Indicator Report
     */
    
    // !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
    
    var NAMESPACE = "http://cidrz.org/bhoma/general";
    
    
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
    
        _emit("total", 1, 1);
        
        /*
        #-----------------------------------
        #1. Blood Pressure recorded
        */
        
        var vitals = doc.vitals;        
        var bp_recorded_num = Boolean(vitals.bp) ? 1 : 0;
        _emit("bp_rec", bp_recorded_num, 1);
        
        /* 
		#-----------------------------------
		# 2. Temperature, respiratory rate, and heart rate recorded 
		*/

        var vitals_rec_num = Boolean(vitals.temp && vitals.resp_rate && vitals.heart_rate) ? 1 : 0;
		_emit("vit_rec", vitals_rec_num, 1);
		
	    /*
	    #-----------------------------------
	    #3. Malaria managed appropriately
	    */  
	    var drugs_prescribed = doc.drugs_prescribed;	
	    var assessment = doc.assessment;			
	    var malaria_managed_denom = 0;
        var malaria_managed_num = 0;	   
	    if (exists(assessment.categories, "fever") ||
	    	(assessment.fever && !exists(assessment.fever,"blank")) ||
	    	(vitals.temp >= 37.5) || exists(doc.danger_signs, "fever")) {
	       malaria_managed_denom = 1;
	       /* If malaria test positive, check for anti_malarial*/
	       if (doc.investigations.rdt_mps == "p" && drugs_prescribed) {
	       		malaria_managed_num = check_drug_type(drugs_prescribed,"antimalarial"); 
	       /* If malaria test negative, check anti_malarial not given*/
	       } else if (doc.investigations.rdt_mps == "n") {
	       		if (drugs_prescribed) {
       				malaria_managed_num = check_drug_type(drugs_prescribed,"antimalarial") ? 0 : 1;			       		
	       		} else {
	       		/* Neg RDT, no drugs means no antimalarial, consider good */
	       			malaria_managed_num = 1;
       			}
	       } else {
	       		malaria_managed_num = 0;
	       }
	    } 
	    _emit("mal_mgd", malaria_managed_num, malaria_managed_denom);
	    
        /*
	    #----------------------------------------------
	    #4. HIV test ordered appropriately
	    # Check if HIV symptoms present
	    */
	    var shows_hiv_symptoms = function(doc) {
	       return (exists(doc.phys_exam_detail, "lymph") || 
	               exists(doc.assessment.categories,"weight") ||
	               exists(doc.assessment.resp,"sev_fast_breath") ||
				   exists(doc.assessment.resp,"mod_cough_two_weeks") ||
	               exists(doc.assessment.resp,"mod_sweats") ||
	               exists(doc.assessment.abdom_anog, "mod_vesicles") ||
	               exists(doc.assessment.abdom_anog, "mod_groin") ||
	               exists(doc.assessment.abdom_anog, "mod_sores") ||
	               exists(doc.assessment.abdom_anog, "mod_warts") ||
	               exists(doc.assessment.abdom_anog, "mod_burning") ||
	               exists(doc.assessment.abdom_anog, "mod_swelling") ||
	               exists(doc.assessment.abdom_anog, "mod_itching") ||
	               exists(doc.assessment.abdom_anog, "mod_sti") ||
	               exists(doc.assessment.abdom_anog, "mod_discharge") ||
	               exists(doc.assessment.abdom_anog, "mod_cervical") ||
	               exists(doc.assessment.abdom_anog, "mod_abdomen") ||
	               exists(doc.assessment.categories, "mouth_throat") ||
	               exists(doc.assessment.fever, "mod_fever") ||
	               exists(doc.assessment.fever, "mod_no_apparent_cause_fever") ||
	               exists(doc.assessment.dehydration_diarrhea, "mod_diarrhea") ||
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
	    
	    var not_reactive = doc.history.hiv_result != "r";
	    var should_test_hiv = 0;
	    var did_test_hiv = 0;
	    if (not_reactive && shows_hiv_symptoms(doc)) {
	       should_test_hiv = 1;
	       did_test_hiv = (doc.investigations.hiv_rapid == "r" || doc.investigations.hiv_rapid == "nr" || doc.investigations.hiv_rapid == "ind") ? 1 : 0;
	    }
	    _emit("hiv_test", did_test_hiv, should_test_hiv);
		    
		/*
	    #----------------------------------------------
	    #5.  Drugs dispensed appropriately
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
    } 
}