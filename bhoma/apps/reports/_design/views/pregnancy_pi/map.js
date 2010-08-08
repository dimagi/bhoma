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
        #-----------------------------------
	    #2. Danger signs followed up
	    #Assess if sick pregnancy form needs to be filled out
		*/
		
		danger_sign_present = doc.danger_signs != "none";
		breech_presentation = ((doc.presentation == "breech") && (doc.gestational_age > "27"));
		no_fetal_heart_rate = doc.fetal_heart_rate == "0";
		need_sick_preg_num = (danger_sign_present || breech_presentation || no_fetal_heart_rate) ? 1 : 0;
		report_values.push(new reportValue(need_sick_preg_num, 1, "Danger Sign Follow Up"));
		
		/*
	    #----------------------------------
	    #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
		*/
		
		clinic_exam_num = Boolean(doc.fundal_height && doc.presentation && doc.fetal_heart_rate) ? 1 : 0;
		report_values.push(new reportValue(clinic_exam_num, 1, "Clinical Exam"));
	    
		/*
	    #----------------------------------
	    #4. HIV Testing: Proportion of all pregnant women seen with HIV test done
		
		## Count per Pregnancy ID ##
		
		*/
		
		/*TODO: make search across healthy pregnancy visits for a given pregnancy*/
	    hiv_test_done_num = ((doc.hiv_first_visit && doc.hiv_first_visit["hiv"]) || 
	                         (doc.hiv_after_first_visit && doc.hiv_after_first_visit["hiv"] != "nd")) ? 1 : 0;
		report_values.push(new reportValue(hiv_test_done_num, 1, "HIV Test Done"));
		
		/*
	    #----------------------------------
	    #5. NVP: Proportion of all women testing HIV-positive provided a dose of NVP on the 1st visit
	    */
		
		/*TODO: be able to search through all forms to determine if woman HIV positive
		OR make a boolean value stored with pregnancy ID number that indicates hiv positive*/
		hiv_positive = ((doc.hiv_first_visit && doc.hiv_first_visit["hiv"] != "nr") ||
		                (doc.hiv_after_first_visit && doc.hiv_after_first_visit["hiv"] == "r"));
		if (hiv_positive && (doc.visit_number == "1")) {
	       nvp_mgmt_denom = 1
	       nvp_mgmt_num = exists(doc.pmtct, "nvp") ? 1 : 0;
	    } else {
	       nvp_mgmt_denom = 0;
           nvp_mgmt_num = 0;
	    }
		report_values.push(new reportValue(nvp_mgmt_num, nvp_mgmt_denom, "NVP on first visit"));
	    
		/*	
	    #-----------------------------------
	    #6. AZT: a.Proportion of all women testing HIV-positive provided AZT on ANY visit
	    #        b.Proportion of all women provided AZT who received it at their last visit
	    */
        
		if (hiv_positive) {
			hiv_azt_denom = 1;
			hiv_azt_num = exists(doc.pmtct, "azt") ? 1 : 0;
		} else {
			hiv_azt_denom = 0;
			hiv_azt_num = 0;
		}
		report_values.push(new reportValue(hiv_azt_num, hiv_azt_denom, "AZT on any visit"));
		
		/*TODO: keep record with pregnancy ID and HIV pos that knows if AZT given during last visit*/
		azt_last_visit = true;
		if (azt_last_visit) {
			hiv_azt_repeat_denom = 1;
			hiv_azt_repeat_num = exists(doc.pmtct, "azt") ? 1 : 0;
		} else {
			hiv_azt_repeat_denom = 0;
			hiv_azt_repeat_num = 0;
		}
		report_values.push(new reportValue(hiv_azt_repeat_num, hiv_azt_repeat_denom, "AZT on consecutive visits"));	
		
	    /*	
	    #-----------------------------------
	    #7a.Proportion of all pregnant women seen with RPR test given on the 1st visit
		
		## Count per Pregnancy ID ##
		
		*/
		
		rpr_first_visit_num = ((doc.visit_number == "1") && exists(doc.rpr, "r")) ? 1 : 0;
		report_values.push(new reportValue(rpr_first_visit_num, 1, "RPR given on 1st visit"));
		
		/*
		#-----------------------------------
	    #7b.Proportion of all women testing RPR-positive provided a dose of penicillin
		*/
		
		rpr_penicillin_num = (exists(doc.rpr, "r") && exists(doc.checklist, "penicilin")) ? 1 : 0;
		report_values.push(new reportValue(rpr_penicillin_num, 1, "RPR positive given penicillin"));
		
	    /*
	    #7c. Proportion of all women testing RPR-positive whose partners are given penicillin 
	    #(does not include first visit that women discovers she is RPR positive)
		*/
		
		/*TODO: create memory of if rpr was given last time*/
		rpr_last_visit = true;
		if (rpr_last_visit) {
			rpr_prtnr_penicillin_denom = 1;
			rpr_prtnr_penicillin_num = exists(doc.checklist, "partner_penicillin") ? 1 : 0;
		} else {
			rpr_prtnr_penicillin_denom = 0;
			rpr_prtnr_penicillin_num = 0;
		}
		report_values.push(new reportValue(rpr_prtnr_penicillin_num, rpr_prtnr_penicillin_denom, "RPR positive partner penicillin"));

		/*
	    #--------------------------------------------
	    #8. Fansidar:  Proportion of all pregnant women seen provided three doses of fansidar
		
		## Count per Pregnancy ID ##
		
		*/
		
		/*TODO: create running tally of fansidar during pregnancy to be kept with preg ID num and other 
		data spanning pregnancy.  count as good if:
			a) fansidar_count >= 3
			b) pregnancy closed, doc.resolution == "y"
			c) pregnancy has to be over: first_visit["edd"] >= today()+30
			
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
        
		emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth()], report_values); 
    } 
}
