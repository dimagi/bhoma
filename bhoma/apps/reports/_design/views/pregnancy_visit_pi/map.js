function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
	// these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
	
    HEALTHY_NAMESPACE = "http://cidrz.org/bhoma/pregnancy";
    SICK_NAMESPACE = "http://cidrz.org/bhoma/sick_pregnancy";
    
    if (xform_matches(doc, HEALTHY_NAMESPACE))
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
	    #----------------------------------
	    #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
		*/
		
		clinic_exam_num = Boolean(doc.fundal_height && doc.presentation && doc.fetal_heart_rate) ? 1 : 0;
		report_values.push(new reportValue(clinic_exam_num, 1, "Clinical Exam"));
	    
		emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 
    } 
    else if (xform_matches(doc, SICK_NAMESPACE)) {
        
        /*
        #--------------------------------------------
        #9.  Drugs dispensed appropriately
        */
        
        drugs = doc.drugs;
        if (exists(drugs["dispensed_as_prescribed"])) {
           drugs_appropriate_denom = 1;
           drugs_appropriate_num = exists(drugs["dispensed_as_prescribed"], "y") ? 1 : 0;
        } else {
           drugs_appropriate_denom = 0;
           drugs_appropriate_num = 0;
        }
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], 
             [new reportValue(drugs_appropriate_num, drugs_appropriate_denom, "Drugs dispensed appropriately")]);
    }
}
