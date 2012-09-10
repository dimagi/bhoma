function(doc) {
    /* Pregnancy Performance Indicator Report
     */
    
    // !code util/dates.js
    // !code util/reports.js
    // !code util/xforms.js
    
    var ADULT_NAMESPACE = "http://cidrz.org/bhoma/general";
    var U5_NAMESPACE = "http://cidrz.org/bhoma/underfive";
    // var HEALTHY_NAMESPACE = "http://cidrz.org/bhoma/pregnancy";
    var SICK_ANC_NAMESPACE = "http://cidrz.org/bhoma/sick_pregnancy";
    var DELIVERY_NAMESPACE = "http://cidrz.org/bhoma/delivery";
    
    var enc_date = get_encounter_date(doc);
    if (enc_date == null)  {
        // weird, but don't worry about it
        return;
    }
    
    var _emit = function (name, count) {
        emit([enc_date.getFullYear(), enc_date.getMonth(), doc.meta.clinic_id, name], count);    
    };
    
    if (xform_matches(doc, U5_NAMESPACE)) {
        _emit("total",1);
        
        // values related to diagnoses
	        var paed_diagnoses = ["measles", "dysentry", "meningitis", 
	                              "anaemia", "rti_non_pneumonia", "rti_pneumonia"];
        for (var i = 0; i < paed_diagnoses.length; i++) {
            if (doc.primary_diagnosis_one   === paed_diagnoses[i] || 
                doc.primary_diagnosis_two   === paed_diagnoses[i] || 
                doc.secondary_diagnosis_one === paed_diagnoses[i] ||
                doc.secondary_diagnosis_two === paed_diagnoses[i]) 
            {
                _emit(paed_diagnoses[i], 1);
            }
        }
    } else if (xform_matches(doc, ADULT_NAMESPACE)) {
        _emit("total",1);
        // values related to diagnoses
        var adult_diagnoses = ["dysentry", "meningitis", "diabetes", 
                               "hypertension", "anaemia", "rti_non_pneumonia", 
                               "rti_pneumonia", "tb"];
        for (var i = 0; i < adult_diagnoses.length; i++) {
            if (doc.primary_diagnosis_one   === adult_diagnoses[i] || 
                doc.primary_diagnosis_two   === adult_diagnoses[i] || 
                doc.secondary_diagnosis_one === adult_diagnoses[i] ||
                doc.secondary_diagnosis_two === adult_diagnoses[i]) 
            {
                _emit(adult_diagnoses[i], 1);
            }
        }
    }
}