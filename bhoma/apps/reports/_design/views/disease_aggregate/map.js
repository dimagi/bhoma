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
    
    var _key_from_form_value = function (val) {
        // convert these to the same indicator
        if (val === "acute_diarrhea" || val === "persistent_diarrhea") {
            return "diarrhea";
        }
        return val;
    };
    
    var _emit = function (name, count) {
        emit([enc_date.getFullYear(), 
              enc_date.getMonth(), 
              doc.meta.clinic_id, 
              _key_from_form_value(name)], count);    
    };
    
    var _emit_diagnoses = function (doc, values) {
        for (var i = 0; i < values.length; i++) {
            if (doc.primary_diagnosis_one   === values[i] || 
                doc.primary_diagnosis_two   === values[i] || 
                exists(doc.secondary_diagnosis_one, values[i]) ||
                exists(doc.secondary_diagnosis_two, values[i])) 
            {
                _emit(values[i], 1);
            }
        }
        
    };
    
    var _emit_malaria = function (doc) {
        if (doc.investigations && doc.investigations.rdt_mps === "p") {
            _emit("malaria", 1);
        }
    };
    
    var _emit_hypertension = function (doc) {
        if (doc.assessment && exists(doc.assessment.categores, "hypertension")) {
            _emit("hypertension", 1);
        }
    };
    
    var _emit_given_antimalarials = function (doc) {
        if (check_drug_type(doc.drugs_prescribed, "antimalarial")) {
            _emit("given_antimalarials", 1);
        }
    };
    
    var enc_date = get_encounter_date(doc);
    if (enc_date == null)  {
        // weird, but don't worry about it
        return;
    }
    
    if (xform_matches(doc, U5_NAMESPACE)) {
        _emit("total",1);
        
        // values related to diagnoses
        var paed_diagnoses = ["measles", "dysentry", "meningitis", 
	                          "anaemia", "rti_non_pneumonia", "rti_pneumonia",
	                          "acute_diarrhea", "persistent_diarrhea"];
        _emit_diagnoses(doc, paed_diagnoses);
        _emit_malaria(doc);
        _emit_given_antimalarials(doc); 
        
    } else if (xform_matches(doc, ADULT_NAMESPACE)) {
        _emit("total", 1);
        // values related to diagnoses
        var adult_diagnoses = ["dysentry", "meningitis", "diabetes", 
                               "hypertension", "anaemia", "rti_non_pneumonia", 
                               "rti_pneumonia", "tb", "acute_diarrhea", 
                               "persistent_diarrhea"];
        _emit_diagnoses(doc, adult_diagnoses);
        _emit_malaria(doc);
        _emit_given_antimalarials(doc); 
        
    } else if (xform_matches(doc, SICK_ANC_NAMESPACE)) {
        _emit("total", 1);
        
        var sick_anc_diagnoses = ["meningitis", "pneumonia"];
        _emit_diagnoses(doc, sick_anc_diagnoses);
        _emit_malaria(doc);
        if (doc.investigations && doc.investigations.rdt_mps === "p") {
            _emit("pregnancy_malaria", 1);
        }
        _emit_hypertension(doc);
        _emit_given_antimalarials(doc); 
    
    } else if (xform_matches(doc, DELIVERY_NAMESPACE)) {
        _emit("total", 1);
        _emit_hypertension(doc);
        _emit_given_antimalarials(doc); 
    
    }
    
}