function(doc) {
    /* 
     * Mortality Register Report (Cause and Place of Death)
     */
    
    // !code util/dates.js
    // !code util/xforms.js
    
    NAMESPACE = "http://cidrz.org/bhoma/mortality_register"
    
    if (xform_matches(doc, NAMESPACE))
    {   
        var _emit_with_district = function(keys, value) {
            // emit twice for clinic and district, making some serious assumptions:    
            // 1. That the first key is the clinic code
            // 2. That the district is the first four digits of the clinic code.
            emit(keys, value);
            if (keys[0] && keys[0].length > 4) {
                var keyscopy = eval(uneval(keys));
                keyscopy[0] = keys[0].substring(0,4);
                // this is not even a joke, if you remove this comment the below won't work.
                emit(keyscopy, value);
            }
            
        }
        var enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        var to_int = function(val) {
            if (val == null || val == "") {
                return 0;
            }
            return parseInt(val);
        }
        _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "adult", "m", "global", "num_adult_men"], to_int(doc.num_adult_men));
        _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "adult", "f", "global", "num_adult_women"], to_int(doc.num_adult_women));
        _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "child", "", "global", "num_under_five"], to_int(doc.num_under_five));
        _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "child", "", "global", "num_five_up"], to_int(doc.num_five_up));
        _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "", "", "global", "num_households"], to_int(doc.num_households));
        var child_reg = extract_repeats(doc.child_register);
        for (var i in child_reg) { 
            var reg = child_reg[i];
            _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "child", reg.gender, "cause", reg.death_type], 1);
            _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "child", reg.gender, "place", reg.death_location], 1);
        }
        var adult_reg = extract_repeats(doc.adult_register);
        for (i in adult_reg) {
            var reg = adult_reg[i];
            _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "adult", reg.gender, "cause", reg.death_type], 1);
            _emit_with_district([doc.meta.clinic_id, enc_date.getFullYear(), enc_date.getMonth(), "adult", reg.gender, "place", reg.death_location], 1);
        }

    } 
}