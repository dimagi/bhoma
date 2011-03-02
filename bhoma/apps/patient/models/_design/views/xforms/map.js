function(doc) { 
    if (doc["#doc_type"] == "XForm") {
        if (doc.case && doc.case.patient_id) {
            emit(doc.case.patient_id, null);
        } else if (doc["#patient_guid"]) {
            // sometimes we need to use this property because forms like
            // the chw referral don't have case blocks or patient ids by
            // default - they get added in after.
            emit(doc["#patient_guid"], null);
        }
    } 
}