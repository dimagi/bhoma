function(doc) {
    /* 
     * Mortality Register Report (Cause and Place of Death)
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
            emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "child", reg.gender, "cause", reg.death_type], 1);
            emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "child", reg.gender, "place", reg.death_location], 1);
	    }
        adult_reg = extract_repeats(doc.adult_register);
        for (i in adult_reg) {
            reg = adult_reg[i];
            emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "adult", reg.gender, "cause", reg.death_type], 1);
            emit([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "adult", reg.gender, "place", reg.death_location], 1);
        }

    } 
}