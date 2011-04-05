function(doc) {
    if (doc.doc_type == "ClinicZone") {
        emit([doc.clinic_id, doc.zone], null);
    }
}