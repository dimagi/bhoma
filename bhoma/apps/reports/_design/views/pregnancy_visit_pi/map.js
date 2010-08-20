function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
	// these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
	
    NAMESPACE = "http://cidrz.org/bhoma/pregnancy"
    
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
	    #1. Pre-eclampsia screening and management
	    #1a.Proportion of routine visits with Blood Pressure and Urinalysis results
		*/
		
		vitals_recorded_num = Boolean(doc.blood_pressure && doc.urinalysis) ? 1 : 0;
        report_values.push(new reportValue(vitals_recorded_num, 1, "Vitals recorded")); 
	    
		/*
        #----------------------------------- 
	    #1b.Proportion of (1a) above with abnormal results or Oedema who are 
	    #prescribed with Antihypertensives and Referred. 
		*/
	    
	    /* TODO: assuming get systolic and diastolic blood pressure from form */
		bp_systolic = doc.blood_pressure;
		bp_diastolic = doc.blood_pressure;
	    /*abnormal_bp = Boolean(bp_systolic >= 140) || (bp_diastolic >= 90); */
		abnormal_bp = true; //TODO - fix this
	    abnormal_preeclamp = (abnormal_bp && (doc.urinalysis == "protein_pos") && (doc.gestational_age > 20));
	
	    /* Assess treatment methods */
	    if (abnormal_preeclamp || (doc.danger_signs== "oedema")) {
			/* todo: see if Referral is ticked on Sick Preg Form */
			/* todo: check med */
			preeclamp_mgmt_denom = 1;
			/*preeclamp_mgmt_num = (exists(sickdoc.resolution, "referral") || exists(drugs => right med)) ? 1 : 0; */
	    } else {
			preeclamp_mgmt_denom = 0;
			preeclamp_mgmt_num = 0;
	    }
	    report_values.push(new reportValue(preeclamp_mgmt_num, preeclamp_mgmt_denom, "Pre-eclampsia Managed")); 
		
	    /*
	    #----------------------------------
	    #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
		*/
		
		clinic_exam_num = Boolean(doc.fundal_height && doc.presentation && doc.fetal_heart_rate) ? 1 : 0;
		report_values.push(new reportValue(clinic_exam_num, 1, "Clinical Exam"));
	    
			
		/*
		#--------------------------------------------
	    #9.  Drugs dispensed appropriately
		*/
		
		/*TODO: search through sick pregnancy forms for drugs dispensed */
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
