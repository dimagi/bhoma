function(doc) { 
    if (doc.doc_type == "CPatient") {
        emit(doc.last_name, null);
        emit(doc.first_name, null);
    }
}