function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
	// !code util/dates.js
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
        
        vitals_recorded_num = Boolean(doc.blood_pressure && (doc.urinalysis_protein == "p" || doc.urinalysis_protein == "n")) ? 1 : 0;
        report_values.push(new reportValue(vitals_recorded_num, 1, "Preeclampsia Screening", false, "Blood Pressure recorded and results received for Urinalysis Protein test.")); 
        
        /*
        #----------------------------------
        #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
        */
        
        gest_age = doc.gestational_age;
        if (parseInt(gest_age) > 28) {
        	clinic_exam_num = Boolean(doc.fundal_height && doc.fetal_heart_rate && doc.presentation != "blank") ? 1 : 0;
        	clinic_exam_denom = 1;
        } else if (parseInt(gest_age) > 16) {
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
		if (doc.visit_number == 1) {
			hiv_test_denom = 1;
			hiv_test_num = (doc.hiv_result == "r" || doc.hiv_result == "nr") ? 1 : 0;
		} else {
        	hiv_test_num = 0;
        	hiv_test_denom = 0;
    	}
		report_values.push(new reportValue(hiv_test_num, hiv_test_denom, "HIV Test Done", false, "HIV test results recorded at first ANC visit."));
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 
    } 
    else if (xform_matches(doc, SICK_NAMESPACE)) {
        
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        
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
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], 
             [new reportValue(drug_stock_num, drug_stock_denom, "Drugs In Stock", false, "Protocol recommended prescriptions in stock at the clinic.")]);

    } 
    else if (xform_matches(doc, DELIVERY_NAMESPACE)) {
    	
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        report_values = [];
        /* this field keeps track of total forms */
        report_values.push(new reportValue(1,1,"total",true));

    	/*
        #--------------------------------------------
        #12.  Correct management of maternal HIV:
        # for hiv-positive women not already on Haart, antiretroviral given
        */
        
        drugs_prescribed = doc.drugs_prescribed;
        if (doc.history["hiv_result"] == "r" && doc.history["on_haart"] != "y") {
        	if(drugs_prescribed) {
        		maternal_hiv_num = check_drug_type(drugs_prescribed,"antiretroviral");
    		} else {
    			maternal_hiv_num = 0;
    		}
        	maternal_hiv_denom = 1;
        } else {
        	maternal_hiv_num = 0;
        	maternal_hiv_denom = 0;
        }
        report_values.push(new reportValue(maternal_hiv_num, maternal_hiv_denom, "Maternal HIV", false, "For HIV-positive women not already on HAART, an antiretroviral is prescribed on the Delivery form.")); 

    	/*
        #--------------------------------------------
        #13.  Infants given NVP as part of PMTCT at birth:
        # infant ARV NVP ticked if mother is Reactive
        */
        
        if (doc.history["hiv_result"] == "r" && doc.continue_form == "y") {
        	infant_hiv_num = exists(doc.newborn_eval["infant_arvs"],"nvp") ? 1 : 0;
        	infant_hiv_denom = 1;
        } else {
        	infant_hiv_num = 0;
        	infant_hiv_denom = 0;
        }
        report_values.push(new reportValue(infant_hiv_num, infant_hiv_denom, "Infant NVP", false, "Infants of HIV-positive mothers prescribed NVP after delivery.")); 
        
        /*
        #--------------------------------------------
        #14. Correct management of intrapartum complications
        */
        // TODO: make this function smarter
        complications = doc.complications;
        var severe_delivery_symptom = function(doc) {
	       return (exists(complications["prolonged_labour"], "sev_fhr") || 
	               exists(complications["hypertension"],"sev_sbp") ||
	               exists(complications["hypertension"],"sev_dbp") ||
				   exists(complications["hypertension"],"sev_urine") ||
	               exists(complications["hypertension"],"sev_hgb") ||
	               exists(complications["hypertension"], "sev_seizure") ||
	               exists(complications["hypertension"], "sev_altered") ||
	               exists(complications["hypertension"], "sev_headache") ||
	               exists(complications["hypertension"], "sev_visual_changes") ||
	               exists(complications["hypertension"], "sev_abd_pain") ||
	               exists(complications["fever"], "sev_sbp") ||
	               exists(complications["fever"], "sev_resp_rate") ||
	               exists(complications["fever"], "sev_mat_hr") ||
	               exists(complications["fever"], "sev_altered") ||
	               exists(complications["vag_bleed"], "sev_sbp") ||
	               exists(complications["vag_bleed"], "sev_resp_rate") ||
	               exists(complications["vag_bleed"], "sev_mat_hr") ||
	               exists(complications["vag_bleed"], "sev_hgb") ||
	               exists(complications["vag_bleed"], "sev_altered") ||
	               exists(complications["mem_rupture"], "sev_sbp") ||
	               exists(complications["mem_rupture"], "sev_resp_rate") ||
	               exists(complications["mem_rupture"], "sev_mat_hr") ||
	               exists(complications["mem_rupture"], "sev_temp") ||
	               exists(complications["mem_rupture"], "sev_34_weeks") ||
	               exists(complications["mem_rupture"], "sev_28_weeks") ||
	               exists(complications["mem_rupture"], "sev_abd_pain") ||
	               exists(complications["mem_rupture"], "sev_foul_discharge"));
	    }
       
        comp_deliv_denom = 0;
        mgmt_good_so_far = 1;
        if (mgmt_good_so_far == 1 && comp_deliv_denom == 0 && (exists(doc.secondary_diagnosis, "uterine_infection") || doc.diagnosis == "uterine_infection") && drugs_prescribed) {
        	comp_deliv_denom = 1;
        	comp_deliv_num = check_drug_type(drugs_prescribed,"antibiotic") ? 1 : 0;
        	mgmt_good_so_far = comp_deliv_num;
        }
        if (mgmt_good_so_far == 1 && complications["vag_bleed"] && !exists(complications["vag_bleed"],"blank")) {
        	comp_deliv_denom = 1;
        	if (drugs_prescribed) {
        		comp_deliv_num = (exists(doc.other_treatment,"oxygen") && (exists(doc.other_treatment,"fluids") || check_drug_name(drugs_prescribed,"sodium_chloride") || check_drug_name(drugs_prescribed,"ringers_lactate"))) ? 1 : 0;
        	} else {
        		comp_deliv_num = exists(doc.other_treatment,"blank") ? 0 : 1;
        	}
        	mgmt_good_so_far = comp_deliv_num;
        }
        if (mgmt_good_so_far == 1 && doc.phys_exam["fetal_heart_rate"] <= 110 && drugs_prescribed) {
        	comp_deliv_denom = 1;
        	if (drugs_prescribed){
        		comp_deliv_num = (exists(doc.other_treatment,"fluids") || check_drug_name(drugs_prescribed,"sodium_chloride")  || check_drug_name(drugs_prescribed,"ringers_lactate")) ? 1 : 0;
        	} else {
        		exists(doc.other_treatment,"fluids");
        	}
        	mgmt_good_so_far = comp_deliv_num;
        }
        if (mgmt_good_so_far == 1 && severe_delivery_symptom(doc)) {
        	comp_deliv_denom = 1;
        	comp_deliv_num = (doc.resolution == "referral" || doc.admitted == "y") ? 1 : 0;
        	mgmt_good_so_far = comp_deliv_num;
        }
        /*If made it this far, dont have delivery complications*/
        if (comp_deliv_denom == 0) {
        	comp_deliv_num = 0;
    	}
        report_values.push(new reportValue(comp_deliv_num, comp_deliv_denom, "Delivery Mgmt", false, "Severe symptoms referred or admitted, fluids given for fetal distress, severe vaginal bleeding given oxygen and fluids, and uterine infection given antibiotics.")); 

        /*
        #--------------------------------------------
        #15.  Drugs dispensed appropriately (combined with Delivery form and Sick ANC)
        */
		drugs = doc.drugs["prescribed"]["med"];
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } else {
	       drug_stock_denom = 0;
	       drug_stock_num = 0;
	    }
	   	report_values.push(new reportValue(drug_stock_num, drug_stock_denom, "Drugs In Stock", false, "Protocol recommended prescriptions in stock at the clinic.")); 
        
        
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id], report_values); 

         
    } else if (doc["doc_type"] == "PregnancyReportRecord") {

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
                 [new reportValue(1, 1, "Pre-eclampsia Managed",false,"Patients with high blood pressure, proteinuria, and symptoms of pre-eclampsia after GA of 20 weeks.")]);
        }
        for (var i in doc.dates_preeclamp_not_treated) {
            treated_date = parse_date(doc.dates_preeclamp_not_treated[i]);
            emit([treated_date.getFullYear(), treated_date.getMonth(), doc.clinic_id], 
                 [new reportValue(0, 1, "Pre-eclampsia Managed",false,"Patients with high blood pressure, proteinuria, and symptoms of pre-eclampsia after GA of 20 weeks.")]);
        }
        		
		
		/*
	    #----------------------------------
	    #5. PMTCT for HIV positive women testing HIV-positive not already on Haart
	    # i. Provided a dose of NVP on the 1st visit they are +
	    */
		
		report_values.push(new reportValue(doc.got_nvp_when_tested_positive ? 1:0,
		                                   doc.not_on_haart_when_test_positive ? 1:0, "NVP First Visit", false, "HIV-positive women not already on HAART dispensed NVP on first visit with a reactive test recorded."));

		/*
	    #----------------------------------
	    #6. PMTCT for HIV positive women testing HIV-positive not already on Haart
	    # Provided a dose of AZT on the 1st visit they are + > 14 weeks GA
	    */
		report_values.push(new reportValue(doc.got_azt_when_tested_positive ? 1:0,
		                                   doc.not_on_haart_when_test_positive_ga_14 ? 1:0, "AZT First Visit", false, "HIV-positive women not already on HAART dispensed AZT on first visit with a reactive test recorded after GA of 14 weeks."));
	    
		/*	
	    #-----------------------------------
	    #7. AZT/Haart: 
	    # Proportion of all women provided AZT who received it at their last visit
	    */
        
		report_values.push(new reportValue(doc.got_azt_haart_on_consecutive_visits ? 1:0,
		                                   doc.ever_tested_positive ? 1:0, "AZT/Haart", false, "HIV-positive women given either AZT or on HAART, recorded at both current and previous visits after GA of 14 weeks."));
		
	    /*	
	    #-----------------------------------
	    #8.Proportion of all pregnant women seen with RPR test given on the 1st visit
		
		*/
		
		report_values.push(new reportValue(doc.rpr_given_on_first_visit ? 1:0,
		                                   1, "RPR 1st visit", false, "RPR result recorded at first ANC visit."));
		
		/*
		#-----------------------------------
	    #9.Proportion of all women testing RPR-positive provided a dose of penicillin
		*/
		
		report_values.push(new reportValue(doc.got_penicillin_when_rpr_positive ? 1:0, 
		                                   doc.tested_positive_rpr ? 1:0, "RPR+ Penicillin",false,"Women testing RPR-positive given a dose of penicillin at the same visit."));
		
	    /*
	    #10. Proportion of all women testing RPR-positive whose partners are given penicillin 
	    #(does not include first visit that women discovers she is RPR positive)
		*/
		
		report_values.push(new reportValue(doc.partner_got_penicillin_when_rpr_positive ? 1:0,
		                                   doc.tested_positive_rpr ? 1:0, "RPR+ Partner",false,"Women testing RPR-positive whose partners are given penicillin at the visit after the womans test done."));

		/*
	    #--------------------------------------------
	    #11. Fansidar:  Proportion of all pregnant women seen provided three doses of fansidar
		
		*/
		
		report_values.push(new reportValue(doc.got_three_doses_fansidar ? 1:0,
                                           1, "Fansidar",false,"3 doses of Fansidar given during pregnancy."));

        
	    first_visit_date = parse_date(doc.first_visit_date);
	    emit([first_visit_date.getFullYear(), first_visit_date.getMonth(), doc.clinic_id], report_values); 
    } 
}