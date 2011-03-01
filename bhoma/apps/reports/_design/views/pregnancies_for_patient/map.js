function(doc) { 
    if (doc["doc_type"] == "PregnancyReportRecord") {
        emit(doc.patient_id, null);
    } 
}