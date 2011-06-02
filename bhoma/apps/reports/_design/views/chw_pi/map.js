function(doc) {
    /* 
     * CHW Performance Indicator Report (this is only a very parial listing)
     * the majority of this report is build in python and through other couch views
     */
    
    // !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
    
    var HH_NAMESPACE = "http://cidrz.org/bhoma/household_survey";
    
    
    if (xform_matches(doc, HH_NAMESPACE))
    {   
        var enc_date = get_encounter_date(doc);
        if (enc_date == null)  {
            log("encounter date not found in doc " + doc._id + ". Will not be counted in reports");
            return;
        }
        
        function _emit(name, num, denom) {
            emit([doc.meta.user_id, enc_date.getFullYear(), enc_date.getMonth(), name], [num, denom]);    
        }
    
        //_emit("hh_surveys", 1, 1);
        var any_sick = extract_repeats(doc.any_sick);
        for (var i in any_sick) {
            var sick_person = any_sick[i];
            var has_danger_sign = sick_person.danger_signs && sick_person.danger_signs != "none";
            if (has_danger_sign) {
                var referred = (sick_person.refer_to_clinic == "y") ? 1 : 0;
                _emit("danger_referred", referred, 1);
            }
        }
        
    } 
}