function(doc) { 
    if (doc["#doc_type"] == "XForm") {
        if (doc["#patient_id"]) {
            emit(doc["#patient_id"], null);
        }
    } 
}