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
        
        vitals = doc.vitals;
        /*
        #-----------------------------------
        #1. Blood Pressure recorded
        */
        
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
	    if (exists(assessment["categories"],"resp")) {
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
	               exists(assessment["resp"],"very_fast_breath") ||
	               exists(assessment["categories"],"weight") ||
	               exists(assessment["categories"], "anogen") ||
	               exists(assessment["dischg_abdom_pain"], "mass") ||
	               exists(assessment["mouth_throat"], "ulcers"));
	               
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
	    TODO
	    #5. Drugs dispensed appropriately
	    if adult_form['prescription_dispensed']: 
	        adult_form['pi_drugs'] = mgmt_good
	    elif adult_form['prescription_not_dispensed']:
	        adult_form['pi_drugs'] = mgmt_bad
	    else:
	        adult_form['pi_drugs'] = mgmt_na
	    
	    */
	    values["drugs_appropriate"] = false;
	    emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), enc_date.getDate()], values); 
    } 
}