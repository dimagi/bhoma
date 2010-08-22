function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
	// these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
	
    if (doc["doc_type"] == "CPregnancy") {
    
        report_values = [];
        /* this field keeps track of total pregnancies */
        first_visit_date = doc.first_visit_date
        
        report_values.push(new reportValue(1,1,"total",true));
        
        /*
        #----------------------------------- 
	    #1b.Proportion of (1a) above with abnormal results or Oedema who are 
	    #prescribed with Antihypertensives and Referred. 
		*/
	    
	    for (var i in doc.dates_preeclamp_treated) {
            follow_date = parse_date(doc.dates_danger_signs_followed[i]);
            emit([follow_date.getFullYear(), follow_date.getMonth(), doc.clinic_id], 
                 [new reportValue(1, 1, "Pre-eclampsia Managed")]); 
        }
        for (var i in doc.dates_preeclamp_not_treated) {
            follow_date = parse_date(doc.dates_danger_signs_followed[i]);
            emit([follow_date.getFullYear(), follow_date.getMonth(), doc.clinic_id], 
                 [new reportValue(0, 1, "Pre-eclampsia Managed")]); 
        }
        
		/*
        #-----------------------------------
	    #2. Danger signs followed up
	    #Assess if sick pregnancy form needs to be filled out
		*/
		
		for (var i in doc.dates_danger_signs_followed) {
            follow_date = parse_date(doc.dates_danger_signs_followed[i]);
            emit([follow_date.getFullYear(), follow_date.getMonth(), doc.clinic_id], 
                 [new reportValue(1, 1, "Danger Sign Follow Up")]); 
		}
		for (var i in doc.dates_danger_signs_not_followed) {
            follow_date = parse_date(doc.dates_danger_signs_followed[i]);
            emit([follow_date.getFullYear(), follow_date.getMonth(), doc.clinic_id], 
                 [new reportValue(0, 1, "Danger Sign Follow Up")]); 
        }
		
		
		/*
	    #----------------------------------
	    #4. HIV Testing: Proportion of all pregnant women seen with HIV test done
		
		## Count per Pregnancy ID ##
		
		*/
		
		report_values.push(new reportValue(doc.hiv_test_done ? 1:0, 1, "HIV Test Done"));
		
		/*
	    #----------------------------------
	    #5. NVP: Proportion of all women testing HIV-positive provided a dose of NVP on the 1st visit
	    */
		
		report_values.push(new reportValue(doc.got_nvp_when_tested_positive ? 1:0, 
		                                   doc.ever_tested_positive ? 1:0, "NVP on first pos visit"));
	    
		/*	
	    #-----------------------------------
	    #6. AZT: a.Proportion of all women testing HIV-positive provided AZT on ANY visit
	    #        b.Proportion of all women provided AZT who received it at their last visit
	    */
        
        got_azt_when_positive = doc.got_azt && doc.ever_tested_positive;
		report_values.push(new reportValue(got_azt_when_positive ? 1:0,
		                                   doc.ever_tested_positive ? 1:0, "AZT on any visit"));
		
		report_values.push(new reportValue(doc.got_azt_on_consecutive_visits ? 1:0,
		                                   doc.got_azt ? 1:0, "AZT on consecutive visits"));	
		
	    /*	
	    #-----------------------------------
	    #7a.Proportion of all pregnant women seen with RPR test given on the 1st visit
		
		*/
		
		report_values.push(new reportValue(doc.rpr_given_on_first_visit ? 1:0,
		                                   1, "RPR given on 1st visit"));
		
		/*
		#-----------------------------------
	    #7b.Proportion of all women testing RPR-positive provided a dose of penicillin
		*/
		
		report_values.push(new reportValue(doc.got_penicillin_when_rpr_positive ? 1:0, 
		                                   doc.tested_positive_rpr ? 1:0, "RPR positive given penicillin"));
		
	    /*
	    #7c. Proportion of all women testing RPR-positive whose partners are given penicillin 
	    #(does not include first visit that women discovers she is RPR positive)
		*/
		
		report_values.push(new reportValue(doc.partner_got_penicillin_when_rpr_positive ? 1:0,
		                                   doc.tested_positive_rpr ? 1:0, "RPR positive partner penicillin"));

		/*
	    #--------------------------------------------
	    #8. Fansidar:  Proportion of all pregnant women seen provided three doses of fansidar
		
		*/
		
		report_values.push(new reportValue(doc.got_three_doses_fansidar ? 1:0,
                                           1, "Got 3 doses Fansidar"));

        
		/*
		#--------------------------------------------
	    #9.  Drugs dispensed appropriately
		*/
		
		/*TODO: search through sick pregnancy forms for drugs dispensed */
	    first_visit_date = parse_date(doc.first_visit_date);
	    emit([first_visit_date.getFullYear(), first_visit_date.getMonth(), doc.clinic_id], report_values); 
    } 
}
