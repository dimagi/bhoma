
function(doc) { 
    if (doc.doc_type == "CPatient") {
        emit([doc.address.clinic_id, doc.address.zone], null);
    }
}