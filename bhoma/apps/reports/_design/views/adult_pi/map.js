function(doc) {
    /* Adult Performance Indicator Report
     */
    
    NAMESPACE = "http://cidrz.org/bhoma/general"
    
    
    if (doc["#doc_type"] == "XForm" && doc["@xmlns"] == NAMESPACE)
    {   
        values = {};
        /* this field keeps track of total forms */
        values["total"] = true;
        
        new_case = doc.encounter_type == "new_case";
        values["followup_case"] = !new_case;
        
        
        enc_date = new Date(Date.parse(doc.encounter_date));
        
        /*
        #-----------------------------------
        #1. Blood Pressure recorded
        */

        vitals = doc.vitals;        
        values['bp_recorded'] = Boolean(vitals["bp"]);
        
        /*
        #-----------------------------------
	    #2. TB managed appropriately
	    */
	    
	    var exists = function(basestring, searchstring) {
	       return basestring && basestring.indexOf(searchstring) >= 0;
	    }
	    
	    assessment = doc.assessment;
	    investigations = doc.investigations;
	    if (exists(assessment["categories"],"resp") && exists(assessment["resp"],"mod_cough_two_weeks")) {
	       values['tb_managed_denom'] = true;
	       values['tb_managed_num'] = exists(investigations["categories"], "sputum");
	    } else {
	       values['tb_managed_denom'] = false;
	       values['tb_managed_num'] = false;
	    }
	
	    /*
	    #-----------------------------------
	    #3. Malaria managed appropriately
	    */       
        
	    if (exists(doc.danger_signs, "fever")) {
	       values["fever_present"] = true;
	       malaria_test_ordered = exists(investigations["categories"], "rdt_mps");
	       values["fever_present_malaria_ordered"] = malaria_test_ordered;
	       if (malaria_test_ordered) {
	           /* todo: check prescriptions */
	       }
	    } else {
	       values["fever_present"] = false;
           values["fever_present_malaria_ordered"] = false;
	    }
	    
        /*
	    #----------------------------------------------
	    #4. HIV test ordered appropriately
	    # Check if HIV symptoms present
	    */
	    
	    var shows_hiv_symptoms = function(doc) {
	       return (exists(doc.phys_exam_detail, "lymph") || 
	               exists(assessment["resp"],"sev_fast_breath") ||
				   exists(assessment["resp"],"mod_cough_two_weeks") ||
	               exists(assessment["categories"],"weight") ||
	               exists(assessment["categories"], "anogen") ||
	               exists(assessment["dischg_abdom_pain"], "sev_mass") ||
	               exists(assessment["mouth_throat"], "mod_ulcers"));
	               
	    }
	    hiv_not_tested = doc.hiv_result == "nd";
	    if (hiv_not_tested && shows_hiv_symptoms(doc)) {
	       values["should_test_hiv"] = true;
	       values["did_test_hiv"] = exists(investigations["categories"], "hiv_rapid");
	    } else {
	       values["should_test_hiv"] = false;
           values["did_test_hiv"] = false;
	    }
	    
		/*
	    #----------------------------------------------
	    #5. Drugs dispensed appropriately
	    */
		
		drugs = doc.drugs;
		if (exists(drugs["dispensed_as_prescribed"])) {
	       values['drugs_appropriate_denom'] = true;
	       values['drugs_appropriate_num'] = exists(drugs["dispensed_as_prescribed"], "y");
	    } else {
	       values['drugs_appropriate_denom'] = false;
	       values['drugs_appropriate_num'] = false;
	    }
		

	    emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), enc_date.getDate()], values); 
    } 
}