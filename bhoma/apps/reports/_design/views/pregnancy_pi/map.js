function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
	// these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/reports.js
    // !code util/xforms.js
	HEALTHY_NAMESPACE = "http://cidrz.org/bhoma/pregnancy";
    SICK_NAMESPACE = "http://cidrz.org/bhoma/sick_pregnancy";
    DELIVERY_NAMESPACE = "http://cidrz.org/bhoma/delivery";
    
    if (xform_matches(doc, HEALTHY_NAMESPACE))
    {   
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        
        report_values = [];
        /* this field keeps track of total forms */
        report_values.push(new reportValue(1,1,"total",true));
        
        new_case = doc.encounter_type == "new_case" ? 1 : 0;
        report_values.push(new reportValue(new_case, 1, "new_case", true));
        
        followup_case = doc.encounter_type == "new_case" ? 0 : 1;
        report_values.push(new reportValue(followup_case, 1, "followup_case", true));

        /*
        #-----------------------------------
        #1. Pre-eclampsia screening
        #Proportion of routine visits with Blood Pressure and Urinalysis Protein results
        */
        
        vitals_recorded_num = Boolean(doc.blood_pressure && (doc.urinalysis_protein == "p" || "n")) ? 1 : 0;
        report_values.push(new reportValue(vitals_recorded_num, 1, "Preeclampsia Screening", false, "Blood Pressure recorded and results received for Urinalysis Protein test.")); 
        
        /*
        #----------------------------------
        #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
        */
        
        gest_age = doc.gestational_age.parseInt;
        if (gest_age > 28) {
        	clinic_exam_num = Boolean(doc.fundal_height && doc.fetal_heart_rate && doc.presentation) ? 1 : 0;
        	clinic_exam_denom = 1;
        } else if (gest_age > 16) {
        	clinic_exam_num = Boolean(doc.fundal_height && doc.fetal_heart_rate) ? 1 : 0;
        	clinic_exam_denom = 1;
        } else {
        	clinic_exam_num = 0;
        	clinic_exam_denom = 0;
    	}
        report_values.push(new reportValue(clinic_exam_num, clinic_exam_denom, "Clinical Exam", false, "Fundal Height (GA > 16 weeks), Presentation (GA > 28 weeks), and Fetal Heart Rate (GA > 16 weeks) recorded."));
        
        /*
	    #----------------------------------
	    #4. HIV Testing: Proportion of all pregnant women seen with HIV test done on 1st visit
		*/
		if (doc.visit_number == "1") {
			hiv_test_denom = 1;
			hiv_test_num = doc.hiv_result == "r" || "nr";
		}
		report_values.push(new reportValue(hiv_test_num, hiv_test_denom, "HIV Test Done", false, "HIV Test Done during pregnancy."));
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 
    } 
    else if (xform_matches(doc, SICK_NAMESPACE)) {
        
        /*
        #--------------------------------------------
        #12.  Drugs dispensed appropriately (combined with Delivery form and Sick ANC)
        */
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        
        drugs = doc.drugs["prescribed"]["med"];
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } else {
	       drug_stock_denom = 0;
	       drug_stock_num = 0;
	    }
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], 
             [new reportValue(drug_stock_num, drug_stock_denom, "Drugs In Stock", false, "First line drugs in stock at the clinic.")]);

    } else if (xform_matches(doc, DELIVERY_NAMESPACE)) {
    
    	/*
        #--------------------------------------------
        #9.  Correct management of maternal HIV:
        # for hiv-positive women not already on Haart, antiretroviral given
        */
       
        if (doc.history["hiv_result"] == "r" && doc.history["on_haart"] != "y") {
        	maternal_hiv_num = check_drug_type(drugs_prescribed,"antiretroviral");
        	maternal_hiv_denom = 1;
        } else {
        	maternal_hiv_num = 0;
        	maternal_hiv_denom = 0;
        }
        report_values.push(new reportValue(maternal_hiv_num, maternal_hiv_denom, "Maternal HIV", false, "For HIV-positive women not already on HAART, an antiretroviral is prescribed on the Delivery form.")); 

    	/*
        #--------------------------------------------
        #10.  Infants given NVP as part of PMTCT at birth:
        # infant ARV NVP ticked if mother is Reactive
        */
        
        if (doc.history["hiv_result"] == "r" && doc.continue_form == "y") {
        	infant_hiv_num = doc.newborn_eval["infant_arvs"] == "nvp" ? 1 : 0;
        	infant_hiv_denom = 1;
        } else {
        	infant_hiv_num = 0;
        	infant_hiv_denom = 0;
        }
        report_values.push(new reportValue(infant_hiv_num, infant_hiv_denom, "Maternal HIV", false, "For HIV-positive women not already on HAART, an antiretroviral is prescribed on the Delivery form.")); 
        
        /*
        #--------------------------------------------
        #11. Correct management of intrapartum complications
        */
        
        comp_deliv_denom = 0;
        mgmt_good_so_far = 1;
        if (mgmt_good_so_far == 1 && comp_deliv_num == doc.secondary_diagnosis == "uterine_infection" || doc.diagnosis == "secondary_diagnosis") {
        	comp_deliv_denom = 1;
        	comp_deliv_num = check_drug_type(drugs_prescribed,"antibiotic");
        	mgmt_good_so_far = comp_deliv_num;
        }
        if (mgmt_good_so_far == 1 && doc.severe_vag_bleeding) {
        	comp_deliv_denom = 1;
        	comp_deliv_num = !exists(doc.other_treatment,"blank");
        	mgmt_good_so_far = comp_deliv_num;
        }
        if (mgmt_good_so_far == 1 && doc.fetal_heart_rate <= 110) {
        	comp_deliv_denom = 1;
        	comp_deliv_num = exists(doc.other_treatment,"fluids");
        	mgmt_good_so_far = comp_deliv_num;
        }
        if (mgmt_good_so_far == 1 && doc.severe_delivery_symptom) {
        	comp_deliv_denom = 1;
        	comp_deliv_num = doc.resolution == "referral";
        	mgmt_good_so_far = comp_deliv_num;
        }
        /*If made it this far, dont have delivery complications*/
        if (comp_deliv_denom == 0) {
        	comp_deliv_num = 0;
    	}
        report_values.push(new reportValue(comp_deliv_num, comp_deliv_denom, "Delivery Mgmt", false, "Correct management of select intrapartum complications.")); 

        /*
        #--------------------------------------------
        #12.  Drugs dispensed appropriately (combined with Delivery form and Sick ANC)
        */
		drugs = doc.drugs["prescribed"]["med"];
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } else {
	       drug_stock_denom = 0;
	       drug_stock_num = 0;
	    }
	   	report_values.push(new reportValue(drug_stock_num, drug_stock_denom, "Drugs In Stock", false, "First line drugs in stock at the clinic.")); 
        
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 

         
    } else if (doc["doc_type"] == "CPregnancy") {
        // this is where the aggregated data across pregnancies goes.
        report_values = [];
        /* this field keeps track of total pregnancies */
        first_visit_date = doc.first_visit_date
        
        report_values.push(new reportValue(1,1,"total",true));
        
        /*
        #----------------------------------- 
	    #2.Proportion of those with potential Preeclampsia who are 
	    #prescribed with Antihypertensives and Referred. 
		*/
	    
	    // here and below, if we don't have a follow date we don't emit anything
	    // that's fine, it just won't count towards either indicator (good or bad)
	    for (var i in doc.dates_preeclamp_treated) {
            treated_date = parse_date(doc.dates_preeclamp_treated[i]);
            emit([treated_date.getFullYear(), treated_date.getMonth(), doc.clinic_id], 
                 [new reportValue(1, 1, "Pre-eclampsia Managed",false,"Cases with Oedema or abnormal BP or protein in urine after 20 weeks GA who are prescribed with antihypertensives and referred.  Abnormal BP is SBP >= 140 or DBP >= 90.")]);
        }
        for (var i in doc.dates_preeclamp_not_treated) {
            treated_date = parse_date(doc.dates_preeclamp_not_treated[i]);
            emit([treated_date.getFullYear(), treated_date.getMonth(), doc.clinic_id], 
                 [new reportValue(0, 1, "Pre-eclampsia Managed",false,"Cases with Oedema or abnormal BP or protein in urine after 20 weeks GA who are prescribed with antihypertensives and referred.  Abnormal BP is SBP >= 140 or DBP >= 90.")]);
        }
        		
		
		/*
	    #----------------------------------
	    #5. PMTCT for HIV positive women testing HIV-positive not already on Haart
	    # i. Provided a dose of NVP on the 1st visit they are +
	    # ii. Provided a dose of AZT on the 1st visit they are +
	    */
		
		report_values.push(new reportValue(doc.got_nvp_azt_when_tested_positive ? 1:0, 
		                                   doc.not_on_haart_when_test_positive ? 1:0, "PMTCT First Visit", false, "Women testing HIV-positive not already on Haart provided with a does of NVP and AZT (GA > 14 weeks) on the first visit they test HIV-positive."));
	    
		/*	
	    #-----------------------------------
	    #6. AZT/Haart: 
	    # Proportion of all women provided AZT who received it at their last visit
	    */
        
		report_values.push(new reportValue(doc.got_azt_haart_on_consecutive_visits ? 1:0,
		                                   doc.ever_tested_positive ? 1:0, "AZT/Haart", false, "Women testing HIV-positive given a dose of AZT or on Haart at both their current and previous visits."));
		
	    /*	
	    #-----------------------------------
	    #7a.Proportion of all pregnant women seen with RPR test given on the 1st visit
		
		*/
		
		report_values.push(new reportValue(doc.rpr_given_on_first_visit ? 1:0,
		                                   1, "RPR 1st visit", false, "RPR test given on the first pregnancy visit."));
		
		/*
		#-----------------------------------
	    #7b.Proportion of all women testing RPR-positive provided a dose of penicillin
		*/
		
		report_values.push(new reportValue(doc.got_penicillin_when_rpr_positive ? 1:0, 
		                                   doc.tested_positive_rpr ? 1:0, "RPR+ Penicillin",false,"Women testing RPR-positive provided a dose of penicillin."));
		
	    /*
	    #7c. Proportion of all women testing RPR-positive whose partners are given penicillin 
	    #(does not include first visit that women discovers she is RPR positive)
		*/
		
		report_values.push(new reportValue(doc.partner_got_penicillin_when_rpr_positive ? 1:0,
		                                   doc.tested_positive_rpr ? 1:0, "RPR+ Partner",false,"Women testing RPR-positive whose partners are given penicillin (does not include the first visit discover RPR-positive)."));

		/*
	    #--------------------------------------------
	    #8. Fansidar:  Proportion of all pregnant women seen provided three doses of fansidar
		
		*/
		
		report_values.push(new reportValue(doc.got_three_doses_fansidar ? 1:0,
                                           1, "Fansidar",false,"3 doses of Fansidar given during pregnancy."));

        
	    first_visit_date = parse_date(doc.first_visit_date);
	    emit([first_visit_date.getFullYear(), first_visit_date.getMonth(), doc.clinic_id], report_values); 
    } 
}
