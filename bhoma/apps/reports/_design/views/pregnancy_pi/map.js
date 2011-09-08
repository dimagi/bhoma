function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
	// !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
	
	var HEALTHY_NAMESPACE = "http://cidrz.org/bhoma/pregnancy";
    var SICK_NAMESPACE = "http://cidrz.org/bhoma/sick_pregnancy";
    var DELIVERY_NAMESPACE = "http://cidrz.org/bhoma/delivery";
    var enc_date = get_encounter_date(doc);
    
    function _emit(name, num, denom) {
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id, name], [num, denom]);    
    }
    
        
    if (xform_matches(doc, HEALTHY_NAMESPACE))
    {   
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
    
        /* this field keeps track of total forms */
        _emit("total",1,1);
        
        
        /*
        #-----------------------------------
        #1. Pre-eclampsia screening
        #Proportion of routine visits with Blood Pressure and Urinalysis Protein results
        */
        
        var vitals_recorded_num = Boolean(doc.blood_pressure && (doc.urinalysis_protein == "p" || doc.urinalysis_protein == "n")) ? 1 : 0;
        _emit("preeclamp", vitals_recorded_num, 1);
        
        /*
        #----------------------------------
        #3. Clinical Exam: record Fundal Height, Presentation, and Fetal Heart Rate
        */
        
        var gest_age = doc.gestational_age;
        var clinic_exam_num = 0;
        var clinic_exam_denom = 0;
        if (parseInt(gest_age) > 28) {
        	clinic_exam_num = Boolean(doc.fundal_height && doc.fetal_heart_rate && doc.presentation != "blank") ? 1 : 0;
        	clinic_exam_denom = 1;
        } else if (parseInt(gest_age) > 16) {
        	clinic_exam_num = Boolean(doc.fundal_height && doc.fetal_heart_rate) ? 1 : 0;
        	clinic_exam_denom = 1;
        } 
        _emit("clin_exam", clinic_exam_num, clinic_exam_denom);
        
        /*
	    #----------------------------------
	    #4. HIV Testing: Proportion of all pregnant women seen with HIV test done on 1st visit
		*/
		var hiv_test_num = 0;
        var hiv_test_denom = 0;
		if (doc.visit_number == 1) {
			hiv_test_denom = 1;
			hiv_test_num = (doc.hiv_result == "r" || doc.hiv_result == "nr") ? 1 : 0;
		} 
		_emit("hiv_test", hiv_test_num, hiv_test_denom);
		
		      /*  
        #-----------------------------------
        #8.Proportion of all pregnant women seen with RPR test given on the 1st visit
           A proxy for this is to just check visit number = 1 and rpr given
        */
        
        var rpr_denom = 0;
        var rpr_num = 0;
        if (doc.visit_number == 1) {
            rpr_denom = 1;
            rpr_num = (doc.rpr == "r" || doc.rpr == "nr") ? 1 : 0;
        }
        _emit("rpr_1st_visit", rpr_num, rpr_denom);
    } 
    else if (xform_matches(doc, SICK_NAMESPACE)) {
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
    
        /*
        #--------------------------------------------
        #12.  Drugs dispensed appropriately (combined with Delivery form and Sick ANC)
        */
        
        /* this field keeps track of total forms */
        _emit("total",1,1);
        
        var drugs = doc.drugs.prescribed.med;
        var drug_stock_denom = 0;
        var drug_stock_num = 0;
		if (drugs) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(drugs);
	    } 
        
        _emit("drugs_stocked", drug_stock_num, drug_stock_denom);

    } 
    else if (xform_matches(doc, DELIVERY_NAMESPACE)) {
    	if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
    
        /* this field keeps track of total forms */
        _emit("total",1,1);
        
    	/*
        #--------------------------------------------
        #12.  Correct management of maternal HIV:
        # for hiv-positive women not already on Haart, antiretroviral given
        */
        
        var drugs_prescribed = doc.drugs_prescribed;
        var maternal_hiv_num = 0;
        var maternal_hiv_denom = 0;
        if (doc.history != null && doc.history.hiv_result == "r" && doc.history.on_haart != "y") {
        	if(drugs_prescribed) {
        		maternal_hiv_num = check_drug_type(drugs_prescribed,"antiretroviral");
    		} else {
    			maternal_hiv_num = 0;
    		}
        	maternal_hiv_denom = 1;
        } 
        _emit("maternal_hiv", maternal_hiv_num, maternal_hiv_denom);

    	/*
        #--------------------------------------------
        #13.  Infants given NVP as part of PMTCT at birth:
        # infant ARV NVP ticked if mother is Reactive
        */
        
        var infant_hiv_num = 0;
        var infant_hiv_denom = 0;
        if (doc.history.hiv_result == "r" && doc.continue_form == "y") {
        	infant_hiv_num = exists(doc.newborn_eval.infant_arvs,"nvp") ? 1 : 0;
        	infant_hiv_denom = 1;
        } 
        _emit("infant_nvp", infant_hiv_num, infant_hiv_denom);
        
        /*
        #--------------------------------------------
        #14. Correct management of intrapartum complications
        */
        // TODO: make this function smarter
        var complications = doc.complications;
        if (complications == null) {
            // no complications, no data
            _emit("del_mgmt", 0, 0);
        } else {
	        var severe_delivery_symptom = function(doc) {
		       return (exists(doc.complications.prolonged_labour, "sev_fhr") || 
		               exists(doc.complications.hypertension,"sev_sbp") ||
		               exists(doc.complications.hypertension,"sev_dbp") ||
					   exists(doc.complications.hypertension,"sev_urine") ||
		               exists(doc.complications.hypertension,"sev_hgb") ||
		               exists(doc.complications.hypertension, "sev_seizure") ||
		               exists(doc.complications.hypertension, "sev_altered") ||
		               exists(doc.complications.hypertension, "sev_headache") ||
		               exists(doc.complications.hypertension, "sev_visual_changes") ||
		               exists(doc.complications.hypertension, "sev_abd_pain") ||
		               exists(doc.complications.fever, "sev_sbp") ||
		               exists(doc.complications.fever, "sev_resp_rate") ||
		               exists(doc.complications.fever, "sev_mat_hr") ||
		               exists(doc.complications.fever, "sev_altered") ||
		               exists(doc.complications.vag_bleed, "sev_sbp") ||
		               exists(doc.complications.vag_bleed, "sev_resp_rate") ||
		               exists(doc.complications.vag_bleed, "sev_mat_hr") ||
		               exists(doc.complications.vag_bleed, "sev_hgb") ||
		               exists(doc.complications.vag_bleed, "sev_altered") ||
		               exists(doc.complications.mem_rupture, "sev_sbp") ||
		               exists(doc.complications.mem_rupture, "sev_resp_rate") ||
		               exists(doc.complications.mem_rupture, "sev_mat_hr") ||
		               exists(doc.complications.mem_rupture, "sev_temp") ||
		               exists(doc.complications.mem_rupture, "sev_34_weeks") ||
		               exists(doc.complications.mem_rupture, "sev_28_weeks") ||
		               exists(doc.complications.mem_rupture, "sev_abd_pain") ||
		               exists(doc.complications.mem_rupture, "sev_foul_discharge"));
		    }
	       
	        var comp_deliv_denom = 0;
	        var mgmt_good_so_far = 1;
	        var comp_deliv_num = 0;
	        if ((exists(doc.secondary_diagnosis, "uterine_infection") || doc.diagnosis == "uterine_infection") && drugs_prescribed) {
	        	comp_deliv_denom = 1;
	        	comp_deliv_num = check_drug_type(drugs_prescribed,"antibiotic") ? 1 : 0;
	        	mgmt_good_so_far = comp_deliv_num;
	        }
	        if (mgmt_good_so_far == 1 && complications.vag_bleed && !exists(complications.vag_bleed,"blank")) {
	        	comp_deliv_denom = 1;
	        	if (drugs_prescribed) {
	        		comp_deliv_num = (exists(doc.other_treatment,"oxygen") && (exists(doc.other_treatment,"fluids") || check_drug_name(drugs_prescribed,"sodium_chloride") || check_drug_name(drugs_prescribed,"ringers_lactate"))) ? 1 : 0;
	        	} else {
	        		comp_deliv_num = exists(doc.other_treatment,"blank") ? 0 : 1;
	        	}
	        	mgmt_good_so_far = comp_deliv_num;
	        }
	        if (mgmt_good_so_far == 1 && doc.phys_exam.fetal_heart_rate <= 110 && drugs_prescribed) {
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
	        _emit("del_mgmt", comp_deliv_num, comp_deliv_denom);
        }

        /*
        #--------------------------------------------
        #15.  Drugs dispensed appropriately (combined with Delivery form and Sick ANC)
        */
		var drug_stock_denom = 0;
        var drug_stock_num = 0;
		if (doc.drugs && doc.drugs.prescribed && doc.drugs.prescribed.med) {
	       drug_stock_denom = 1;
	       drug_stock_num = check_drug_stock(doc.drugs.prescribed.med);
	    } 
	   	_emit("drugs_stocked", drug_stock_num, drug_stock_denom);
        
    } else if (doc.doc_type == "PregnancyReportRecord") {

        // this is where the aggregated data across pregnancies goes.
        
        function _emit_with_custom_date(date, name, num, denom) {
            // we also use a different clinic id here
            emit([date.getFullYear(), date.getMonth(), doc.clinic_id, name], [num, denom]);    
        }
    
        var first_visit_date = parse_date(doc.first_visit_date);
        /* this field keeps track of total pregnancies */
        _emit_with_custom_date(first_visit_date, "total_pregs",1,1);
        
        /*
        #----------------------------------- 
	    #2.Proportion of those with potential Preeclampsia who are 
	    #prescribed with Antihypertensives and Referred. 
		*/
	    
	    // here and below, if we don't have a follow date we don't emit anything
	    // that's fine, it just won't count towards either indicator (good or bad)
	    for (var i in doc.dates_preeclamp_treated) {
            treated_date = parse_date(doc.dates_preeclamp_treated[i]);
            _emit_with_custom_date(treated_date, "preeclamp_mgd", 1, 1);
        }
        for (var i in doc.dates_preeclamp_not_treated) {
            treated_date = parse_date(doc.dates_preeclamp_not_treated[i]);
            _emit_with_custom_date(treated_date, "preeclamp_mgd", 0, 1);
        }
        		
		
		/*
	    #----------------------------------
	    #5. PMTCT for HIV positive women testing HIV-positive not already on Haart
	    # i. Provided a dose of NVP on the 1st visit they are +
	    */
		
		_emit_with_custom_date(first_visit_date, "nvp_1st_visit", doc.got_nvp_when_tested_positive ? 1:0, 
		      doc.not_on_haart_when_test_positive ? 1:0);

		/*
	    #----------------------------------
	    #6. PMTCT for HIV positive women testing HIV-positive not already on Haart
	    # Provided a dose of AZT on the 1st visit they are + > 14 weeks GA
	    */
		_emit_with_custom_date(first_visit_date, "azt_1st_visit", doc.got_azt_when_tested_positive ? 1:0,
	          doc.not_on_haart_when_test_positive_ga_14 ? 1:0);
	    
		/*	
	    #-----------------------------------
	    #7. AZT/Haart: 
	    # Proportion of all women provided AZT who received it at their last visit
	    */
        
		if (doc.had_two_healthy_visits_after_pos_test_ga_14 !== undefined) {
		    _emit_with_custom_date(first_visit_date, "azt_haart", 
		          (doc.got_azt_haart_on_consecutive_visits && doc.had_two_healthy_visits_after_pos_test_ga_14) ? 1:0,
                  doc.had_two_healthy_visits_after_pos_test_ga_14 ? 1:0);
		} else {
		    _emit_with_custom_date(first_visit_date, "azt_haart", 
		          (doc.got_azt_haart_on_consecutive_visits && doc.ever_tested_positive) ? 1:0,
                  doc.ever_tested_positive ? 1:0);
		}
		
              
		
		/*
		#-----------------------------------
	    #9.Proportion of all women testing RPR-positive provided a dose of penicillin
		*/
		
        _emit_with_custom_date(first_visit_date, "rpr_pen", doc.got_penicillin_when_rpr_positive ? 1:0, 
                               doc.tested_positive_rpr ? 1:0);
       
	    /*
	    #10. Proportion of all women testing RPR-positive whose partners are given penicillin 
	    #(does not include first visit that women discovers she is RPR positive)
		*/
		
        if (doc.tested_positive_rpr_and_had_later_visit !== undefined) {
            // post 0.2.4
            _emit_with_custom_date(first_visit_date, "rpr_partner", 
                    (doc.partner_got_penicillin_when_rpr_positive && doc.tested_positive_rpr_and_had_later_visit) ? 1:0, 
                     doc.tested_positive_rpr_and_had_later_visit ? 1:0);
        } else {
            // pre 0.2.4
            _emit_with_custom_date(first_visit_date, "rpr_partner", 
                                   doc.partner_got_penicillin_when_rpr_positive ? 1:0, 
                                   doc.tested_positive_rpr ? 1:0);
       
        }
        
        /*
	    #--------------------------------------------
	    #11. Fansidar:  Proportion of all pregnant women seen provided three doses of fansidar
		
		*/
		
		if (doc.eligible_three_doses_fansidar !== undefined) {
		    var denom = doc.eligible_three_doses_fansidar ? 1:0;
		    var num = denom && doc.got_three_doses_fansidar ? 1:0;
		    _emit_with_custom_date(first_visit_date, "fansidar", 
                                   num, denom);
		} else {
		    // not yet on the new indicator, emit the old indicator
		    _emit_with_custom_date(first_visit_date, "fansidar_old", doc.got_three_doses_fansidar ? 1:0, 1);
		}
	    
    } 
}