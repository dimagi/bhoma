function(doc) {
    if (doc.doc_type == "ClinicZone") {
        emit([doc.clinic_code, doc.zone], null);
    }
}