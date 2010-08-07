function(doc) {
    /* 
     * Adult Performance Indicator Report
     */
    
    // these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
    
    NAMESPACE = "http://cidrz.org/bhoma/general"
    
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
        #1. Blood Pressure recorded
        */
        
        vitals = doc.vitals;        
        bp_recorded_num = Boolean(vitals["bp"]) ? 1 : 0;
        report_values.push(new reportValue(bp_recorded_num, 1, "Blood pressure recorded")); 
        
        /*
        #-----------------------------------
	    #2. TB managed appropriately
	    */
	    
	    assessment = doc.assessment;
	    investigations = doc.investigations;
	    if (exists(assessment["categories"],"resp") && exists(assessment["resp"],"mod_cough_two_weeks")) {
	       tb_managed_denom = 1;
	       tb_managed_num = exists(investigations["categories"], "sputum") ? 1 : 0;
	    } else {
	       tb_managed_denom = 0;
	       tb_managed_num = 0;
	    }
	    report_values.push(new reportValue(tb_managed_num, tb_managed_denom, "TB Managed")); 
	
	    /*
	    #-----------------------------------
	    #3. Malaria managed appropriately
	    */       
        
	    if (exists(doc.danger_signs, "fever")) {
	       malaria_managed_denom = 1;
	       malaria_test_ordered = exists(investigations["categories"], "rdt_mps");
	       if (malaria_test_ordered) {
	           /* todo: check prescriptions */
	       }
	       malaria_managed_num = malaria_test_ordered ? 1 : 0;
	    } else {
	       malaria_managed_denom = 0;
           malaria_managed_num = 0;
	    }
	    report_values.push(new reportValue(malaria_managed_num, malaria_managed_denom, "Malaria Managed")); 
    
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
	       should_test_hiv = 1;
	       did_test_hiv = exists(investigations["categories"], "hiv_rapid") ? 1 : 0;
	    } else {
	       should_test_hiv = 0;
           did_test_hiv = 0;
	    }
	    report_values.push(new reportValue(did_test_hiv, should_test_hiv, "HIV Test Ordered"));
		    
		/*
	    #----------------------------------------------
	    #5. Drugs dispensed appropriately
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
    
	    emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth()], report_values); 
    } 
}