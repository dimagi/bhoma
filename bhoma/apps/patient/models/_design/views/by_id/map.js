
function(doc) { 
    if (doc.doc_type == "CPatient") 
        emit(doc.patient_id, doc); 
}