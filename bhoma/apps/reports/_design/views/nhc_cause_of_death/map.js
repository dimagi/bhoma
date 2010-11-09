function(doc) {
    /* 
     * Mortality Register Report
     */
    
    // these lines magically import our other javascript files.  DON'T REMOVE THEM!
    // !code util/xforms.js
    
    NAMESPACE = "http://cidrz.org/bhoma/mortality_register"
    
    if (xform_matches(doc, NAMESPACE))
    {   
        enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        child_reg = extract_repeats(doc.child_register);
        for (i in child_reg) { 
            reg = child_reg[i];
            emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id, "child", reg.gender, reg.death_type], 1);
	    }
        adult_reg = extract_repeats(doc.adult_register);
        for (i in adult_reg) { 
            reg = adult_reg[i];
            emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id, "adult", reg.gender, reg.death_type], 1);
        }

    } 
}